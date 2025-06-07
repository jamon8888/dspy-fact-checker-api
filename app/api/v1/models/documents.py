"""
Document processing Pydantic models for the DSPy-Enhanced Fact-Checker API Platform.
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from .base import BaseResponse, ProcessingStatus, Priority, TimestampMixin


class DocumentType(str, Enum):
    """Supported document types."""
    
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"


class ProcessingMethod(str, Enum):
    """Document processing methods."""
    
    DOCLING = "docling"
    MISTRAL_OCR = "mistral_ocr"
    HYBRID = "hybrid"
    TEXT_EXTRACTION = "text_extraction"


class DocumentProcessingOptions(BaseModel):
    """Document processing configuration options."""
    
    perform_ocr: bool = Field(default=True, description="Use OCR for scanned documents")
    force_ocr: bool = Field(default=False, description="Force OCR even for text-based documents")
    preserve_formatting: bool = Field(default=True, description="Maintain document structure")
    extract_tables: bool = Field(default=True, description="Extract table data")
    extract_images: bool = Field(default=True, description="Extract image information")
    language_detection: bool = Field(default=True, description="Auto-detect document language")
    content_segmentation: str = Field(
        default="auto", 
        pattern="^(auto|semantic|paragraph|sentence)$",
        description="Content segmentation strategy"
    )
    confidence_threshold: float = Field(
        default=0.7, 
        ge=0.0, 
        le=1.0, 
        description="Minimum confidence threshold"
    )
    max_processing_time: int = Field(
        default=300, 
        ge=30, 
        le=1800, 
        description="Maximum processing time in seconds"
    )


class DocumentUploadRequest(BaseModel):
    """Document upload request model."""
    
    filename: str = Field(..., description="Original filename")
    content_type: Optional[str] = Field(None, description="MIME content type")
    processing_options: DocumentProcessingOptions = Field(
        default_factory=DocumentProcessingOptions,
        description="Processing configuration"
    )
    priority: Priority = Field(default=Priority.NORMAL, description="Processing priority")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook URL for completion notification")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename and extract extension."""
        if not v or '.' not in v:
            raise ValueError("Filename must include file extension")
        
        extension = v.split('.')[-1].lower()
        allowed_extensions = [doc_type.value for doc_type in DocumentType]
        
        if extension not in allowed_extensions:
            raise ValueError(f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}")
        
        return v


class DocumentUploadResponse(BaseResponse):
    """Document upload response model."""
    
    processing_id: str = Field(..., description="Unique processing identifier")
    filename: str = Field(..., description="Original filename")
    file_type: DocumentType = Field(..., description="Detected file type")
    file_size: int = Field(..., description="File size in bytes")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated completion time in seconds")
    estimated_cost: Optional[float] = Field(None, description="Estimated processing cost")
    queue_position: Optional[int] = Field(None, description="Position in processing queue")
    processing_options: DocumentProcessingOptions = Field(..., description="Applied processing options")


class DocumentMetadata(BaseModel):
    """Document metadata model."""
    
    title: Optional[str] = Field(None, description="Document title")
    author: Optional[str] = Field(None, description="Document author")
    creation_date: Optional[datetime] = Field(None, description="Document creation date")
    modification_date: Optional[datetime] = Field(None, description="Last modification date")
    page_count: Optional[int] = Field(None, description="Number of pages")
    word_count: Optional[int] = Field(None, description="Word count")
    language: Optional[str] = Field(None, description="Detected language")
    file_size: int = Field(..., description="File size in bytes")
    processing_method: ProcessingMethod = Field(..., description="Processing method used")
    extraction_confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence score")


class ExtractedContent(BaseModel):
    """Extracted content model."""
    
    text: str = Field(..., description="Extracted text content")
    structured_content: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Structured content elements"
    )
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted tables")
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted images")
    metadata: DocumentMetadata = Field(..., description="Document metadata")


class ClaimVerificationResult(BaseModel):
    """Individual claim verification result."""
    
    claim: str = Field(..., description="The factual claim")
    verdict: str = Field(
        ..., 
        pattern="^(SUPPORTED|REFUTED|INSUFFICIENT_EVIDENCE|CONFLICTING)$",
        description="Verification verdict"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in verification")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    sources: List[str] = Field(default_factory=list, description="Evidence sources")
    context: Optional[str] = Field(None, description="Claim context from document")
    location: Optional[Dict[str, Any]] = Field(None, description="Location in document")


class DocumentFactCheckResult(BaseModel):
    """Complete document fact-checking result."""
    
    processing_id: str = Field(..., description="Processing identifier")
    document_metadata: DocumentMetadata = Field(..., description="Document metadata")
    extracted_content: ExtractedContent = Field(..., description="Extracted content")
    claims: List[ClaimVerificationResult] = Field(..., description="Verified claims")
    overall_verdict: str = Field(
        ...,
        pattern="^(MOSTLY_ACCURATE|MIXED|MOSTLY_INACCURATE|INSUFFICIENT_INFO)$",
        description="Overall document verdict"
    )
    accuracy_score: float = Field(..., ge=0.0, le=1.0, description="Overall accuracy score")
    processing_stats: Dict[str, Any] = Field(..., description="Processing statistics")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for readers")


class DocumentProcessingStatus(BaseModel, TimestampMixin):
    """Document processing status model."""
    
    processing_id: str = Field(..., description="Processing identifier")
    status: ProcessingStatus = Field(..., description="Current processing status")
    progress: float = Field(..., ge=0.0, le=100.0, description="Processing progress percentage")
    current_stage: Optional[str] = Field(None, description="Current processing stage")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated completion time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    processing_time: Optional[float] = Field(None, description="Total processing time in seconds")


class BatchDocumentRequest(BaseModel):
    """Batch document processing request."""
    
    files: List[DocumentUploadRequest] = Field(
        ..., 
        min_items=1, 
        max_items=10, 
        description="List of documents to process"
    )
    batch_options: DocumentProcessingOptions = Field(
        default_factory=DocumentProcessingOptions,
        description="Batch processing options"
    )
    priority: Priority = Field(default=Priority.NORMAL, description="Batch processing priority")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook URL for batch completion")


class BatchDocumentResponse(BaseResponse):
    """Batch document processing response."""
    
    batch_id: str = Field(..., description="Unique batch identifier")
    files_accepted: int = Field(..., description="Number of files accepted for processing")
    files_rejected: int = Field(..., description="Number of files rejected")
    processing_ids: List[Dict[str, Any]] = Field(..., description="Individual processing IDs")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated batch completion time")
    estimated_total_cost: Optional[float] = Field(None, description="Estimated total processing cost")


class DocumentSearchRequest(BaseModel):
    """Document search request model."""
    
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    pagination: Optional[Dict[str, int]] = Field(None, description="Pagination parameters")
    sort_by: Optional[str] = Field("relevance", description="Sort criteria")
    include_content: bool = Field(False, description="Include document content in results")


class DocumentSearchResult(BaseModel):
    """Document search result model."""
    
    processing_id: str = Field(..., description="Processing identifier")
    filename: str = Field(..., description="Original filename")
    title: Optional[str] = Field(None, description="Document title")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Search relevance score")
    snippet: Optional[str] = Field(None, description="Content snippet")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    processing_date: datetime = Field(..., description="Processing date")


class DocumentSearchResponse(BaseResponse):
    """Document search response model."""
    
    query: str = Field(..., description="Original search query")
    results: List[DocumentSearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    search_time: float = Field(..., description="Search execution time in seconds")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
