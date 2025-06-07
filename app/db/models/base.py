"""
Base database models for the DSPy-Enhanced Fact-Checker API Platform.
"""

from sqlalchemy import Column, Integer, DateTime, String, Text, Boolean, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from typing import Any, Dict

from app.db.database import Base


class TimestampMixin:
    """Mixin for timestamp fields."""
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UUIDMixin:
    """Mixin for UUID primary key."""
    
    id = Column(String(36), primary_key=True, index=True)


class BaseModel(Base, TimestampMixin, UUIDMixin):
    """Base model with common fields."""
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name."""
        return cls.__name__.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class ProcessingJob(BaseModel):
    """Base model for processing jobs."""
    
    __tablename__ = "processing_jobs"
    
    # Job identification
    job_type = Column(String(50), nullable=False, index=True)  # document, text, url
    status = Column(String(20), nullable=False, default="pending", index=True)
    priority = Column(String(10), nullable=False, default="normal", index=True)
    
    # Processing details
    input_data = Column(JSON, nullable=False)
    processing_options = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    
    # Progress tracking
    progress = Column(Float, default=0.0, nullable=False)
    current_stage = Column(String(100), nullable=True)
    estimated_completion_time = Column(Integer, nullable=True)  # seconds
    actual_processing_time = Column(Float, nullable=True)  # seconds
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Metadata
    user_id = Column(String(36), nullable=True, index=True)
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    callback_url = Column(String(500), nullable=True)
    
    # Cost tracking
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)


class Document(BaseModel):
    """Model for uploaded documents."""
    
    __tablename__ = "documents"
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=True)
    content_type = Column(String(100), nullable=True)
    
    # Processing information
    processing_job_id = Column(String(36), nullable=False, index=True)
    extraction_method = Column(String(50), nullable=True)
    extraction_confidence = Column(Float, nullable=True)
    
    # Document metadata
    title = Column(String(500), nullable=True)
    author = Column(String(255), nullable=True)
    creation_date = Column(DateTime, nullable=True)
    modification_date = Column(DateTime, nullable=True)
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    language = Column(String(10), nullable=True)
    
    # Content
    extracted_text = Column(Text, nullable=True)
    structured_content = Column(JSON, nullable=True)
    tables = Column(JSON, nullable=True)
    images = Column(JSON, nullable=True)
    
    # Analysis results
    claims = Column(JSON, nullable=True)
    overall_verdict = Column(String(50), nullable=True)
    accuracy_score = Column(Float, nullable=True)
    
    # Status
    is_processed = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)


class TextAnalysis(BaseModel):
    """Model for text analysis results."""
    
    __tablename__ = "text_analyses"
    
    # Input information
    processing_job_id = Column(String(36), nullable=False, index=True)
    input_text = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    optimization_level = Column(String(20), nullable=False)
    
    # Analysis results
    language = Column(String(10), nullable=True)
    word_count = Column(Integer, nullable=False)
    character_count = Column(Integer, nullable=False)
    sentence_count = Column(Integer, nullable=False)
    paragraph_count = Column(Integer, nullable=False)
    reading_time = Column(Float, nullable=True)
    complexity_score = Column(Float, nullable=True)
    
    # Content analysis
    topics = Column(JSON, nullable=True)
    sentiment = Column(String(20), nullable=True)
    segments = Column(JSON, nullable=True)
    
    # Fact-checking results
    claims = Column(JSON, nullable=True)
    overall_verdict = Column(String(50), nullable=True)
    confidence_score = Column(Float, nullable=True)
    claims_analyzed = Column(Integer, default=0, nullable=False)
    
    # Processing metadata
    processing_time = Column(Float, nullable=True)
    is_processed = Column(Boolean, default=False, nullable=False)


class URLAnalysis(BaseModel):
    """Model for URL analysis results."""
    
    __tablename__ = "url_analyses"
    
    # URL information
    processing_job_id = Column(String(36), nullable=False, index=True)
    original_url = Column(String(2000), nullable=False)
    final_url = Column(String(2000), nullable=True)
    domain = Column(String(255), nullable=False, index=True)
    
    # Access information
    is_accessible = Column(Boolean, default=False, nullable=False)
    response_code = Column(Integer, nullable=True)
    content_type = Column(String(50), nullable=True)
    
    # Content extraction
    title = Column(String(500), nullable=True)
    author = Column(String(255), nullable=True)
    publication_date = Column(DateTime, nullable=True)
    extracted_content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    images = Column(JSON, nullable=True)
    links = Column(JSON, nullable=True)
    
    # Source analysis
    credibility_score = Column(Float, nullable=True)
    bias_rating = Column(String(50), nullable=True)
    factual_reporting = Column(String(50), nullable=True)
    domain_age = Column(String(50), nullable=True)
    alexa_rank = Column(Integer, nullable=True)
    
    # Fact-checking results
    claims = Column(JSON, nullable=True)
    overall_verdict = Column(String(50), nullable=True)
    accuracy_score = Column(Float, nullable=True)
    
    # Processing metadata
    extraction_method = Column(String(50), nullable=True)
    extraction_confidence = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)
    is_processed = Column(Boolean, default=False, nullable=False)


class FactCheckResult(BaseModel):
    """Model for individual fact-check results."""
    
    __tablename__ = "fact_check_results"
    
    # Reference to parent analysis
    processing_job_id = Column(String(36), nullable=False, index=True)
    parent_type = Column(String(20), nullable=False, index=True)  # document, text, url
    parent_id = Column(String(36), nullable=False, index=True)
    
    # Claim information
    claim = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    location = Column(JSON, nullable=True)  # Position in source
    
    # Verification results
    verdict = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    evidence = Column(JSON, nullable=True)
    sources = Column(JSON, nullable=True)
    cross_references = Column(JSON, nullable=True)
    
    # Analysis metadata
    verification_method = Column(String(50), nullable=True)
    processing_time = Column(Float, nullable=True)
    uncertainty_factors = Column(JSON, nullable=True)


class SystemMetrics(BaseModel):
    """Model for system performance metrics."""
    
    __tablename__ = "system_metrics"
    
    # Metric identification
    metric_type = Column(String(50), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    
    # Metric values
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)
    
    # Context
    context = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Timestamp (using created_at from TimestampMixin)


class UserSession(BaseModel):
    """Model for user sessions and API usage tracking."""

    __tablename__ = "api_sessions"
    
    # Session identification
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    
    # Client information
    client_ip = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text, nullable=True)
    
    # Usage tracking
    requests_count = Column(Integer, default=0, nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Session metadata
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
