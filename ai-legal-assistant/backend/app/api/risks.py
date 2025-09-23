"""
Risk detection API endpoints
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
from app.models.analysis import RiskAnalysis
from app.schemas.analysis import RiskDetectionRequest, RiskDetectionResponse, RiskAnalysisResponse, RiskAnalysisSummary

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=RiskDetectionResponse)
async def detect_risks(
    request: RiskDetectionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Detect risks in a document"""
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
                detail="No text content available for risk analysis"
            )
        
        # Check if risk analysis already exists
        existing_risks = db.query(RiskAnalysis).filter(
            RiskAnalysis.document_id == request.document_id
        ).all()
        
        if existing_risks and not request.force_regenerate:
            return RiskDetectionResponse(
                document_id=document.id,
                risks=[RiskAnalysisResponse.from_orm(risk) for risk in existing_risks],
                summary=create_risk_summary(existing_risks),
                processing_time=None
            )
        
        # Generate risk analysis using LLM
        start_time = datetime.utcnow()
        
        risk_analysis = await llm_service.detect_risks(document.extracted_text)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Clear existing risks if regenerating
        if existing_risks:
            for risk in existing_risks:
                db.delete(risk)
        
        # Save new risk analyses
        risk_objects = []
        for risk_data in risk_analysis:
            risk_obj = RiskAnalysis(
                document_id=document.id,
                risk_level=risk_data.get("risk_level", "Medium"),
                risk_type=risk_data.get("risk_type", "other"),
                description=risk_data.get("description", ""),
                location=risk_data.get("location"),
                recommendation=risk_data.get("recommendation"),
                severity_score=risk_data.get("severity_score"),
                likelihood_score=risk_data.get("likelihood_score"),
                overall_score=risk_data.get("overall_score"),
                clause_reference=risk_data.get("clause_reference"),
                page_number=risk_data.get("page_number"),
                line_number=risk_data.get("line_number")
            )
            risk_objects.append(risk_obj)
            db.add(risk_obj)
        
        db.commit()
        
        logger.info(f"Risk analysis completed for document {document.id}: {len(risk_objects)} risks found")
        
        return RiskDetectionResponse(
            document_id=document.id,
            risks=[RiskAnalysisResponse.from_orm(risk) for risk in risk_objects],
            summary=create_risk_summary(risk_objects),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting risks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error detecting document risks"
        )


@router.get("/{document_id}", response_model=RiskDetectionResponse)
async def get_document_risks(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get risk analysis for a document"""
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
        
        # Get risk analyses
        risks = db.query(RiskAnalysis).filter(
            RiskAnalysis.document_id == document_id
        ).all()
        
        if not risks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No risk analysis found for this document"
            )
        
        return RiskDetectionResponse(
            document_id=document.id,
            risks=[RiskAnalysisResponse.from_orm(risk) for risk in risks],
            summary=create_risk_summary(risks),
            processing_time=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving document risks"
        )


@router.get("/", response_model=List[RiskAnalysisResponse])
async def get_all_risks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all risk analyses for user's documents"""
    try:
        # Get all risk analyses for user's documents
        risks = db.query(RiskAnalysis).join(Document).filter(
            Document.owner_id == current_user.id
        ).all()
        
        return [RiskAnalysisResponse.from_orm(risk) for risk in risks]
        
    except Exception as e:
        logger.error(f"Error getting all risks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving risk analyses"
        )


@router.delete("/{document_id}")
async def delete_document_risks(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete risk analysis for a document"""
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
        
        # Get and delete risk analyses
        risks = db.query(RiskAnalysis).filter(
            RiskAnalysis.document_id == document_id
        ).all()
        
        for risk in risks:
            db.delete(risk)
        
        db.commit()
        
        logger.info(f"Risk analysis deleted for document {document_id}")
        return {"message": "Risk analysis deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting risks: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting document risk analysis"
        )


def create_risk_summary(risks: List[RiskAnalysis]) -> RiskAnalysisSummary:
    """Create risk analysis summary from risk objects"""
    if not risks:
        return RiskAnalysisSummary(
            total_risks=0,
            high_risks=0,
            medium_risks=0,
            low_risks=0,
            risk_types={},
            overall_risk_score=0.0,
            recommendations=[]
        )
    
    # Count risks by level
    high_risks = sum(1 for risk in risks if risk.risk_level == "High")
    medium_risks = sum(1 for risk in risks if risk.risk_level == "Medium")
    low_risks = sum(1 for risk in risks if risk.risk_level == "Low")
    
    # Count risks by type
    risk_types = {}
    for risk in risks:
        risk_type = risk.risk_type
        risk_types[risk_type] = risk_types.get(risk_type, 0) + 1
    
    # Calculate overall risk score
    if risks:
        overall_score = sum(risk.overall_score or 0.5 for risk in risks) / len(risks)
    else:
        overall_score = 0.0
    
    # Collect recommendations
    recommendations = [risk.recommendation for risk in risks if risk.recommendation]
    
    return RiskAnalysisSummary(
        total_risks=len(risks),
        high_risks=high_risks,
        medium_risks=medium_risks,
        low_risks=low_risks,
        risk_types=risk_types,
        overall_risk_score=overall_score,
        recommendations=recommendations
    )
