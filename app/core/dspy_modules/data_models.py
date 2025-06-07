"""
Data models for DSPy-based document fact-checking.

This module contains Pydantic models that define the data structures
used throughout the document-aware fact-checking pipeline.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator


class ClaimType(str, Enum):
    """Types of claims that can be extracted from documents."""
    FACTUAL = "factual"
    STATISTICAL = "statistical"
    CAUSAL = "causal"
    COMPARATIVE = "comparative"
    TEMPORAL = "temporal"
    DEFINITIONAL = "definitional"
    OPINION = "opinion"
    PREDICTION = "prediction"


class VerificationResult(str, Enum):
    """Possible results of claim verification."""
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING = "CONFLICTING"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"


class DocumentType(str, Enum):
    """Types of documents that can be processed."""
    ACADEMIC = "academic"
    NEWS = "news"
    LEGAL = "legal"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    GENERAL = "general"


class EvidenceType(str, Enum):
    """Types of evidence that can support or refute claims."""
    ACADEMIC_PAPER = "academic_paper"
    NEWS_ARTICLE = "news_article"
    GOVERNMENT_DATA = "government_data"
    EXPERT_STATEMENT = "expert_statement"
    STATISTICAL_DATA = "statistical_data"
    HISTORICAL_RECORD = "historical_record"
    LEGAL_DOCUMENT = "legal_document"
    CORPORATE_REPORT = "corporate_report"


class DocumentClaim(BaseModel):
    """A claim extracted from a document with context preservation."""
    
    claim_id: str = Field(..., description="Unique identifier for the claim")
    text: str = Field(..., description="The actual claim text")
    claim_type: ClaimType = Field(..., description="Type of claim")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in claim extraction")
    
    # Document context
    document_section: Optional[str] = Field(None, description="Section where claim was found")
    page_number: Optional[int] = Field(None, description="Page number in document")
    paragraph_index: Optional[int] = Field(None, description="Paragraph index in document")
    surrounding_context: str = Field(..., description="Text surrounding the claim")
    
    # Claim characteristics
    is_atomic: bool = Field(True, description="Whether claim is atomic (single verifiable fact)")
    is_verifiable: bool = Field(True, description="Whether claim can be fact-checked")
    requires_expertise: bool = Field(False, description="Whether claim requires domain expertise")
    temporal_scope: Optional[str] = Field(None, description="Time period the claim refers to")
    
    # Metadata
    extraction_method: str = Field(..., description="Method used to extract the claim")
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class Evidence(BaseModel):
    """Evidence supporting or refuting a claim."""
    
    evidence_id: str = Field(..., description="Unique identifier for the evidence")
    text: str = Field(..., description="Evidence text or description")
    source: str = Field(..., description="Source of the evidence")
    source_url: Optional[str] = Field(None, description="URL of the evidence source")
    evidence_type: EvidenceType = Field(..., description="Type of evidence")
    
    # Evidence quality metrics
    credibility_score: float = Field(..., ge=0.0, le=1.0, description="Credibility of the source")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance to the claim")
    recency_score: float = Field(..., ge=0.0, le=1.0, description="How recent the evidence is")
    
    # Evidence metadata
    publication_date: Optional[datetime] = Field(None, description="When evidence was published")
    author: Optional[str] = Field(None, description="Author of the evidence")
    methodology: Optional[str] = Field(None, description="Methodology used (for studies)")
    
    # Verification details
    supports_claim: bool = Field(..., description="Whether evidence supports the claim")
    strength: float = Field(..., ge=0.0, le=1.0, description="Strength of evidence")
    
    @validator('credibility_score', 'relevance_score', 'recency_score', 'strength')
    def validate_scores(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Score must be between 0.0 and 1.0')
        return v


class UncertaintyMetrics(BaseModel):
    """Metrics quantifying uncertainty in verification results."""
    
    epistemic_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Model uncertainty")
    aleatoric_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Data uncertainty")
    evidence_quality_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Evidence quality uncertainty")
    
    # Uncertainty factors
    conflicting_evidence: bool = Field(False, description="Whether evidence conflicts")
    insufficient_evidence: bool = Field(False, description="Whether evidence is insufficient")
    outdated_evidence: bool = Field(False, description="Whether evidence is outdated")
    biased_sources: bool = Field(False, description="Whether sources may be biased")
    
    # Uncertainty sources
    uncertainty_sources: List[str] = Field(default_factory=list, description="Sources of uncertainty")
    confidence_interval: Optional[Dict[str, float]] = Field(None, description="Confidence interval for scores")
    
    @validator('epistemic_uncertainty', 'aleatoric_uncertainty', 'evidence_quality_uncertainty')
    def validate_uncertainty(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Uncertainty must be between 0.0 and 1.0')
        return v


class ClaimVerificationResult(BaseModel):
    """Result of verifying a single claim."""
    
    claim: DocumentClaim = Field(..., description="The claim that was verified")
    verification_result: VerificationResult = Field(..., description="Verification outcome")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in verification")
    
    # Evidence
    supporting_evidence: List[Evidence] = Field(default_factory=list, description="Evidence supporting the claim")
    refuting_evidence: List[Evidence] = Field(default_factory=list, description="Evidence refuting the claim")
    
    # Analysis
    verification_reasoning: str = Field(..., description="Reasoning behind the verification")
    uncertainty_factors: List[str] = Field(default_factory=list, description="Factors contributing to uncertainty")
    uncertainty_metrics: Optional[UncertaintyMetrics] = Field(None, description="Detailed uncertainty metrics")
    
    # Metadata
    verification_method: str = Field(..., description="Method used for verification")
    verification_timestamp: datetime = Field(default_factory=datetime.now)
    processing_time: float = Field(..., description="Time taken for verification in seconds")
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class ProcessingOptions(BaseModel):
    """Options for configuring the fact-checking process."""
    
    # General options
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")
    max_claims_per_document: int = Field(default=50, ge=1, description="Maximum claims to extract")
    enable_uncertainty_quantification: bool = Field(default=True, description="Enable uncertainty analysis")
    
    # Document-specific options
    document_type: DocumentType = Field(default=DocumentType.GENERAL, description="Type of document being processed")
    preserve_context: bool = Field(default=True, description="Preserve document context in claims")
    extract_citations: bool = Field(default=True, description="Extract and verify citations")
    
    # Verification options
    evidence_sources: List[str] = Field(default_factory=list, description="Preferred evidence sources")
    verification_depth: str = Field(default="standard", description="Depth of verification (quick, standard, thorough)")
    require_multiple_sources: bool = Field(default=True, description="Require multiple evidence sources")
    
    # Performance options
    timeout_seconds: float = Field(default=300.0, description="Maximum processing time")
    parallel_processing: bool = Field(default=True, description="Enable parallel claim processing")
    cache_results: bool = Field(default=True, description="Cache verification results")


class DocumentFactCheckResult(BaseModel):
    """Complete fact-checking result for a document."""
    
    # Document information
    document_metadata: Dict[str, Any] = Field(..., description="Document metadata")
    document_type: DocumentType = Field(..., description="Type of document")
    processing_options: ProcessingOptions = Field(..., description="Options used for processing")
    
    # Extraction results
    total_claims_extracted: int = Field(..., description="Total number of claims extracted")
    claims_processed: int = Field(..., description="Number of claims actually processed")
    extraction_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall extraction confidence")
    
    # Verification results
    verification_results: List[ClaimVerificationResult] = Field(..., description="Individual claim results")
    overall_accuracy_score: float = Field(..., ge=0.0, le=1.0, description="Overall document accuracy")
    
    # Summary statistics
    supported_claims: int = Field(..., description="Number of supported claims")
    refuted_claims: int = Field(..., description="Number of refuted claims")
    insufficient_evidence_claims: int = Field(..., description="Claims with insufficient evidence")
    conflicting_claims: int = Field(..., description="Claims with conflicting evidence")
    
    # Analysis
    key_findings: List[str] = Field(default_factory=list, description="Key findings from fact-checking")
    credibility_assessment: Dict[str, Any] = Field(default_factory=dict, description="Document credibility assessment")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for readers")
    
    # Metadata
    processing_timestamp: datetime = Field(default_factory=datetime.now)
    total_processing_time: float = Field(..., description="Total processing time in seconds")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional processing metadata")
    
    @validator('extraction_confidence', 'overall_accuracy_score')
    def validate_scores(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Score must be between 0.0 and 1.0')
        return v
