"""
Public/anonymous Q&A endpoints for landing chat.
Uploads go under supabase path prefix 'free-user/'.
Documents and sessions are deleted when the session is closed.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import Optional, List
import re
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


def _extract_payment_schedule_table(chunks_text: List[str]) -> str:
    """Build a normalized payment schedule table from chunk texts with FINANCIAL markers.

    Expected lines like:
      "On Booking Rs.[[FINANCIAL: AMOUNT: 1020000] /-]"
    Returns a markdown table with Sr., Stage, Amount.
    """
    combined = "\n".join(chunks_text)
    lines = [ln.strip() for ln in combined.splitlines() if 'FINANCIAL: AMOUNT' in ln]
    if not lines:
        return ""

    rows: List[tuple[str, str]] = []
    total_amount = 0

    for ln in lines:
        # Extract numeric amount
        m_amt = re.search(r"FINANCIAL:\s*AMOUNT:\s*([\d,]+)", ln)
        amount_raw = m_amt.group(1) if m_amt else ""
        amount_num = 0
        try:
            amount_num = int(amount_raw.replace(',', '')) if amount_raw else 0
        except Exception:
            amount_num = 0

        # Derive stage text by removing the Rs/marker sequence
        stage_text = re.sub(r"Rs\.\s*\[\[.*?\]\]\s*/-\]?", "", ln, flags=re.IGNORECASE)
        stage_text = re.sub(r"\s{2,}", " ", stage_text).strip(':- ').strip()
        # Keep it concise
        stage_text = stage_text[:120]

        if amount_num > 0:
            total_amount += amount_num
        rows.append((stage_text, amount_raw))

    if not rows:
        return ""

    # Build markdown table
    table_lines = [
        "| Sr. | Stage | Amount (INR) |",
        "| --- | ------ | ------------- |",
    ]
    for idx, (stage, amount) in enumerate(rows, 1):
        display_amt = f"{amount}/-" if amount else ""
        table_lines.append(f"| {idx} | {stage} | {display_amt} |")

    if total_amount > 0:
        table_lines.append(f"|  | Total (computed) | {total_amount:,}/- |")

    return "\n".join(table_lines)

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

        # Check if document with same hash exists and delete it first
        existing = db.query(Document).filter(Document.file_hash == file_hash, Document.owner_id == owner.id).first()
        if existing:
            logger.info(f"Found existing document with same hash, deleting it first: {existing.id}")
            # Delete existing document and all related data
            db.query(QAQuestion).filter(QAQuestion.session_id.in_(
                db.query(QASession.id).filter(QASession.document_id == existing.id)
            )).delete()
            db.query(QASession).filter(QASession.document_id == existing.id).delete()
            db.query(DocumentChunk).filter(DocumentChunk.document_id == existing.id).delete()
            from app.models.analysis import RiskAnalysis
            db.query(RiskAnalysis).filter(RiskAnalysis.document_id == existing.id).delete()
            
            # Delete from Supabase storage
            if existing.supabase_path:
                try:
                    await supabase_service.delete_file(existing.supabase_path)
                    logger.info(f"Deleted existing file from Supabase: {existing.supabase_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete existing file from Supabase: {e}")
            
            db.delete(existing)
            db.commit()
            logger.info(f"Deleted existing document {existing.id}")

        # Create new document
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
        logger.info(f"Question: {question}")
        logger.info(f"Context retrieved: {len(context)} characters")
        logger.info(f"Context preview: {context[:200]}...")
        
        # Force context retrieval if none found
        if not context.strip():
            logger.warning("No context retrieved for question, trying fallback with all chunks")
            # Fallback: get all chunks if no context found
            all_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document.id
            ).order_by(DocumentChunk.chunk_index.asc()).all()
            
            if all_chunks:
                context_parts = []
                for ch in all_chunks:  # Get ALL chunks, not just first 10
                    if ch.content:
                        context_parts.append(f"[Chunk {ch.chunk_index}]: {ch.content}")
                context = "\n\n".join(context_parts)
                logger.info(f"Fallback context: {len(context)} characters from {len(all_chunks)} chunks")
            else:
                logger.error("No chunks found for document")
                return {"answer": "I couldn't find any content in the document. Please make sure the document has been processed completely.", "confidence": 0.1, "model_used": "none", "timestamp": datetime.utcnow().isoformat()}
        
        # Additional fallback: if context is still very short, get more chunks
        if len(context) < 500:
            logger.warning(f"Context too short ({len(context)} chars), getting more chunks")
            all_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document.id
            ).order_by(DocumentChunk.chunk_index.asc()).all()
            
            if all_chunks:
                context_parts = []
                for ch in all_chunks:
                    if ch.content:
                        context_parts.append(f"[Chunk {ch.chunk_index}]: {ch.content}")
                context = "\n\n".join(context_parts)
                logger.info(f"Extended context: {len(context)} characters from {len(all_chunks)} chunks")
        
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


@router.get("/debug/document/{document_id}")
async def debug_document(document_id: int, db: Session = Depends(get_db)):
    """Debug endpoint to check document processing"""
    try:
        owner = _get_or_create_free_user(db)
        document = db.query(Document).filter(Document.id == document_id, Document.owner_id == owner.id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index.asc()).all()
        
        return {
            "document_id": document_id,
            "filename": document.filename,
            "status": document.status,
            "total_chunks": len(chunks),
            "chunks_preview": [
                {
                    "index": chunk.chunk_index,
                    "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "has_amounts": bool(re.search(r'[\d,]+(?:\.\d{2})?/-', chunk.content) or re.search(r'\$[\d,]+', chunk.content))
                }
                for chunk in chunks[:5]  # First 5 chunks
            ]
        }
    except Exception as e:
        logger.error(f"Debug error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@router.post("/cleanup-orphaned")
async def cleanup_orphaned_documents(db: Session = Depends(get_db)):
    """Clean up any orphaned documents for free users"""
    try:
        owner = _get_or_create_free_user(db)
        
        # Find documents without active sessions
        orphaned_docs = db.query(Document).filter(
            Document.owner_id == owner.id,
            ~Document.id.in_(
                db.query(QASession.document_id).filter(QASession.user_id == owner.id)
            )
        ).all()
        
        cleaned_count = 0
        for doc in orphaned_docs:
            logger.info(f"Cleaning up orphaned document: {doc.id} - {doc.original_filename}")
            
            # Delete all related data
            db.query(QAQuestion).filter(QAQuestion.session_id.in_(
                db.query(QASession.id).filter(QASession.document_id == doc.id)
            )).delete()
            db.query(QASession).filter(QASession.document_id == doc.id).delete()
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
            from app.models.analysis import RiskAnalysis
            db.query(RiskAnalysis).filter(RiskAnalysis.document_id == doc.id).delete()
            
            # Delete from Supabase storage
            if doc.supabase_path:
                try:
                    await supabase_service.delete_file(doc.supabase_path)
                    logger.info(f"Deleted orphaned file from Supabase: {doc.supabase_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete orphaned file from Supabase: {e}")
            
            db.delete(doc)
            cleaned_count += 1
        
        db.commit()
        logger.info(f"Cleaned up {cleaned_count} orphaned documents")
        return {"message": f"Cleaned up {cleaned_count} orphaned documents"}
        
    except Exception as e:
        logger.error(f"cleanup_orphaned_documents error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to cleanup orphaned documents")


# Enhanced context retrieval with financial information focus and multi-pass analysis
async def find_relevant_context(question: str, document_id: int, db: Session) -> str:
    try:
        # Check if question is money-related
        money_keywords = ['cost', 'price', 'amount', 'fee', 'payment', 'charge', 'total', 'sum', 'dollar', 'money', 'financial', 'budget', 'expense', 'revenue', 'income', 'salary', 'wage', 'bonus', 'penalty', 'fine', 'refund', 'deposit', 'advance', 'installment', 'interest', 'tax', 'commission', 'royalty', 'rent', 'lease', 'purchase', 'sale', 'value', 'worth', 'expensive', 'cheap', 'affordable', 'costly', 'free', 'paid', 'unpaid', 'due', 'overdue', 'billing', 'invoice', 'receipt', 'receivable', 'payable', 'debt', 'credit', 'loan', 'mortgage', 'investment', 'profit', 'loss', 'earnings', 'compensation', 'benefits', 'allowance', 'stipend', 'pension', 'retirement', 'insurance', 'premium', 'deductible', 'coverage', 'claim', 'settlement', 'award', 'damages', 'restitution', 'reimbursement', 'subsidy', 'grant', 'funding', 'sponsorship', 'endorsement', 'licensing', 'franchise', 'royalty', 'dividend', 'share', 'stock', 'bond', 'security', 'asset', 'liability', 'equity', 'capital', 'fund', 'treasury', 'budget', 'forecast', 'projection', 'estimate', 'quotation', 'proposal', 'bid', 'tender', 'contract', 'agreement', 'deal', 'transaction', 'exchange', 'trade', 'commerce', 'business', 'enterprise', 'corporation', 'company', 'firm', 'partnership', 'sole proprietorship', 'llc', 'inc', 'corp', 'ltd', 'llp', 'pllc', 'pc', 'pa', 'llc', 'inc', 'corp', 'ltd', 'llp', 'pllc', 'pc', 'pa']
        
        is_money_related = any(keyword in question.lower() for keyword in money_keywords)
        
        if is_money_related:
            # Detect payment schedule intent
            schedule_keywords = [
                'payment schedule', 'installment', 'instalment', 'milestone', 'stage of work',
                'schedule of payment', 'plan of payment', 'payment plan', 'due on', 'on possession',
                'on booking', 'on agreement', 'slab'
            ]
            is_schedule_query = any(k in question.lower() for k in schedule_keywords)
            
            # Multi-pass financial analysis for comprehensive data extraction
            from app.core.utils import multi_pass_financial_analysis
            
            # Get all document chunks for multi-pass analysis
            all_document_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index.asc()).all()
            
            # Combine all chunks for comprehensive analysis
            full_document_text = "\n\n".join([ch.content or "" for ch in all_document_chunks])
            
            # Perform multi-pass financial analysis
            financial_analysis = multi_pass_financial_analysis(full_document_text)
            
            logger.info(f"Multi-pass analysis found:")
            logger.info(f"- {len(financial_analysis['amounts'])} monetary amounts")
            logger.info(f"- {len(financial_analysis['payment_schedules'])} payment schedules")
            logger.info(f"- {len(financial_analysis['financial_terms'])} financial terms")
            logger.info(f"- {len(financial_analysis['tables'])} tables")
            logger.info(f"- {len(financial_analysis['calculations'])} calculations")
            
            # For money-related questions, use aggressive amount detection
            question_embedding = embedding_service.generate_embedding(question)
            base_k = 25  # Further increased for financial queries
            chunk_ids, scores = embedding_service.search_similar(question_embedding, k=base_k, document_id=document_id, question_text=question)
            
            # Get ALL chunks to ensure we don't miss amounts at the end
            all_document_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index.asc()).all()
            
            logger.info(f"Total chunks found for document {document_id}: {len(all_document_chunks)}")
            if all_document_chunks:
                logger.info(f"First chunk preview: {all_document_chunks[0].content[:200]}...")
                logger.info(f"Last chunk preview: {all_document_chunks[-1].content[:200]}...")

            # If schedule question, synthesize a table from markers
            synthesized_schedule_table = None
            if is_schedule_query and all_document_chunks:
                try:
                    synthesized_schedule_table = _extract_payment_schedule_table([ch.content or '' for ch in all_document_chunks])
                    if synthesized_schedule_table:
                        logger.info("Synthesized TABLE DATA for payment schedule")
                except Exception as e:
                    logger.warning(f"Failed to synthesize schedule table: {e}")
            
            # Find chunks with specific amount patterns - simplified approach
            amount_chunks = []
            for chunk in all_document_chunks:
                content = chunk.content
                # Look for specific amount patterns - simplified
                if (re.search(r'\$[\d,]+', content) or  # Dollar amounts
                    re.search(r'[\d,]+(?:\.\d{2})?/-', content) or  # Indian currency format
                    re.search(r'[\d,]+(?:\.\d{2})?\s*/-', content) or  # Indian currency with space
                    re.search(r'[\d,]+(?:\.\d{2})?\s*(?:dollars?|usd|eur|gbp|rupees?)', content.lower()) or  # Currency amounts
                    re.search(r'[\d,]+(?:\.\d{2})?\s*%', content) or  # Percentages
                    re.search(r'(?:total|sum|amount|cost|price|fee|charge)\s*:?\s*[\d,]+', content.lower()) or  # Financial terms
                    re.search(r'[\d,]+(?:\.\d{2})?\s*(?:total|sum|amount|cost|price|fee|charge)', content.lower())):  # Amounts with financial terms
                    amount_chunks.append(chunk)
                    logger.info(f"Found amount in chunk {chunk.chunk_index}: {content[:100]}...")
            
            # Also search for chunks containing financial terms
            financial_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.content.ilike('%$%') |  # Dollar signs
                DocumentChunk.content.ilike('%USD%') |  # Currency codes
                DocumentChunk.content.ilike('%EUR%') |
                DocumentChunk.content.ilike('%GBP%') |
                DocumentChunk.content.ilike('%CAD%') |
                DocumentChunk.content.ilike('%AUD%') |
                DocumentChunk.content.ilike('%payment%') |  # Payment terms
                DocumentChunk.content.ilike('%fee%') |
                DocumentChunk.content.ilike('%cost%') |
                DocumentChunk.content.ilike('%charge%') |
                DocumentChunk.content.ilike('%amount%') |
                DocumentChunk.content.ilike('%total%') |
                DocumentChunk.content.ilike('%price%') |
                DocumentChunk.content.ilike('%financial%') |
                DocumentChunk.content.ilike('%money%') |
                DocumentChunk.content.ilike('%budget%') |
                DocumentChunk.content.ilike('%expense%') |
                DocumentChunk.content.ilike('%revenue%') |
                DocumentChunk.content.ilike('%income%') |
                DocumentChunk.content.ilike('%salary%') |
                DocumentChunk.content.ilike('%wage%') |
                DocumentChunk.content.ilike('%bonus%') |
                DocumentChunk.content.ilike('%penalty%') |
                DocumentChunk.content.ilike('%fine%') |
                DocumentChunk.content.ilike('%refund%') |
                DocumentChunk.content.ilike('%deposit%') |
                DocumentChunk.content.ilike('%advance%') |
                DocumentChunk.content.ilike('%installment%') |
                DocumentChunk.content.ilike('%interest%') |
                DocumentChunk.content.ilike('%tax%') |
                DocumentChunk.content.ilike('%commission%') |
                DocumentChunk.content.ilike('%royalty%') |
                DocumentChunk.content.ilike('%rent%') |
                DocumentChunk.content.ilike('%lease%') |
                DocumentChunk.content.ilike('%purchase%') |
                DocumentChunk.content.ilike('%sale%') |
                DocumentChunk.content.ilike('%value%') |
                DocumentChunk.content.ilike('%worth%') |
                DocumentChunk.content.ilike('%expensive%') |
                DocumentChunk.content.ilike('%cheap%') |
                DocumentChunk.content.ilike('%affordable%') |
                DocumentChunk.content.ilike('%costly%') |
                DocumentChunk.content.ilike('%free%') |
                DocumentChunk.content.ilike('%paid%') |
                DocumentChunk.content.ilike('%unpaid%') |
                DocumentChunk.content.ilike('%due%') |
                DocumentChunk.content.ilike('%overdue%') |
                DocumentChunk.content.ilike('%billing%') |
                DocumentChunk.content.ilike('%invoice%') |
                DocumentChunk.content.ilike('%receipt%') |
                DocumentChunk.content.ilike('%receivable%') |
                DocumentChunk.content.ilike('%payable%') |
                DocumentChunk.content.ilike('%debt%') |
                DocumentChunk.content.ilike('%credit%') |
                DocumentChunk.content.ilike('%loan%') |
                DocumentChunk.content.ilike('%mortgage%') |
                DocumentChunk.content.ilike('%investment%') |
                DocumentChunk.content.ilike('%profit%') |
                DocumentChunk.content.ilike('%loss%') |
                DocumentChunk.content.ilike('%earnings%') |
                DocumentChunk.content.ilike('%compensation%') |
                DocumentChunk.content.ilike('%benefits%') |
                DocumentChunk.content.ilike('%allowance%') |
                DocumentChunk.content.ilike('%stipend%') |
                DocumentChunk.content.ilike('%pension%') |
                DocumentChunk.content.ilike('%retirement%') |
                DocumentChunk.content.ilike('%insurance%') |
                DocumentChunk.content.ilike('%premium%') |
                DocumentChunk.content.ilike('%deductible%') |
                DocumentChunk.content.ilike('%coverage%') |
                DocumentChunk.content.ilike('%claim%') |
                DocumentChunk.content.ilike('%settlement%') |
                DocumentChunk.content.ilike('%award%') |
                DocumentChunk.content.ilike('%damages%') |
                DocumentChunk.content.ilike('%restitution%') |
                DocumentChunk.content.ilike('%reimbursement%') |
                DocumentChunk.content.ilike('%subsidy%') |
                DocumentChunk.content.ilike('%grant%') |
                DocumentChunk.content.ilike('%funding%') |
                DocumentChunk.content.ilike('%sponsorship%') |
                DocumentChunk.content.ilike('%endorsement%') |
                DocumentChunk.content.ilike('%licensing%') |
                DocumentChunk.content.ilike('%franchise%') |
                DocumentChunk.content.ilike('%royalty%') |
                DocumentChunk.content.ilike('%dividend%') |
                DocumentChunk.content.ilike('%share%') |
                DocumentChunk.content.ilike('%stock%') |
                DocumentChunk.content.ilike('%bond%') |
                DocumentChunk.content.ilike('%security%') |
                DocumentChunk.content.ilike('%asset%') |
                DocumentChunk.content.ilike('%liability%') |
                DocumentChunk.content.ilike('%equity%') |
                DocumentChunk.content.ilike('%capital%') |
                DocumentChunk.content.ilike('%fund%') |
                DocumentChunk.content.ilike('%treasury%') |
                DocumentChunk.content.ilike('%budget%') |
                DocumentChunk.content.ilike('%forecast%') |
                DocumentChunk.content.ilike('%projection%') |
                DocumentChunk.content.ilike('%estimate%') |
                DocumentChunk.content.ilike('%quotation%') |
                DocumentChunk.content.ilike('%proposal%') |
                DocumentChunk.content.ilike('%bid%') |
                DocumentChunk.content.ilike('%tender%') |
                DocumentChunk.content.ilike('%contract%') |
                DocumentChunk.content.ilike('%agreement%') |
                DocumentChunk.content.ilike('%deal%') |
                DocumentChunk.content.ilike('%transaction%') |
                DocumentChunk.content.ilike('%exchange%') |
                DocumentChunk.content.ilike('%trade%') |
                DocumentChunk.content.ilike('%commerce%') |
                DocumentChunk.content.ilike('%business%') |
                DocumentChunk.content.ilike('%enterprise%') |
                DocumentChunk.content.ilike('%corporation%') |
                DocumentChunk.content.ilike('%company%') |
                DocumentChunk.content.ilike('%firm%') |
                DocumentChunk.content.ilike('%partnership%') |
                DocumentChunk.content.ilike('%sole proprietorship%') |
                DocumentChunk.content.ilike('%llc%') |
                DocumentChunk.content.ilike('%inc%') |
                DocumentChunk.content.ilike('%corp%') |
                DocumentChunk.content.ilike('%ltd%') |
                DocumentChunk.content.ilike('%llp%') |
                DocumentChunk.content.ilike('%pllc%') |
                DocumentChunk.content.ilike('%pc%') |
                DocumentChunk.content.ilike('%pa%')
            ).all()
            
            # Combine all chunk sources
            candidate_indices = set()
            
            # Add semantic search results
            for chunk_id in chunk_ids:
                if chunk_id.startswith(f"doc_{document_id}_chunk_"):
                    idx = int(chunk_id.split("_")[-1])
                    candidate_indices.update([idx - 3, idx - 2, idx - 1, idx, idx + 1, idx + 2, idx + 3])
            
            # Add amount chunks (highest priority)
            logger.info(f"Found {len(amount_chunks)} chunks with amounts for document {document_id}")
            for chunk in amount_chunks:
                logger.info(f"Amount chunk {chunk.chunk_index}: {chunk.content[:100]}...")
                candidate_indices.add(chunk.chunk_index)
                # Include more surrounding context for amount chunks
                candidate_indices.update([chunk.chunk_index - 2, chunk.chunk_index - 1, chunk.chunk_index + 1, chunk.chunk_index + 2])
            
            # Add financial chunks
            for chunk in financial_chunks:
                candidate_indices.add(chunk.chunk_index)
                candidate_indices.update([chunk.chunk_index - 1, chunk.chunk_index + 1])
            
            # Get all chunks in order
            all_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.chunk_index.in_(sorted([i for i in candidate_indices if i >= 0]))
            ).order_by(DocumentChunk.chunk_index.asc()).all()
            
        else:
            # Regular semantic search for non-financial questions
            question_embedding = embedding_service.generate_embedding(question)
            base_k = 15
            chunk_ids, scores = embedding_service.search_similar(question_embedding, k=base_k, document_id=document_id, question_text=question)
            candidate_indices = set()
            for chunk_id in chunk_ids:
                if chunk_id.startswith(f"doc_{document_id}_chunk_"):
                    idx = int(chunk_id.split("_")[-1])
                    candidate_indices.update([idx - 2, idx - 1, idx, idx + 1, idx + 2])
            
            all_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.chunk_index.in_(sorted([i for i in candidate_indices if i >= 0]))
            ).order_by(DocumentChunk.chunk_index.asc()).all()
        
        # Build context with enhanced financial analysis
        context_parts = []
        
        # Add comprehensive financial analysis summary
        if is_money_related and 'financial_analysis' in locals():
            context_parts.append("=== COMPREHENSIVE FINANCIAL ANALYSIS ===")
            
            # Add monetary amounts with context
            if financial_analysis['amounts']:
                context_parts.append(f"\nMONETARY AMOUNTS FOUND ({len(financial_analysis['amounts'])}):")
                for i, amount_data in enumerate(financial_analysis['amounts'][:10]):  # Limit to first 10
                    context_parts.append(f"{i+1}. {amount_data['amount']} - Context: {amount_data['context']}")
            
            # Add payment schedules
            if financial_analysis['payment_schedules']:
                context_parts.append(f"\nPAYMENT SCHEDULES FOUND ({len(financial_analysis['payment_schedules'])}):")
                for i, schedule in enumerate(financial_analysis['payment_schedules'][:3]):  # Limit to first 3
                    context_parts.append(f"{i+1}. {schedule['text'][:200]}...")
            
            # Add financial terms
            if financial_analysis['financial_terms']:
                context_parts.append(f"\nFINANCIAL TERMS FOUND ({len(financial_analysis['financial_terms'])}):")
                for i, term in enumerate(financial_analysis['financial_terms'][:10]):  # Limit to first 10
                    context_parts.append(f"{i+1}. {term['term']}")
            
            # Add tables
            if financial_analysis['tables']:
                context_parts.append(f"\nTABLES FOUND ({len(financial_analysis['tables'])}):")
                for i, table in enumerate(financial_analysis['tables'][:3]):  # Limit to first 3
                    context_parts.append(f"Table {i+1} ({table['type']}): Headers: {table['headers']}")
                    for j, row in enumerate(table['rows'][:5]):  # First 5 rows
                        context_parts.append(f"  Row {j+1}: {row['data']}")
            
            # Add calculations
            if financial_analysis['calculations']:
                context_parts.append(f"\nCALCULATIONS FOUND ({len(financial_analysis['calculations'])}):")
                for i, calc in enumerate(financial_analysis['calculations'][:5]):  # Limit to first 5
                    context_parts.append(f"{i+1}. {calc['calculation']}")
            
            context_parts.append("\n=== END FINANCIAL ANALYSIS ===\n")
        
        # Prepend TABLE DATA if we synthesized a schedule
        try:
            if is_money_related and 'is_schedule_query' in locals() and is_schedule_query and 'synthesized_schedule_table' in locals() and synthesized_schedule_table:
                context_parts.append("TABLE DATA:\n" + synthesized_schedule_table)
        except Exception:
            pass
        
        total_len = 0
        max_context_length = 8000  # Increased for comprehensive financial analysis
        
        logger.info(f"Building context from {len(all_chunks)} chunks for document {document_id}")
        
        for ch in all_chunks:
            if not ch.content:
                continue
            if total_len >= max_context_length:
                logger.info(f"Context length limit reached at {total_len} characters")
                break
            context_parts.append(f"[Chunk {ch.chunk_index}]: {ch.content}")
            total_len += len(ch.content)
        
        context = "\n\n".join(context_parts)
        logger.info(f"Final context length: {len(context)} characters")
        logger.info(f"Context preview: {context[:500]}...")
        
        return context
        
    except Exception as e:
        logger.error(f"Error in find_relevant_context: {e}")
        return ""


