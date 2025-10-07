"""
Q&A API endpoints for document interaction
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.llm import llm_service
from app.core.supabase_embeddings import embedding_service
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.models.analysis import QASession, QAQuestion
from app.schemas.analysis import (
    QAQuestionCreate, 
    QAQuestionResponse, 
    QASessionCreate, 
    QASessionResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sessions", response_model=QASessionResponse)
async def create_qa_session(
    request: QASessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new Q&A session for a document"""
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
        
        # Create Q&A session
        session = QASession(
            user_id=current_user.id,
            document_id=request.document_id,
            session_name=request.session_name or f"Q&A Session - {document.title}"
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Q&A session created: {session.id} for document {document.id}")
        
        return QASessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Q&A session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating Q&A session"
        )


@router.get("/sessions", response_model=List[QASessionResponse])
async def get_user_qa_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all Q&A sessions for the current user"""
    try:
        sessions = db.query(QASession).filter(
            QASession.user_id == current_user.id
        ).order_by(QASession.created_at.desc()).all()
        
        return [QASessionResponse.from_orm(session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Error getting Q&A sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving Q&A sessions"
        )


@router.get("/sessions/{session_id}", response_model=QASessionResponse)
async def get_qa_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific Q&A session"""
    try:
        session = db.query(QASession).filter(
            QASession.id == session_id,
            QASession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Q&A session not found"
            )
        
        return QASessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Q&A session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving Q&A session"
        )


@router.post("/ask", response_model=QAQuestionResponse)
async def ask_question(
    request: QAQuestionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Ask a question about a document"""
    try:
        # Get or create session
        if request.session_id:
            session = db.query(QASession).filter(
                QASession.id == request.session_id,
                QASession.user_id == current_user.id
            ).first()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Q&A session not found"
                )
        else:
            # Create new session (need document_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id is required"
            )
        
        # Get document
        document = db.query(Document).filter(
            Document.id == session.document_id,
            Document.owner_id == current_user.id
        ).first()
        
        if not document or not document.is_processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document not available for Q&A"
            )
        
        # Create question record
        question = QAQuestion(
            session_id=session.id,
            question=request.question
        )
        
        db.add(question)
        db.commit()
        db.refresh(question)
        
        # Find relevant context using vector search
        context = await find_relevant_context(request.question, document.id, db)
        
        # Generate answer using LLM
        start_time = datetime.utcnow()
        
        answer_result = await llm_service.answer_question(
            request.question,
            context
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Update question with answer
        question.answer = answer_result["answer"]
        question.confidence_score = answer_result["confidence"]
        question.context_used = context
        question.processing_time = processing_time
        question.model_used = answer_result["model_used"]  # Use actual model from LLM service
        question.answered_at = datetime.utcnow()
        
        # Update session
        session.total_questions += 1
        session.last_activity = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Question answered: {question.id} in session {session.id}")
        
        return QAQuestionResponse.from_orm(question)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error answering question"
        )


@router.get("/sessions/{session_id}/questions", response_model=List[QAQuestionResponse])
async def get_session_questions(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all questions for a Q&A session"""
    try:
        # Verify session ownership
        session = db.query(QASession).filter(
            QASession.id == session_id,
            QASession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Q&A session not found"
            )
        
        # Get questions
        questions = db.query(QAQuestion).filter(
            QAQuestion.session_id == session_id
        ).order_by(QAQuestion.created_at.asc()).all()
        
        return [QAQuestionResponse.from_orm(question) for question in questions]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving session questions"
        )


@router.put("/questions/{question_id}/feedback")
async def provide_feedback(
    question_id: int,
    is_helpful: bool,
    rating: Optional[int] = None,
    feedback: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Provide feedback on a question answer"""
    try:
        # Get question
        question = db.query(QAQuestion).join(QASession).filter(
            QAQuestion.id == question_id,
            QASession.user_id == current_user.id
        ).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Update feedback
        question.is_helpful = is_helpful
        if rating is not None:
            question.user_rating = rating
        if feedback:
            question.feedback = feedback
        
        db.commit()
        
        logger.info(f"Feedback provided for question {question_id}")
        return {"message": "Feedback recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error providing feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error recording feedback"
        )


@router.delete("/sessions/{session_id}")
async def delete_qa_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a Q&A session and associated document with chunks"""
    try:
        session = db.query(QASession).filter(
            QASession.id == session_id,
            QASession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Q&A session not found"
            )
        
        # Get document before deleting session
        document_id = session.document_id
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == current_user.id
        ).first()
        
        logger.info(f"Starting cleanup for session {session_id}, document {document_id}")
        
        # Delete QA questions first (due to foreign key constraints)
        questions_deleted = db.query(QAQuestion).filter(QAQuestion.session_id == session.id).delete()
        logger.info(f"Deleted {questions_deleted} QA questions")
        
        # Delete the session
        db.delete(session)
        logger.info(f"Deleted session {session_id}")
        
        # Delete document chunks
        chunks_deleted = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        logger.info(f"Deleted {chunks_deleted} document chunks")
        
        # Delete document analysis if exists
        from app.models.analysis import RiskAnalysis
        analysis_deleted = db.query(RiskAnalysis).filter(RiskAnalysis.document_id == document_id).delete()
        logger.info(f"Deleted {analysis_deleted} risk analyses")
        
        # Delete the document
        if document:
            logger.info(f"Deleting document {document_id}: {document.original_filename}")
            # Delete from Supabase storage if path exists
            if document.supabase_path:
                try:
                    from app.services.supabase_service import supabase_service
                    await supabase_service.delete_file(document.supabase_path)
                    logger.info(f"Deleted file from Supabase: {document.supabase_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete file from Supabase: {e}")
            
            db.delete(document)
            logger.info(f"Deleted document {document_id} from database")
        else:
            logger.warning(f"Document {document_id} not found for user {current_user.id}")
        
        db.commit()
        
        logger.info(f"Q&A session, document, and chunks deleted: {session_id}")
        return {"message": "Q&A session and document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Q&A session: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting Q&A session"
        )


@router.post("/sessions/{session_id}/cleanup")
async def cleanup_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clean up session and associated document when user navigates away"""
    try:
        session = db.query(QASession).filter(
            QASession.id == session_id,
            QASession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Q&A session not found"
            )
        
        # Get document before deleting session
        document_id = session.document_id
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == current_user.id
        ).first()
        
        logger.info(f"Starting cleanup for session {session_id}, document {document_id}")
        
        # Delete QA questions first (due to foreign key constraints)
        questions_deleted = db.query(QAQuestion).filter(QAQuestion.session_id == session.id).delete()
        logger.info(f"Deleted {questions_deleted} QA questions")
        
        # Delete the session
        db.delete(session)
        logger.info(f"Deleted session {session_id}")
        
        # Delete document chunks
        chunks_deleted = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        logger.info(f"Deleted {chunks_deleted} document chunks")
        
        # Delete document analysis if exists
        from app.models.analysis import RiskAnalysis
        analysis_deleted = db.query(RiskAnalysis).filter(RiskAnalysis.document_id == document_id).delete()
        logger.info(f"Deleted {analysis_deleted} risk analyses")
        
        # Delete the document
        if document:
            logger.info(f"Deleting document {document_id}: {document.original_filename}")
            # Delete from Supabase storage if path exists
            if document.supabase_path:
                try:
                    from app.services.supabase_service import supabase_service
                    await supabase_service.delete_file(document.supabase_path)
                    logger.info(f"Deleted file from Supabase: {document.supabase_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete file from Supabase: {e}")
            
            db.delete(document)
            logger.info(f"Deleted document {document_id} from database")
        else:
            logger.warning(f"Document {document_id} not found for user {current_user.id}")
        
        db.commit()
        
        logger.info(f"Session cleanup completed: {session_id}")
        return {"message": "Session cleaned up successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up session: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cleaning up session"
        )


async def find_relevant_context(question: str, document_id: int, db: Session) -> str:
    """Find relevant context for a question using vector search"""
    try:
        # Generate embedding for the question
        question_embedding = embedding_service.generate_embedding(question)

        # Retrieve a larger pool and then stitch adjacent chunks for better continuity
        base_k = 10
        chunk_ids, scores = embedding_service.search_similar(
            question_embedding,
            k=base_k,
            document_id=document_id,
            question_text=question
        )

        # Expand to include neighboring chunks (+/-1) to preserve context
        candidate_indices = set()
        for chunk_id in chunk_ids:
            if chunk_id.startswith(f"doc_{document_id}_chunk_"):
                idx = int(chunk_id.split("_")[-1])
                candidate_indices.update([idx - 1, idx, idx + 1])

        # Heuristic keyword/regex-based recall boost for monetary/consideration questions
        keywords = [
            "amount", "consideration", "price", "sum", "payment", "paid", "payable",
            "rs.", "inr", "rupees", "$", "usd", "eur", "₹"
        ]
        q_lower = question.lower()
        if any(k in q_lower for k in keywords):
            money_like = [
                "%rs.%", "%inr%", "%rupees%", "%price%", "%consideration%",
                "%amount%", "%payment%", "%paid%", "%payable%", "%usd%", "%$%", "%₹%"
            ]
            extra_chunks = (
                db.query(DocumentChunk)
                .filter(
                    DocumentChunk.document_id == document_id,
                    (
                        DocumentChunk.content.ilike(money_like[0]) |
                        DocumentChunk.content.ilike(money_like[1]) |
                        DocumentChunk.content.ilike(money_like[2]) |
                        DocumentChunk.content.ilike(money_like[3]) |
                        DocumentChunk.content.ilike(money_like[4]) |
                        DocumentChunk.content.ilike(money_like[5]) |
                        DocumentChunk.content.ilike(money_like[6]) |
                        DocumentChunk.content.ilike(money_like[7]) |
                        DocumentChunk.content.ilike(money_like[8]) |
                        DocumentChunk.content.ilike(money_like[9]) |
                        DocumentChunk.content.ilike(money_like[10]) |
                        DocumentChunk.content.ilike(money_like[11])
                    )
                )
                .with_entities(DocumentChunk.chunk_index)
                .limit(20)
                .all()
            )
            for (idx,) in extra_chunks:
                candidate_indices.update([idx - 1, idx, idx + 1])

        # Fetch candidates ordered by position
        if candidate_indices:
            ordered_chunks = (
                db.query(DocumentChunk)
                .filter(
                    DocumentChunk.document_id == document_id,
                    DocumentChunk.chunk_index.in_(sorted([i for i in candidate_indices if i >= 0]))
                )
                .order_by(DocumentChunk.chunk_index.asc())
                .all()
            )
        else:
            ordered_chunks = []

        # Concatenate up to ~3500 chars
        context_parts: list[str] = []
        total_len = 0
        for ch in ordered_chunks:
            if not ch.content:
                continue
            if total_len >= 3500:
                break
            context_parts.append(ch.content)
            total_len += len(ch.content)

        context = "\n\n".join(context_parts)
        
        # If no context found, use document summary
        if not context:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document and document.extracted_text:
                # Use first 3500 characters as fallback
                context = document.extracted_text[:3500]
        
        return context
        
    except Exception as e:
        logger.error(f"Error finding relevant context: {e}")
        return ""
