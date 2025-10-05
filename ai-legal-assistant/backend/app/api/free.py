"""
Public/anonymous Q&A endpoints for landing chat.
Uploads go under supabase path prefix 'free-user/'.
Documents and sessions are deleted when the session is closed.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import Optional
import hashlib
from datetime import datetime
import asyncio
import logging

from app.core.database import get_db, SessionLocal
from app.core.config import settings
from app.services.supabase_service import supabase_service
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.models.analysis import QASession, QAQuestion
from app.core.llm import llm_service
from app.core.supabase_embeddings import embedding_service
from app.api.upload import process_document_supabase_async
from fastapi import Depends

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/free", tags=["Free Chat"])


def _get_or_create_free_user(db: Session) -> User:
    email = "free@system.local"
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(email=email, username="free_user", hashed_password="!", is_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/upload")
async def free_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()

        # owner is system free user
        owner = _get_or_create_free_user(db)

        # unique name and free-user prefix path
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_name = f"free_{owner.id}_{ts}_{file.filename}"
        supa_path = f"free-user/{owner.id}/{unique_name}"

        # upload
        uploaded = await supabase_service.upload_file(
            file_path=supa_path,
            file_content=content,
            content_type=file.content_type or "application/octet-stream",
        )
        if not uploaded:
            raise HTTPException(status_code=500, detail="Failed to upload to storage")

        file_url = await supabase_service.get_file_url(supa_path)

        # If a document with the same hash exists for the free user, reuse it
        existing = db.query(Document).filter(Document.file_hash == file_hash, Document.owner_id == owner.id).first()
        if existing:
            logger.info("Reusing existing free-user document for identical content")
            return {"id": existing.id}

        doc = Document(
            filename=unique_name,
            original_filename=file.filename,
            file_path=supa_path,
            file_url=file_url,
            file_hash=file_hash,
            file_size=len(content),
            mime_type=file.content_type or "application/octet-stream",
            document_type="free",
            title=file.filename,
            owner_id=owner.id,
            supabase_path=supa_path,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # process asynchronously
        asyncio.create_task(process_document_supabase_async(doc.id))
        return {"id": doc.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"free_upload error: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


@router.post("/sessions")
async def free_create_session(payload: dict, db: Session = Depends(get_db)):
    try:
        document_id = int(payload.get("document_id"))
        # Ensure document exists and is owned by free user
        owner = _get_or_create_free_user(db)
        doc = db.query(Document).filter(Document.id == document_id, Document.owner_id == owner.id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        if not doc.is_processed:
            raise HTTPException(status_code=400, detail="Document is still being processed")
        s = QASession(user_id=owner.id, document_id=doc.id, session_name=f"Free Q&A - {doc.title}")
        db.add(s)
        db.commit()
        db.refresh(s)
        return {"id": s.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"free_create_session error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.post("/ask")
async def free_ask(payload: dict, db: Session = Depends(get_db)):
    try:
        session_id = int(payload.get("session_id"))
        question = str(payload.get("question") or "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question required")
        owner = _get_or_create_free_user(db)
        session = db.query(QASession).filter(QASession.id == session_id, QASession.user_id == owner.id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        document = db.query(Document).filter(Document.id == session.document_id, Document.owner_id == owner.id).first()
        if not document or not document.is_processed:
            raise HTTPException(status_code=400, detail="Document not ready")

        q = QAQuestion(session_id=session.id, question=question)
        db.add(q)
        db.commit()
        db.refresh(q)

        context = await find_relevant_context(question, document.id, db)
        result = await llm_service.answer_question(question, context)

        q.answer = result["answer"]
        q.confidence_score = result["confidence"]
        q.context_used = context
        q.processing_time = 0
        q.model_used = result["model_used"]
        q.answered_at = datetime.utcnow()
        session.total_questions += 1
        session.last_activity = datetime.utcnow()
        db.commit()

        return {"answer": q.answer}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"free_ask error: {e}")
        raise HTTPException(status_code=500, detail="Failed to answer")


@router.post("/analyze-risks")
async def free_analyze_risks(payload: dict, db: Session = Depends(get_db)):
    """Analyze risks in a legal document"""
    try:
        session_id = int(payload.get("session_id"))
        owner = _get_or_create_free_user(db)
        session = db.query(QASession).filter(QASession.id == session_id, QASession.user_id == owner.id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        document = db.query(Document).filter(Document.id == session.document_id, Document.owner_id == owner.id).first()
        if not document or not document.is_processed:
            raise HTTPException(status_code=400, detail="Document not ready")

        # Get document content for risk analysis
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).order_by(DocumentChunk.chunk_index.asc()).all()
        document_text = "\n\n".join([ch.content for ch in chunks if ch.content])
        
        # Limit text length for analysis
        max_chars = 8000
        if len(document_text) > max_chars:
            document_text = document_text[:max_chars] + "..."
        
        # Perform risk analysis
        risk_analysis = await llm_service.detect_risks(document_text, "legal")
        
        return {
            "risk_analysis": risk_analysis["analysis"],
            "risk_level": risk_analysis["risk_level"],
            "risk_factors": risk_analysis["risk_factors"],
            "recommendations": risk_analysis["recommendations"],
            "confidence": risk_analysis["confidence"],
            "analysis_date": risk_analysis["analysis_date"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"free_analyze_risks error: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze risks")


@router.delete("/sessions/{session_id}")
async def free_end_session(session_id: int, db: Session = Depends(get_db)):
    """Delete the session, related questions, and the underlying document + storage."""
    try:
        owner = _get_or_create_free_user(db)
        session = db.query(QASession).filter(QASession.id == session_id, QASession.user_id == owner.id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # delete QA questions
        db.query(QAQuestion).filter(QAQuestion.session_id == session.id).delete()
        db.delete(session)

        # delete document + chunks + storage file
        doc = db.query(Document).filter(Document.id == session.document_id, Document.owner_id == owner.id).first()
        if doc:
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
            try:
                await supabase_service.delete_file(doc.supabase_path)
            except Exception:
                pass
            db.delete(doc)

        db.commit()
        return {"message": "Session and document deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"free_end_session error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to end session")


# reuse from qa module
async def find_relevant_context(question: str, document_id: int, db: Session) -> str:
    try:
        question_embedding = embedding_service.generate_embedding(question)
        # Increased base_k for better retrieval
        base_k = 15
        chunk_ids, scores = embedding_service.search_similar(question_embedding, k=base_k, document_id=document_id, question_text=question)
        candidate_indices = set()
        for chunk_id in chunk_ids:
            if chunk_id.startswith(f"doc_{document_id}_chunk_"):
                idx = int(chunk_id.split("_")[-1])
                # Include more surrounding chunks for better context
                candidate_indices.update([idx - 2, idx - 1, idx, idx + 1, idx + 2])
        if candidate_indices:
            ordered_chunks = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == document_id, DocumentChunk.chunk_index.in_(sorted([i for i in candidate_indices if i >= 0])))
                .order_by(DocumentChunk.chunk_index.asc())
                .all()
            )
        else:
            ordered_chunks = []
        context_parts = []
        total_len = 0
        # Increased context length for better answers
        max_context_length = 5000
        for ch in ordered_chunks:
            if not ch.content:
                continue
            if total_len >= max_context_length:
                break
            context_parts.append(f"[Chunk {ch.chunk_index}]: {ch.content}")
            total_len += len(ch.content)
        context = "\n\n".join(context_parts)
        return context
    except Exception:
        return ""


