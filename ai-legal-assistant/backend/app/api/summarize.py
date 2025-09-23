"""
Document summarization API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.llm import llm_service
from app.models.user import User
from app.models.document import Document, DocumentAnalysis
from app.schemas.analysis import SummaryRequest, SummaryResponse
from app.schemas.document import DocumentAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=SummaryResponse)
async def summarize_document(
    request: SummaryRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate summary for a document"""
    try:
        # Get document
        document = db.query(Document).filter(
            Document.id == request.document_id,
            Document.owner_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        if not document.is_processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document is still being processed"
            )
        
        if not document.extracted_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text content available for summarization"
            )
        
        # Check if summary already exists
        existing_summary = db.query(DocumentAnalysis).filter(
            DocumentAnalysis.document_id == request.document_id,
            DocumentAnalysis.analysis_type == "summary"
        ).first()
        
        if existing_summary and not request.force_regenerate:
            return SummaryResponse(
                document_id=document.id,
                summary=existing_summary.summary,
                structured_summary=existing_summary.structured_data or {},
                word_count=document.word_count,
                analysis_date=existing_summary.created_at,
                confidence_score=existing_summary.confidence_score,
                processing_time=existing_summary.processing_time
            )
        
        # Generate summary using LLM
        start_time = datetime.utcnow()
        
        summary_result = await llm_service.summarize_document(
            document.extracted_text,
            document.document_type or "contract"
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Save or update summary analysis
        if existing_summary:
            existing_summary.summary = summary_result["summary"]
            existing_summary.structured_data = summary_result["structured"]
            existing_summary.confidence_score = 0.8  # Default confidence
            existing_summary.processing_time = processing_time
            existing_summary.model_used = "gpt-3.5-turbo"
        else:
            summary_analysis = DocumentAnalysis(
                document_id=document.id,
                analysis_type="summary",
                summary=summary_result["summary"],
                structured_data=summary_result["structured"],
                confidence_score=0.8,
                model_used="gpt-3.5-turbo",
                processing_time=processing_time
            )
            db.add(summary_analysis)
        
        db.commit()
        
        logger.info(f"Summary generated for document {document.id}")
        
        return SummaryResponse(
            document_id=document.id,
            summary=summary_result["summary"],
            structured_summary=summary_result["structured"],
            word_count=document.word_count,
            analysis_date=datetime.utcnow(),
            confidence_score=0.8,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating document summary"
        )


@router.get("/{document_id}", response_model=SummaryResponse)
async def get_document_summary(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get existing summary for a document"""
    try:
        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get summary analysis
        summary_analysis = db.query(DocumentAnalysis).filter(
            DocumentAnalysis.document_id == document_id,
            DocumentAnalysis.analysis_type == "summary"
        ).first()
        
        if not summary_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No summary found for this document"
            )
        
        return SummaryResponse(
            document_id=document.id,
            summary=summary_analysis.summary,
            structured_summary=summary_analysis.structured_data or {},
            word_count=document.word_count,
            analysis_date=summary_analysis.created_at,
            confidence_score=summary_analysis.confidence_score,
            processing_time=summary_analysis.processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving document summary"
        )


@router.get("/", response_model=List[DocumentAnalysisResponse])
async def get_all_summaries(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all summaries for user's documents"""
    try:
        # Get all summary analyses for user's documents
        summaries = db.query(DocumentAnalysis).join(Document).filter(
            Document.owner_id == current_user.id,
            DocumentAnalysis.analysis_type == "summary"
        ).all()
        
        return summaries
        
    except Exception as e:
        logger.error(f"Error getting summaries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving summaries"
        )


@router.delete("/{document_id}")
async def delete_document_summary(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete summary for a document"""
    try:
        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get and delete summary analysis
        summary_analysis = db.query(DocumentAnalysis).filter(
            DocumentAnalysis.document_id == document_id,
            DocumentAnalysis.analysis_type == "summary"
        ).first()
        
        if summary_analysis:
            db.delete(summary_analysis)
            db.commit()
            logger.info(f"Summary deleted for document {document_id}")
        
        return {"message": "Summary deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting summary: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting document summary"
        )
