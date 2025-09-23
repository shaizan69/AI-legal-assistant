"""
Document Pydantic schemas
"""

from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Document type enumeration"""
    CONTRACT = "contract"
    AGREEMENT = "agreement"
    TERMS = "terms"
    POLICY = "policy"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUpload(BaseModel):
    """Schema for document upload"""
    title: Optional[str] = None
    document_type: Optional[DocumentType] = None
    description: Optional[str] = None


class DocumentMetadata(BaseModel):
    """Schema for document metadata"""
    filename: str
    file_size: int
    mime_type: str
    word_count: int
    character_count: int
    document_type: Optional[str] = None
    title: Optional[str] = None
    parties: Optional[List[str]] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None


class DocumentChunkResponse(BaseModel):
    """Schema for document chunk response"""
    id: int
    chunk_index: int
    content: str
    word_count: int
    character_count: int
    section_title: Optional[str] = None
    clause_number: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentAnalysisResponse(BaseModel):
    """Schema for document analysis response"""
    id: int
    analysis_type: str
    summary: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    model_used: Optional[str] = None
    processing_time: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: int
    filename: str
    original_filename: str
    # Storage info
    file_url: Optional[str] = None
    file_path: str
    supabase_path: Optional[str] = None
    file_size: int
    mime_type: str
    word_count: int
    character_count: int
    document_type: Optional[str] = None
    title: Optional[str] = None
    parties: Optional[List[str]] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    is_processed: bool
    processing_status: ProcessingStatus
    processing_error: Optional[str] = None
    extracted_text: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner_id: int
    
    # Analysis results
    analyses: Optional[List[DocumentAnalysisResponse]] = None
    chunks: Optional[List[DocumentChunkResponse]] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for document list response"""
    documents: List[DocumentResponse]
    total: int
    page: int
    size: int
    pages: int


class DocumentSearchRequest(BaseModel):
    """Schema for document search request"""
    query: str
    document_type: Optional[DocumentType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    size: int = 10


class DocumentSearchResponse(BaseModel):
    """Schema for document search response"""
    documents: List[DocumentResponse]
    total: int
    page: int
    size: int
    query: str
