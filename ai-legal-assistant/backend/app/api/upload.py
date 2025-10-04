"""
Document upload and processing API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
import os
import aiofiles
import hashlib
from datetime import datetime
import asyncio

from app.core.database import get_db, SessionLocal
from app.core.config import settings
from app.core.auth import get_current_active_user
from app.core.utils import (
    validate_file_extension, 
    calculate_file_hash, 
    clean_text,
    extract_metadata_from_text,
    chunk_text
)
from app.services.document_processor import DocumentProcessor
from app.services.supabase_service import supabase_service
from app.core.supabase_embeddings import embedding_service
from app.models.user import User
from app.models.document import Document, DocumentChunk, DocumentAnalysis
from app.schemas.document import DocumentResponse, DocumentUpload, DocumentListResponse
# Heavy imports removed - will be loaded only when needed

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/supabase", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_supabase(
    request_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload document metadata from Supabase upload"""
    try:
        # Extract data from request
        filename = request_data.get('filename')
        original_filename = request_data.get('original_filename')
        file_path = request_data.get('file_path')
        file_url = request_data.get('file_url')
        file_size = request_data.get('file_size', 0)
        mime_type = request_data.get('mime_type', 'application/octet-stream')
        title = request_data.get('title', original_filename)
        document_type = request_data.get('document_type', 'contract')
        description = request_data.get('description', '')
        supabase_path = request_data.get('supabase_path')
        
        if not all([filename, original_filename, file_path, file_size]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: filename, original_filename, file_path, file_size"
            )
        
        # Validate file extension
        if not validate_file_extension(original_filename, settings.ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        if file_size > settings.UPLOAD_MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.UPLOAD_MAX_SIZE} bytes"
            )
        
        # Calculate file hash using the file path as a unique identifier
        file_hash = hashlib.sha256(file_path.encode()).hexdigest()
        
        # Check if document already exists
        existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()
        if existing_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document with this content already exists"
            )
        
        # Create document record
        document = Document(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_url=file_url,  # Store Supabase URL
            file_hash=file_hash,
            file_size=file_size,
            mime_type=mime_type,
            document_type=document_type,
            title=title,
            owner_id=current_user.id,
            supabase_path=supabase_path  # Store Supabase path for future operations
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document asynchronously
        asyncio.create_task(process_document_supabase_async(document.id))
        
        logger.info(f"Document uploaded via Supabase: {original_filename} by user {current_user.email}")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document via Supabase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading document"
        )


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and process a document to Supabase Storage"""
    try:
        # Validate file
        if not validate_file_extension(file.filename, settings.ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        if file.size > settings.UPLOAD_MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.UPLOAD_MAX_SIZE} bytes"
            )
        
        # Read file content
        content = await file.read()
        
        # Calculate file hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Check if document already exists
        existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()
        if existing_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document with this content already exists"
            )
        
        # Generate unique filename for Supabase
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{current_user.id}_{timestamp}_{file.filename}"
        supabase_path = f"documents/{current_user.id}/{unique_filename}"
        
        # Upload to Supabase Storage
        upload_result = await supabase_service.upload_file(
            file_path=supabase_path,
            file_content=content,
            content_type=file.content_type or "application/octet-stream"
        )
        
        if not upload_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to Supabase Storage"
            )
        
        # Get public URL
        file_url = await supabase_service.get_file_url(supabase_path)
        
        # Create document record
        document = Document(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=supabase_path,  # Store Supabase path
            file_url=file_url,  # Store public URL
            file_hash=file_hash,
            file_size=file.size,
            mime_type=file.content_type or "application/octet-stream",
            document_type=document_type,
            title=title or file.filename,
            owner_id=current_user.id,
            supabase_path=supabase_path
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document asynchronously
        asyncio.create_task(process_document_supabase_async(document.id))
        
        logger.info(f"Document uploaded to Supabase: {file.filename} by user {current_user.email}")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document to Supabase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading document"
        )


async def process_document_async(document_id: int, db: Session):
    """Process document asynchronously"""
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return
        
        # Update processing status
        document.processing_status = "processing"
        db.commit()
        
        # Initialize document processor
        processor = DocumentProcessor()
        
        # Extract text
        extracted_text = await processor.extract_text(document.file_path, document.mime_type)
        if not extracted_text:
            raise Exception("Failed to extract text from document")
        
        # Clean and process text
        cleaned_text = clean_text(extracted_text)
        
        # Extract metadata
        metadata = extract_metadata_from_text(cleaned_text)
        
        # Update document with extracted content
        document.extracted_text = cleaned_text
        document.text_hash = calculate_file_hash(cleaned_text.encode())
        document.word_count = metadata["word_count"]
        document.character_count = metadata["character_count"]
        document.parties = metadata.get("parties", [])
        document.title = document.title or metadata.get("potential_title", document.original_filename)
        
        # Chunk text for vector search
        chunks = chunk_text(cleaned_text, chunk_size=1000, overlap=200)
        
        # Create document chunks
        chunk_objects = []
        for i, chunk_content in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                content=chunk_content,
                word_count=len(chunk_content.split()),
                character_count=len(chunk_content)
            )
            chunk_objects.append(chunk)
            db.add(chunk)
        
        db.commit()
        
        # Generate and store embeddings for chunks
        if chunk_objects:
            texts = [c.content for c in chunk_objects]
            vectors = embedding_service.generate_embeddings_batch(texts)
            ids = [f"{document.id}_{c.chunk_index}" for c in chunk_objects]
            metadata = [
                {
                    'document_id': document.id,
                    'chunk_index': c.chunk_index,
                    'content': c.content[:500]
                } for c in chunk_objects
            ]
            embedding_service.add_vectors(vectors, ids, metadata)
        
        # Heavy processing moved to background script
        logger.info(f"Document {document.id} ready for viewing. Background processing will continue separately.")
        
        # Mark as processed
        document.is_processed = True
        document.processing_status = "completed"
        db.commit()
        
        logger.info(f"Document processed successfully: {document.filename}")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        # Update document with error status
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.processing_status = "failed"
            document.processing_error = str(e)
            db.commit()


async def process_document_supabase_async(document_id: int):
    """Process document from Supabase storage asynchronously"""
    # Create new database session for async processing
    db = SessionLocal()
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return
        
        # Update processing status
        document.processing_status = "processing"
        db.commit()
        
        # Download file from Supabase
        from app.services.supabase_service import supabase_service
        
        if not supabase_service.client:
            raise Exception("Supabase client not initialized")
        
        # Download file content from Supabase
        file_content = await supabase_service.download_file(document.supabase_path)
        if not file_content:
            raise Exception("Failed to download file from Supabase")
        
        # Save file temporarily for processing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{document.original_filename.split('.')[-1]}") as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Use the same processing pipeline as local files
            processor = DocumentProcessor()
            extracted_text = await processor.extract_text(temp_file_path, document.mime_type)
            if not extracted_text:
                raise Exception("Failed to extract text from document")
            
            cleaned_text = clean_text(extracted_text)
            metadata_info = extract_metadata_from_text(cleaned_text)
            
            document.extracted_text = cleaned_text
            document.text_hash = calculate_file_hash(cleaned_text.encode())
            document.word_count = metadata_info["word_count"]
            document.character_count = metadata_info["character_count"]
            document.title = document.title or metadata_info.get("potential_title", document.original_filename)
            
            chunks = chunk_text(cleaned_text, chunk_size=1000, overlap=200)
            chunk_objects = []
            for i, chunk_content in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk_content,
                    word_count=len(chunk_content.split()),
                    character_count=len(chunk_content)
                )
                chunk_objects.append(chunk)
                db.add(chunk)
            db.commit()
            
            if chunk_objects:
                texts = [c.content for c in chunk_objects]
                vectors = embedding_service.generate_embeddings_batch(texts)
                ids = [f"{document.id}_{c.chunk_index}" for c in chunk_objects]
                meta = [
                    {
                        'document_id': document.id,
                        'chunk_index': c.chunk_index,
                        'content': c.content[:500]
                    } for c in chunk_objects
                ]
                embedding_service.add_vectors(vectors, ids, meta)
            
            document.is_processed = True
            document.processing_status = "completed"
            document.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(document)
            logger.info(f"Document processed successfully from Supabase: {document.filename}")
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error processing Supabase document {document_id}: {e}")
        # Update document with error status
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.processing_status = "failed"
            document.processing_error = str(e)
            db.commit()
    finally:
        db.close()


# Background processing moved to separate script


@router.get("/", response_model=DocumentListResponse)
async def get_user_documents(
    page: int = 1,
    size: int = 10,
    document_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's documents with pagination"""
    try:
        query = db.query(Document).filter(Document.owner_id == current_user.id)
        
        if document_type:
            query = query.filter(Document.document_type == document_type)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        documents = query.offset((page - 1) * size).limit(size).all()
        
        # Calculate total pages
        pages = (total + size - 1) // size
        
        return DocumentListResponse(
            documents=documents,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting user documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving documents"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific document by ID"""
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving document"
        )


@router.get("/{document_id}/view")
async def view_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Serve document for viewing with proper headers"""
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Redirect to Supabase URL with proper headers for viewing
        if document.file_url:
            return RedirectResponse(url=document.file_url)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not available"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error viewing document"
        )


@router.get("/{document_id}/stream")
async def stream_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Stream document bytes with inline content-disposition for in-page preview"""
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        if not document.file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file path missing"
            )

        file_bytes = await supabase_service.download_file(document.file_path)
        if file_bytes is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found in storage"
            )

        headers = {
            "Content-Disposition": f"inline; filename=\"{document.original_filename}\""
        }
        return StreamingResponse(
            iter([file_bytes]),
            media_type=document.mime_type or "application/pdf",
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error streaming document"
        )

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Cascade-delete dependent records before document deletion (avoid FK violations)
        doc_id = document.id

        # Delete Q&A questions first, then sessions (FK constraint: questions reference sessions)
        from app.models.analysis import QASession, QAQuestion
        
        # Get session IDs for this document
        session_ids = db.query(QASession.id).filter(QASession.document_id == doc_id).all()
        session_ids_list = [s.id for s in session_ids]
        
        if session_ids_list:
            # Delete Q&A questions for these sessions
            db.query(QAQuestion).filter(QAQuestion.session_id.in_(session_ids_list)).delete()
            
            # Now delete Q&A sessions
            db.query(QASession).filter(QASession.document_id == doc_id).delete()

        # Delete document chunks
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()

        # Delete embeddings from vector store
        try:
            embedding_service.delete_chunks(document_id=doc_id)
        except Exception:
            pass

        # Remove file from Supabase Storage
        if document.supabase_path:
            await supabase_service.delete_file(document.supabase_path)

        db.delete(document)
        db.commit()
        
        logger.info(f"Document deleted: {document.filename}")
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting document"
        )
