"""
Document models for storing uploaded documents and their metadata
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Document(Base):
    """Document model for storing uploaded files and metadata"""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(1000), nullable=True)  # Supabase public URL
    file_hash = Column(String(64), unique=True, index=True, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    supabase_path = Column(String(500), nullable=True)  # Supabase storage path
    
    # Document content
    extracted_text = Column(Text, nullable=True)
    text_hash = Column(String(64), index=True, nullable=True)
    word_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    
    # Document metadata
    document_type = Column(String(100), nullable=True)  # contract, agreement, etc.
    title = Column(String(500), nullable=True)
    parties = Column(JSON, nullable=True)  # List of parties involved
    effective_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="documents")
    analyses = relationship("DocumentAnalysis", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.document_type}')>"


class DocumentChunk(Base):
    """Document chunks for vector search and processing"""
    
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    
    # Vector information - using pgvector
    embedding = Column(String, nullable=True)  # pgvector column for embeddings
    has_embedding = Column(Boolean, default=False)
    
    # Chunk metadata
    start_position = Column(Integer, nullable=True)  # Position in original document
    end_position = Column(Integer, nullable=True)
    section_title = Column(String(500), nullable=True)
    clause_number = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign keys
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


class DocumentAnalysis(Base):
    """Document analysis results"""
    
    __tablename__ = "document_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String(50), nullable=False)  # summary, risk, comparison, etc.
    
    # Analysis results
    summary = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Analysis metadata
    model_used = Column(String(100), nullable=True)
    processing_time = Column(Float, nullable=True)  # seconds
    token_count = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign keys
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="analyses")
    
    def __repr__(self):
        return f"<DocumentAnalysis(id={self.id}, type='{self.analysis_type}', document_id={self.document_id})>"
