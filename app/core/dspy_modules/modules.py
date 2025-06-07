"""
DSPy modules for document-aware fact-checking.

This module contains the main DSPy modules that implement the document-aware
fact-checking pipeline using the defined signatures.
"""

import dspy
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .signatures import DocumentClaimExtraction, DocumentClaimVerification, DocumentFactSynthesis
from .data_models import (
    DocumentClaim, Evidence, ClaimVerificationResult, DocumentFactCheckResult,
    ProcessingOptions, UncertaintyMetrics, DocumentType, VerificationResult
)

logger = logging.getLogger(__name__)


class UncertaintyEstimator:
    """Estimates uncertainty in fact-checking results."""
    
    def __init__(self):
        """Initialize the uncertainty estimator."""
        self.logger = logging.getLogger(__name__ + ".UncertaintyEstimator")
    
    def estimate(
        self,
        claim: DocumentClaim,
        verification: Any,
        document_metadata: Dict[str, Any]
    ) -> UncertaintyMetrics:
        """
        Estimate uncertainty metrics for a claim verification result.
        
        Args:
            claim: The claim being verified
            verification: Verification result
            document_metadata: Document metadata
            
        Returns:
            UncertaintyMetrics with detailed uncertainty analysis
        """
        try:
            # Extract verification details
            confidence = getattr(verification, 'confidence_score', 0.5)
            evidence_count = len(getattr(verification, 'evidence_summary', []))
            uncertainty_factors = getattr(verification, 'uncertainty_factors', [])
            
            # Calculate epistemic uncertainty (model uncertainty)
            epistemic_uncertainty = max(0.0, 1.0 - confidence)
            
            # Calculate aleatoric uncertainty (data uncertainty)
            aleatoric_uncertainty = 0.3  # Base uncertainty
            if evidence_count < 2:
                aleatoric_uncertainty += 0.3
            if "conflicting evidence" in uncertainty_factors:
                aleatoric_uncertainty += 0.2
            aleatoric_uncertainty = min(1.0, aleatoric_uncertainty)
            
            # Calculate evidence quality uncertainty
            evidence_quality_uncertainty = 0.2  # Base uncertainty
            if "outdated sources" in uncertainty_factors:
                evidence_quality_uncertainty += 0.2
            if "biased sources" in uncertainty_factors:
                evidence_quality_uncertainty += 0.2
            evidence_quality_uncertainty = min(1.0, evidence_quality_uncertainty)
            
            # Determine uncertainty flags
            conflicting_evidence = "conflicting evidence" in uncertainty_factors
            insufficient_evidence = evidence_count < 2 or "insufficient evidence" in uncertainty_factors
            outdated_evidence = "outdated sources" in uncertainty_factors
            biased_sources = "biased sources" in uncertainty_factors
            
            return UncertaintyMetrics(
                epistemic_uncertainty=epistemic_uncertainty,
                aleatoric_uncertainty=aleatoric_uncertainty,
                evidence_quality_uncertainty=evidence_quality_uncertainty,
                conflicting_evidence=conflicting_evidence,
                insufficient_evidence=insufficient_evidence,
                outdated_evidence=outdated_evidence,
                biased_sources=biased_sources,
                uncertainty_sources=uncertainty_factors,
                confidence_interval={
                    "lower": max(0.0, confidence - epistemic_uncertainty),
                    "upper": min(1.0, confidence + epistemic_uncertainty)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error estimating uncertainty: {e}")
            # Return default uncertainty metrics
            return UncertaintyMetrics(
                epistemic_uncertainty=0.5,
                aleatoric_uncertainty=0.5,
                evidence_quality_uncertainty=0.5,
                uncertainty_sources=["estimation_error"]
            )


class DocumentAwareFactChecker(dspy.Module):
    """Comprehensive document fact-checking with context awareness.
    
    This module orchestrates the complete fact-checking pipeline for documents,
    including claim extraction, verification, and synthesis with document-specific
    context preservation and specialized analysis.
    """
    
    def __init__(self, document_type: str = "general"):
        """
        Initialize the document-aware fact checker.
        
        Args:
            document_type: Type of document being processed (academic, news, legal, etc.)
        """
        super().__init__()
        
        self.document_type = document_type
        self.logger = logging.getLogger(__name__ + ".DocumentAwareFactChecker")
        
        # Initialize core DSPy modules
        self.claim_extractor = dspy.ChainOfThought(DocumentClaimExtraction)
        self.claim_verifier = dspy.ChainOfThought(DocumentClaimVerification)
        self.fact_synthesizer = dspy.ChainOfThought(DocumentFactSynthesis)
        
        # Initialize uncertainty estimator
        self.uncertainty_estimator = UncertaintyEstimator()
        
        # Initialize specialized modules (will be implemented in specialized.py)
        self.specialized_modules = {}
        
        self.logger.info(f"DocumentAwareFactChecker initialized for document type: {document_type}")
    
    def forward(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        processing_options: Optional[ProcessingOptions] = None
    ) -> DocumentFactCheckResult:
        """
        Execute comprehensive document fact-checking pipeline.
        
        Args:
            document_content: Full document content
            document_metadata: Document metadata and context
            processing_options: Processing configuration options
            
        Returns:
            DocumentFactCheckResult with complete analysis
        """
        start_time = time.time()
        
        if processing_options is None:
            processing_options = ProcessingOptions()
        
        try:
            self.logger.info(f"Starting fact-checking for document type: {self.document_type}")
            
            # Step 1: Extract claims with document context
            extraction_result = self._extract_claims(
                document_content, document_metadata, processing_options
            )
            
            # Step 2: Verify each claim with appropriate standards
            verification_results = self._verify_claims(
                extraction_result.extracted_claims,
                document_content,
                document_metadata,
                processing_options
            )
            
            # Step 3: Perform document-specific specialized analysis
            specialized_analysis = self._perform_specialized_analysis(
                document_content, document_metadata, verification_results
            )
            
            # Step 4: Synthesize final results
            synthesis_result = self._synthesize_results(
                document_metadata, verification_results, document_content, processing_options
            )
            
            # Calculate summary statistics
            total_claims = len(verification_results)
            supported_claims = sum(1 for r in verification_results if r.verification_result == VerificationResult.SUPPORTED)
            refuted_claims = sum(1 for r in verification_results if r.verification_result == VerificationResult.REFUTED)
            insufficient_claims = sum(1 for r in verification_results if r.verification_result == VerificationResult.INSUFFICIENT_EVIDENCE)
            conflicting_claims = sum(1 for r in verification_results if r.verification_result == VerificationResult.CONFLICTING)
            
            # Calculate overall accuracy score
            if total_claims > 0:
                overall_accuracy = (supported_claims + 0.5 * insufficient_claims) / total_claims
            else:
                overall_accuracy = 0.0
            
            processing_time = time.time() - start_time
            
            result = DocumentFactCheckResult(
                document_metadata=document_metadata,
                document_type=DocumentType(processing_options.document_type),
                processing_options=processing_options,
                total_claims_extracted=len(extraction_result.extracted_claims),
                claims_processed=total_claims,
                extraction_confidence=extraction_result.extraction_confidence,
                verification_results=verification_results,
                overall_accuracy_score=overall_accuracy,
                supported_claims=supported_claims,
                refuted_claims=refuted_claims,
                insufficient_evidence_claims=insufficient_claims,
                conflicting_claims=conflicting_claims,
                key_findings=synthesis_result.key_findings,
                credibility_assessment=synthesis_result.credibility_assessment,
                recommendations=synthesis_result.recommendations,
                total_processing_time=processing_time,
                processing_metadata={
                    "document_type": self.document_type,
                    "specialized_analysis": specialized_analysis,
                    "extraction_notes": extraction_result.processing_notes
                }
            )
            
            self.logger.info(f"Fact-checking completed in {processing_time:.2f}s. "
                           f"Processed {total_claims} claims with {overall_accuracy:.2f} accuracy score")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in fact-checking pipeline: {e}")
            processing_time = time.time() - start_time
            
            # Return error result
            return DocumentFactCheckResult(
                document_metadata=document_metadata,
                document_type=DocumentType(processing_options.document_type),
                processing_options=processing_options,
                total_claims_extracted=0,
                claims_processed=0,
                extraction_confidence=0.0,
                verification_results=[],
                overall_accuracy_score=0.0,
                supported_claims=0,
                refuted_claims=0,
                insufficient_evidence_claims=0,
                conflicting_claims=0,
                total_processing_time=processing_time,
                processing_metadata={"error": str(e)}
            )
    
    def _extract_claims(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        processing_options: ProcessingOptions
    ) -> Any:
        """Extract claims from document content."""
        try:
            extraction_context = f"Document type: {self.document_type}"
            if processing_options.document_type != DocumentType.GENERAL:
                extraction_context += f", Domain: {processing_options.document_type.value}"
            
            result = self.claim_extractor(
                document_content=document_content,
                document_metadata=document_metadata,
                extraction_context=extraction_context,
                confidence_threshold=processing_options.confidence_threshold
            )
            
            self.logger.info(f"Extracted {len(result.extracted_claims)} claims")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in claim extraction: {e}")
            # Return empty result
            class EmptyResult:
                extracted_claims = []
                extraction_confidence = 0.0
                processing_notes = [f"Extraction failed: {str(e)}"]
            return EmptyResult()
    
    def _verify_claims(
        self,
        claims: List[DocumentClaim],
        document_content: str,
        document_metadata: Dict[str, Any],
        processing_options: ProcessingOptions
    ) -> List[ClaimVerificationResult]:
        """Verify extracted claims."""
        verification_results = []
        
        for claim in claims[:processing_options.max_claims_per_document]:
            try:
                start_time = time.time()
                
                # Determine verification standards based on document type
                verification_standards = self._get_verification_standards(claim, document_metadata)
                
                # Get evidence sources
                evidence_sources = self._get_evidence_sources(claim, processing_options)
                
                # Verify claim
                verification = self.claim_verifier(
                    claim=claim,
                    document_context=document_content,
                    evidence_sources=evidence_sources,
                    verification_standards=verification_standards
                )
                
                # Add uncertainty quantification
                uncertainty_metrics = self.uncertainty_estimator.estimate(
                    claim, verification, document_metadata
                )
                
                processing_time = time.time() - start_time
                
                verification_result = ClaimVerificationResult(
                    claim=claim,
                    verification_result=VerificationResult(verification.verification_result),
                    confidence_score=verification.confidence_score,
                    supporting_evidence=verification.evidence_summary,
                    refuting_evidence=[],  # Will be populated based on evidence analysis
                    verification_reasoning=f"Verified using {verification_standards}",
                    uncertainty_factors=verification.uncertainty_factors,
                    uncertainty_metrics=uncertainty_metrics,
                    verification_method="dspy_chain_of_thought",
                    processing_time=processing_time
                )
                
                verification_results.append(verification_result)
                
            except Exception as e:
                self.logger.error(f"Error verifying claim {claim.claim_id}: {e}")
                # Add error result
                verification_results.append(
                    ClaimVerificationResult(
                        claim=claim,
                        verification_result=VerificationResult.INSUFFICIENT_EVIDENCE,
                        confidence_score=0.0,
                        verification_reasoning=f"Verification failed: {str(e)}",
                        verification_method="error",
                        processing_time=0.0
                    )
                )
        
        return verification_results
    
    def _perform_specialized_analysis(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        verification_results: List[ClaimVerificationResult]
    ) -> Dict[str, Any]:
        """Perform document-type specific analysis."""
        # Placeholder for specialized analysis
        # Will be implemented with specialized modules
        return {
            "document_type": self.document_type,
            "specialized_modules_used": list(self.specialized_modules.keys()),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _synthesize_results(
        self,
        document_metadata: Dict[str, Any],
        verification_results: List[ClaimVerificationResult],
        document_content: str,
        processing_options: ProcessingOptions
    ) -> Any:
        """Synthesize final fact-checking results."""
        try:
            # Convert verification results to serializable format
            claim_results = [
                {
                    "claim_id": result.claim.claim_id,
                    "claim_text": result.claim.text,
                    "verification_result": result.verification_result.value,
                    "confidence_score": result.confidence_score,
                    "evidence_count": len(result.supporting_evidence),
                    "uncertainty_factors": result.uncertainty_factors
                }
                for result in verification_results
            ]
            
            synthesis_requirements = f"Document type: {self.document_type}, " \
                                   f"Verification depth: {processing_options.verification_depth}"
            
            result = self.fact_synthesizer(
                document_metadata=document_metadata,
                claim_results=claim_results,
                document_context=document_content,
                synthesis_requirements=synthesis_requirements
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in synthesis: {e}")
            # Return default result
            class DefaultSynthesis:
                overall_verdict = "INSUFFICIENT_INFO"
                accuracy_score = 0.0
                key_findings = [f"Synthesis failed: {str(e)}"]
                credibility_assessment = {"error": str(e)}
                recommendations = ["Manual review required due to processing error"]
            return DefaultSynthesis()
    
    def _get_verification_standards(self, claim: DocumentClaim, document_metadata: Dict[str, Any]) -> str:
        """Get verification standards based on document type and claim characteristics."""
        base_standards = "Standard fact-checking with multiple source verification"
        
        if self.document_type == "academic":
            return f"{base_standards}. Require peer-reviewed sources and methodological rigor."
        elif self.document_type == "news":
            return f"{base_standards}. Prioritize recent, credible news sources and official statements."
        elif self.document_type == "legal":
            return f"{base_standards}. Require legal precedents, statutes, and authoritative legal sources."
        else:
            return base_standards
    
    def _get_evidence_sources(self, claim: DocumentClaim, processing_options: ProcessingOptions) -> List[str]:
        """Get appropriate evidence sources for claim verification."""
        default_sources = [
            "academic_databases", "news_archives", "government_data",
            "expert_sources", "fact_checking_sites"
        ]
        
        if processing_options.evidence_sources:
            return processing_options.evidence_sources
        
        return default_sources
