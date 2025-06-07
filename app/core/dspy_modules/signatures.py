"""
DSPy signatures for document-aware fact-checking.

This module contains DSPy signature definitions that specify the input/output
interfaces for document-aware fact-checking operations.
"""

import dspy
from typing import Dict, Any, List
from .data_models import DocumentClaim, Evidence, UncertaintyMetrics


class DocumentClaimExtraction(dspy.Signature):
    """Extract verifiable claims from document content with context preservation.
    
    This signature defines the interface for extracting atomic, verifiable claims
    from document content while preserving the document context and metadata.
    The extraction process should identify claims that can be fact-checked and
    maintain their relationship to the source document.
    """
    
    # Input fields
    document_content: str = dspy.InputField(
        desc="Full document content with structure preserved. Should include "
             "headings, paragraphs, and other structural elements that provide "
             "context for claim extraction."
    )
    
    document_metadata: Dict[str, Any] = dspy.InputField(
        desc="Document metadata including type (academic, news, legal, etc.), "
             "source, author, publication date, and other relevant information "
             "that affects claim extraction strategy."
    )
    
    extraction_context: str = dspy.InputField(
        desc="Document type and processing context that guides extraction. "
             "Includes information about the document domain, expected claim "
             "types, and any special extraction requirements."
    )
    
    confidence_threshold: float = dspy.InputField(
        desc="Minimum confidence required for claim extraction (0.0-1.0). "
             "Claims with confidence below this threshold should be filtered out "
             "to ensure quality of extracted claims."
    )
    
    # Output fields
    extracted_claims: List[DocumentClaim] = dspy.OutputField(
        desc="List of atomic, verifiable claims extracted from the document. "
             "Each claim should be a single factual statement that can be "
             "independently verified, with preserved document context including "
             "section, page number, and surrounding text."
    )
    
    document_summary: str = dspy.OutputField(
        desc="Brief summary of document content and main topics. Should capture "
             "the key themes, arguments, and factual areas covered in the document "
             "to provide context for the extracted claims."
    )
    
    extraction_confidence: float = dspy.OutputField(
        desc="Overall confidence in extraction quality (0.0-1.0). Reflects "
             "the system's confidence in having successfully identified and "
             "extracted the most important verifiable claims from the document."
    )
    
    processing_notes: List[str] = dspy.OutputField(
        desc="Notes about extraction challenges or limitations encountered "
             "during processing. May include warnings about document quality, "
             "ambiguous claims, or areas requiring manual review."
    )


class DocumentClaimVerification(dspy.Signature):
    """Verify claims with document-specific context and evidence standards.
    
    This signature defines the interface for verifying individual claims
    extracted from documents. The verification process should consider the
    document context, apply appropriate evidence standards based on document
    type, and provide comprehensive verification results with uncertainty
    quantification.
    """
    
    # Input fields
    claim: DocumentClaim = dspy.InputField(
        desc="Claim to verify with complete document context. Includes the "
             "claim text, type, confidence, document section, and surrounding "
             "context needed for accurate verification."
    )
    
    document_context: str = dspy.InputField(
        desc="Original document context and metadata that provides background "
             "for the claim. Includes document type, source credibility, "
             "publication context, and other factors affecting verification."
    )
    
    evidence_sources: List[str] = dspy.InputField(
        desc="Available evidence sources and databases to search for "
             "verification. May include academic databases, news archives, "
             "government data, expert sources, and domain-specific repositories."
    )
    
    verification_standards: str = dspy.InputField(
        desc="Verification standards based on document type and claim "
             "characteristics. Defines the level of evidence required, "
             "acceptable source types, and verification criteria."
    )
    
    # Output fields
    verification_result: str = dspy.OutputField(
        desc="Verification outcome: SUPPORTED (claim is backed by strong evidence), "
             "REFUTED (claim is contradicted by evidence), INSUFFICIENT_EVIDENCE "
             "(not enough evidence to verify), CONFLICTING (contradictory evidence), "
             "or PARTIALLY_SUPPORTED (some aspects supported, others not)."
    )
    
    evidence_summary: List[Evidence] = dspy.OutputField(
        desc="Supporting or refuting evidence with sources, credibility scores, "
             "and relevance assessments. Each piece of evidence should include "
             "source information, publication details, and quality metrics."
    )
    
    confidence_score: float = dspy.OutputField(
        desc="Confidence in verification result (0.0-1.0). Reflects the "
             "strength and quality of evidence, consistency of sources, "
             "and overall certainty in the verification outcome."
    )
    
    uncertainty_factors: List[str] = dspy.OutputField(
        desc="Factors contributing to uncertainty in verification. May include "
             "conflicting evidence, outdated sources, limited evidence availability, "
             "source bias, or methodological limitations in studies."
    )


class DocumentFactSynthesis(dspy.Signature):
    """Synthesize document-level fact-checking results with comprehensive analysis.
    
    This signature defines the interface for synthesizing individual claim
    verification results into a comprehensive document-level fact-checking
    report. The synthesis should consider document context, provide overall
    assessments, and generate actionable recommendations.
    """
    
    # Input fields
    document_metadata: Dict[str, Any] = dspy.InputField(
        desc="Complete document metadata and processing information including "
             "document type, source, author, publication date, processing "
             "options, and any specialized analysis results."
    )
    
    claim_results: List[Dict[str, Any]] = dspy.InputField(
        desc="Individual claim verification results with complete details "
             "including claims, verification outcomes, evidence, confidence "
             "scores, and uncertainty metrics for each processed claim."
    )
    
    document_context: str = dspy.InputField(
        desc="Document type, source, and contextual information that affects "
             "synthesis. Includes publication context, intended audience, "
             "document purpose, and domain-specific considerations."
    )
    
    synthesis_requirements: str = dspy.InputField(
        desc="Requirements for synthesis based on use case and audience. "
             "Defines the level of detail needed, specific focus areas, "
             "and format requirements for the final report."
    )
    
    # Output fields
    overall_verdict: str = dspy.OutputField(
        desc="Overall document assessment: MOSTLY_ACCURATE (majority of claims "
             "supported), MIXED (significant mix of supported/refuted claims), "
             "MOSTLY_INACCURATE (majority of claims refuted), or INSUFFICIENT_INFO "
             "(too many claims lack sufficient evidence for assessment)."
    )
    
    accuracy_score: float = dspy.OutputField(
        desc="Overall document accuracy score (0.0-1.0) based on the proportion "
             "of supported claims, strength of evidence, and confidence in "
             "verification results. Weighted by claim importance and confidence."
    )
    
    key_findings: List[str] = dspy.OutputField(
        desc="Key factual findings and their implications for document "
             "credibility. Should highlight the most significant verified "
             "or refuted claims and their impact on the document's reliability."
    )
    
    credibility_assessment: Dict[str, Any] = dspy.OutputField(
        desc="Assessment of document and source credibility including source "
             "reputation, methodology quality (for studies), bias indicators, "
             "citation quality, and overall trustworthiness metrics."
    )
    
    recommendations: List[str] = dspy.OutputField(
        desc="Recommendations for readers or further verification including "
             "areas requiring additional fact-checking, claims needing expert "
             "review, and guidance on interpreting the document's reliability."
    )
