"""
Analysis models for risk detection, Q&A, and comparisons
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class RiskAnalysis(Base):
    """Risk analysis results for documents"""
    
    __tablename__ = "risk_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    risk_level = Column(String(20), nullable=False)  # High, Medium, Low
    risk_type = Column(String(100), nullable=False)  # auto_renewal, liability, etc.
    description = Column(Text, nullable=False)
    location = Column(String(500), nullable=True)  # Where in document
    recommendation = Column(Text, nullable=True)
    
    # Risk scoring
    severity_score = Column(Float, nullable=True)  # 0.0 to 1.0
    likelihood_score = Column(Float, nullable=True)  # 0.0 to 1.0
    overall_score = Column(Float, nullable=True)  # Combined score
    
    # Additional metadata
    clause_reference = Column(String(200), nullable=True)
    page_number = Column(Integer, nullable=True)
    line_number = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign keys
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Relationships
    document = relationship("Document")
    
    def __repr__(self):
        return f"<RiskAnalysis(id={self.id}, level='{self.risk_level}', type='{self.risk_type}')>"


class QASession(Base):
    """Q&A session for document interaction"""
    
    __tablename__ = "qa_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Session metadata
    total_questions = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="qa_sessions")
    document = relationship("Document")
    questions = relationship("QAQuestion", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QASession(id={self.id}, user_id={self.user_id}, document_id={self.document_id})>"


class QAQuestion(Base):
    """Individual Q&A questions and answers"""
    
    __tablename__ = "qa_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    
    # Answer quality metrics
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    context_used = Column(Text, nullable=True)  # Context from document
    sources = Column(JSON, nullable=True)  # References to document sections
    
    # Processing metadata
    processing_time = Column(Float, nullable=True)  # seconds
    model_used = Column(String(100), nullable=True)
    token_count = Column(Integer, nullable=True)
    
    # User feedback
    is_helpful = Column(Boolean, nullable=True)
    user_rating = Column(Integer, nullable=True)  # 1-5 scale
    feedback = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    answered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    session_id = Column(Integer, ForeignKey("qa_sessions.id"), nullable=False)
    
    # Relationships
    session = relationship("QASession", back_populates="questions")
    
    def __repr__(self):
        return f"<QAQuestion(id={self.id}, session_id={self.session_id}, question='{self.question[:50]}...')>"


class Comparison(Base):
    """Document comparison results"""
    
    __tablename__ = "comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    comparison_name = Column(String(255), nullable=True)
    
    # Comparison results
    summary = Column(Text, nullable=True)
    key_differences = Column(JSON, nullable=True)  # List of differences
    similarities = Column(JSON, nullable=True)  # List of similarities
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    
    # Comparison metadata
    comparison_type = Column(String(50), nullable=False)  # template, version, custom
    similarity_score = Column(Float, nullable=True)  # Overall similarity 0.0 to 1.0
    risk_comparison = Column(JSON, nullable=True)  # Risk analysis comparison
    
    # Processing metadata
    processing_time = Column(Float, nullable=True)  # seconds
    model_used = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document1_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    document2_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="comparisons")
    document1 = relationship("Document", foreign_keys=[document1_id])
    document2 = relationship("Document", foreign_keys=[document2_id])
    
    def __repr__(self):
        return f"<Comparison(id={self.id}, doc1_id={self.document1_id}, doc2_id={self.document2_id})>"
