"""
Analysis Pydantic schemas
"""

from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RiskType(str, Enum):
    """Risk type enumeration"""
    AUTO_RENEWAL = "auto_renewal"
    UNLIMITED_LIABILITY = "unlimited_liability"
    HIDDEN_FEES = "hidden_fees"
    UNFAIR_TERMS = "unfair_terms"
    AMBIGUOUS_LANGUAGE = "ambiguous_language"
    MISSING_CLAUSES = "missing_clauses"
    TERMINATION_RISKS = "termination_risks"
    OTHER = "other"


class RiskAnalysisResponse(BaseModel):
    """Schema for risk analysis response"""
    id: int
    risk_level: RiskLevel
    risk_type: RiskType
    description: str
    location: Optional[str] = None
    recommendation: Optional[str] = None
    severity_score: Optional[float] = None
    likelihood_score: Optional[float] = None
    overall_score: Optional[float] = None
    clause_reference: Optional[str] = None
    page_number: Optional[int] = None
    line_number: Optional[int] = None
    created_at: datetime
    document_id: int
    
    class Config:
        from_attributes = True


class RiskAnalysisSummary(BaseModel):
    """Schema for risk analysis summary"""
    total_risks: int
    high_risks: int
    medium_risks: int
    low_risks: int
    risk_types: Dict[str, int]
    overall_risk_score: float
    recommendations: List[str]


class QAQuestionCreate(BaseModel):
    """Schema for creating a Q&A question"""
    question: str
    session_id: Optional[int] = None


class QAQuestionResponse(BaseModel):
    """Schema for Q&A question response"""
    id: int
    question: str
    answer: Optional[str] = None
    confidence_score: Optional[float] = None
    context_used: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    is_helpful: Optional[bool] = None
    user_rating: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime
    answered_at: Optional[datetime] = None
    session_id: int
    
    class Config:
        from_attributes = True


class QASessionCreate(BaseModel):
    """Schema for creating a Q&A session"""
    session_name: Optional[str] = None
    document_id: int


class QASessionResponse(BaseModel):
    """Schema for Q&A session response"""
    id: int
    session_name: Optional[str] = None
    is_active: bool
    total_questions: int
    last_activity: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: int
    document_id: int
    questions: Optional[List[QAQuestionResponse]] = None
    
    class Config:
        from_attributes = True


class ComparisonCreate(BaseModel):
    """Schema for creating a document comparison"""
    comparison_name: Optional[str] = None
    document1_id: int
    document2_id: int
    comparison_type: str = "custom"


class ComparisonResponse(BaseModel):
    """Schema for comparison response"""
    id: int
    comparison_name: Optional[str] = None
    summary: Optional[str] = None
    key_differences: Optional[List[Dict[str, Any]]] = None
    similarities: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    comparison_type: str
    similarity_score: Optional[float] = None
    risk_comparison: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    created_at: datetime
    user_id: int
    document1_id: int
    document2_id: int
    
    class Config:
        from_attributes = True


class SummaryRequest(BaseModel):
    """Schema for document summarization request"""
    document_id: int
    summary_type: str = "comprehensive"  # comprehensive, executive, detailed
    include_risks: bool = True
    include_obligations: bool = True
    include_financial_terms: bool = True


class SummaryResponse(BaseModel):
    """Schema for document summary response"""
    document_id: int
    summary: str
    structured_summary: Dict[str, Any]
    word_count: int
    analysis_date: datetime
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None


class RiskDetectionRequest(BaseModel):
    """Schema for risk detection request"""
    document_id: int
    risk_types: Optional[List[RiskType]] = None
    min_confidence: float = 0.5


class RiskDetectionResponse(BaseModel):
    """Schema for risk detection response"""
    document_id: int
    risks: List[RiskAnalysisResponse]
    summary: RiskAnalysisSummary
    processing_time: Optional[float] = None
