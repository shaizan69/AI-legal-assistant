"""
Document comparison API endpoints
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
from app.models.document import Document
from app.models.analysis import Comparison
from app.schemas.analysis import ComparisonCreate, ComparisonResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ComparisonResponse)
async def compare_documents(
    request: ComparisonCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Compare two documents"""
    try:
        # Get both documents
        document1 = db.query(Document).filter(
            Document.id == request.document1_id,
            Document.owner_id == current_user.id
        ).first()
        
        document2 = db.query(Document).filter(
            Document.id == request.document2_id,
            Document.owner_id == current_user.id
        ).first()
        
        if not document1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="First document not found"
            )
        
        if not document2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Second document not found"
            )
        
        if not document1.is_processed or not document2.is_processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or both documents are still being processed"
            )
        
        if not document1.extracted_text or not document2.extracted_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or both documents have no text content for comparison"
            )
        
        # Check if comparison already exists
        existing_comparison = db.query(Comparison).filter(
            Comparison.user_id == current_user.id,
            Comparison.document1_id == request.document1_id,
            Comparison.document2_id == request.document2_id
        ).first()
        
        if existing_comparison and not request.force_regenerate:
            return ComparisonResponse.from_orm(existing_comparison)
        
        # Generate comparison using LLM
        start_time = datetime.utcnow()
        
        comparison_result = await llm_service.compare_documents(
            document1.extracted_text,
            document2.extracted_text,
            document1.title or f"Document {document1.id}",
            document2.title or f"Document {document2.id}"
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Calculate similarity score (simple implementation)
        similarity_score = calculate_similarity_score(
            document1.extracted_text,
            document2.extracted_text
        )
        
        # Create or update comparison
        if existing_comparison:
            existing_comparison.summary = comparison_result["comparison"]
            existing_comparison.key_differences = comparison_result["structured"].get("key_differences", [])
            existing_comparison.similarities = comparison_result["structured"].get("similarities", [])
            existing_comparison.recommendations = comparison_result["structured"].get("recommendations", [])
            existing_comparison.similarity_score = similarity_score
            existing_comparison.processing_time = processing_time
            existing_comparison.model_used = "gpt-3.5-turbo"
        else:
            comparison = Comparison(
                user_id=current_user.id,
                document1_id=request.document1_id,
                document2_id=request.document2_id,
                comparison_name=request.comparison_name,
                summary=comparison_result["comparison"],
                key_differences=comparison_result["structured"].get("key_differences", []),
                similarities=comparison_result["structured"].get("similarities", []),
                recommendations=comparison_result["structured"].get("recommendations", []),
                comparison_type=request.comparison_type,
                similarity_score=similarity_score,
                processing_time=processing_time,
                model_used="gpt-3.5-turbo"
            )
            db.add(comparison)
        
        db.commit()
        
        # Get the comparison object for response
        if existing_comparison:
            comparison = existing_comparison
        else:
            db.refresh(comparison)
        
        logger.info(f"Document comparison completed: {document1.id} vs {document2.id}")
        
        return ComparisonResponse.from_orm(comparison)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error comparing documents"
        )


@router.get("/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison(
    comparison_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific comparison by ID"""
    try:
        comparison = db.query(Comparison).filter(
            Comparison.id == comparison_id,
            Comparison.user_id == current_user.id
        ).first()
        
        if not comparison:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comparison not found"
            )
        
        return ComparisonResponse.from_orm(comparison)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving comparison"
        )


@router.get("/", response_model=List[ComparisonResponse])
async def get_user_comparisons(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all comparisons for the current user"""
    try:
        comparisons = db.query(Comparison).filter(
            Comparison.user_id == current_user.id
        ).order_by(Comparison.created_at.desc()).all()
        
        return [ComparisonResponse.from_orm(comparison) for comparison in comparisons]
        
    except Exception as e:
        logger.error(f"Error getting user comparisons: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving comparisons"
        )


@router.delete("/{comparison_id}")
async def delete_comparison(
    comparison_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a comparison"""
    try:
        comparison = db.query(Comparison).filter(
            Comparison.id == comparison_id,
            Comparison.user_id == current_user.id
        ).first()
        
        if not comparison:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comparison not found"
            )
        
        db.delete(comparison)
        db.commit()
        
        logger.info(f"Comparison deleted: {comparison_id}")
        return {"message": "Comparison deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting comparison: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting comparison"
        )


def calculate_similarity_score(text1: str, text2: str) -> float:
    """Calculate similarity score between two texts"""
    try:
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        # Jaccard similarity
        similarity = len(intersection) / len(union) if union else 0.0
        
        return min(1.0, similarity)
        
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return 0.0
