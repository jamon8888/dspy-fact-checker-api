"""
DSPy Fact-Checking Service

Service layer for document-aware fact-checking using DSPy modules.
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from app.core.dspy_modules import (
    DocumentAwareFactChecker, ProcessingOptions, DocumentFactCheckResult,
    DocumentType, DATA_MODELS_AVAILABLE, MODULES_AVAILABLE
)

logger = logging.getLogger(__name__)


class DSPyFactCheckingService:
    """Service for document-aware fact-checking using DSPy modules."""
    
    def __init__(self):
        """Initialize the DSPy fact-checking service."""
        self.fact_checkers = {}
        self.initialized = False
        logger.info("DSPyFactCheckingService initialized")
    
    async def initialize(self):
        """Initialize DSPy modules and fact checkers."""
        try:
            if not DATA_MODELS_AVAILABLE or not MODULES_AVAILABLE:
                logger.warning("DSPy modules not fully available - some features may be limited")
                return False
            
            # Initialize fact checkers for different document types
            document_types = ["general", "academic", "news", "legal", "medical", "financial", "technical"]
            
            for doc_type in document_types:
                try:
                    self.fact_checkers[doc_type] = DocumentAwareFactChecker(document_type=doc_type)
                    logger.info(f"Initialized fact checker for document type: {doc_type}")
                except Exception as e:
                    logger.error(f"Failed to initialize fact checker for {doc_type}: {e}")
            
            self.initialized = True
            logger.info(f"DSPy fact-checking service initialized with {len(self.fact_checkers)} fact checkers")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize DSPy fact-checking service: {e}")
            return False
    
    async def fact_check_document(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        document_type: str = "general",
        confidence_threshold: float = 0.5,
        max_claims_per_document: int = 50,
        enable_uncertainty_quantification: bool = True,
        preserve_context: bool = True,
        extract_citations: bool = True,
        evidence_sources: Optional[List[str]] = None,
        verification_depth: str = "standard",
        require_multiple_sources: bool = True,
        timeout_seconds: float = 300.0,
        parallel_processing: bool = True,
        cache_results: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform comprehensive fact-checking on a document.
        
        Args:
            document_content: Full document content
            document_metadata: Document metadata and context
            document_type: Type of document (general, academic, news, legal, etc.)
            confidence_threshold: Minimum confidence threshold for claims
            max_claims_per_document: Maximum number of claims to process
            enable_uncertainty_quantification: Enable uncertainty analysis
            preserve_context: Preserve document context in claims
            extract_citations: Extract and verify citations
            evidence_sources: Preferred evidence sources
            verification_depth: Depth of verification (quick, standard, thorough)
            require_multiple_sources: Require multiple evidence sources
            timeout_seconds: Maximum processing time
            parallel_processing: Enable parallel claim processing
            cache_results: Cache verification results
            **kwargs: Additional options
            
        Returns:
            Dictionary with comprehensive fact-checking results
        """
        processing_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Initialize if not already done
            if not self.initialized:
                await self.initialize()
            
            if not self.initialized:
                raise Exception("DSPy fact-checking service not properly initialized")
            
            # Validate document type
            if document_type not in self.fact_checkers:
                logger.warning(f"Unknown document type '{document_type}', using 'general'")
                document_type = "general"
            
            # Create processing options
            processing_options = ProcessingOptions(
                confidence_threshold=confidence_threshold,
                max_claims_per_document=max_claims_per_document,
                enable_uncertainty_quantification=enable_uncertainty_quantification,
                document_type=DocumentType(document_type),
                preserve_context=preserve_context,
                extract_citations=extract_citations,
                evidence_sources=evidence_sources or [],
                verification_depth=verification_depth,
                require_multiple_sources=require_multiple_sources,
                timeout_seconds=timeout_seconds,
                parallel_processing=parallel_processing,
                cache_results=cache_results
            )
            
            # Get appropriate fact checker
            fact_checker = self.fact_checkers[document_type]
            
            # Perform fact-checking
            result = await asyncio.wait_for(
                self._run_fact_checking(fact_checker, document_content, document_metadata, processing_options),
                timeout=timeout_seconds
            )
            
            # Convert to API response format
            response = self._convert_to_api_response(result, processing_id, start_time)
            
            logger.info(f"Fact-checking completed successfully for {processing_id}")
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Fact-checking timed out for {processing_id}")
            return self._create_error_response(
                processing_id, "timeout_error", 
                f"Fact-checking timed out after {timeout_seconds}s", start_time
            )
        except Exception as e:
            logger.error(f"Fact-checking failed for {processing_id}: {e}")
            return self._create_error_response(
                processing_id, "processing_error", str(e), start_time
            )
    
    async def _run_fact_checking(
        self,
        fact_checker: DocumentAwareFactChecker,
        document_content: str,
        document_metadata: Dict[str, Any],
        processing_options: ProcessingOptions
    ) -> DocumentFactCheckResult:
        """Run the fact-checking process."""
        try:
            # Execute fact-checking pipeline
            result = fact_checker.forward(
                document_content=document_content,
                document_metadata=document_metadata,
                processing_options=processing_options
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in fact-checking execution: {e}")
            raise
    
    async def extract_claims_only(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        document_type: str = "general",
        confidence_threshold: float = 0.5,
        max_claims: int = 50,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract claims from document without full verification.
        
        Args:
            document_content: Document content
            document_metadata: Document metadata
            document_type: Type of document
            confidence_threshold: Minimum confidence for extraction
            max_claims: Maximum number of claims to extract
            **kwargs: Additional options
            
        Returns:
            Dictionary with extracted claims
        """
        processing_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Initialize if not already done
            if not self.initialized:
                await self.initialize()
            
            if not self.initialized:
                raise Exception("DSPy fact-checking service not properly initialized")
            
            # Validate document type
            if document_type not in self.fact_checkers:
                document_type = "general"
            
            fact_checker = self.fact_checkers[document_type]
            
            # Extract claims using the claim extractor
            extraction_result = fact_checker._extract_claims(
                document_content,
                document_metadata,
                ProcessingOptions(
                    confidence_threshold=confidence_threshold,
                    max_claims_per_document=max_claims,
                    document_type=DocumentType(document_type)
                )
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "processing_id": processing_id,
                "document_type": document_type,
                "processing_time": processing_time,
                "extracted_claims": [claim.dict() for claim in extraction_result.extracted_claims],
                "extraction_confidence": extraction_result.extraction_confidence,
                "processing_notes": extraction_result.processing_notes,
                "total_claims": len(extraction_result.extracted_claims)
            }
            
        except Exception as e:
            logger.error(f"Claim extraction failed for {processing_id}: {e}")
            return self._create_error_response(
                processing_id, "extraction_error", str(e), start_time
            )
    
    async def verify_single_claim(
        self,
        claim_text: str,
        document_context: str,
        document_metadata: Dict[str, Any],
        document_type: str = "general",
        evidence_sources: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Verify a single claim with document context.
        
        Args:
            claim_text: Text of the claim to verify
            document_context: Document context for the claim
            document_metadata: Document metadata
            document_type: Type of document
            evidence_sources: Evidence sources to use
            **kwargs: Additional options
            
        Returns:
            Dictionary with verification result
        """
        processing_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Initialize if not already done
            if not self.initialized:
                await self.initialize()
            
            if not self.initialized:
                raise Exception("DSPy fact-checking service not properly initialized")
            
            # Create a DocumentClaim object
            from app.core.dspy_modules import DocumentClaim, ClaimType
            
            claim = DocumentClaim(
                claim_id=processing_id,
                text=claim_text,
                claim_type=ClaimType.FACTUAL,
                confidence=1.0,
                surrounding_context=document_context,
                extraction_method="manual"
            )
            
            # Validate document type
            if document_type not in self.fact_checkers:
                document_type = "general"
            
            fact_checker = self.fact_checkers[document_type]
            
            # Verify the claim
            verification_results = fact_checker._verify_claims(
                [claim],
                document_context,
                document_metadata,
                ProcessingOptions(
                    document_type=DocumentType(document_type),
                    evidence_sources=evidence_sources or []
                )
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if verification_results:
                result = verification_results[0]
                return {
                    "success": True,
                    "processing_id": processing_id,
                    "document_type": document_type,
                    "processing_time": processing_time,
                    "claim": result.claim.dict(),
                    "verification_result": result.verification_result.value,
                    "confidence_score": result.confidence_score,
                    "supporting_evidence": [evidence.dict() for evidence in result.supporting_evidence],
                    "refuting_evidence": [evidence.dict() for evidence in result.refuting_evidence],
                    "verification_reasoning": result.verification_reasoning,
                    "uncertainty_factors": result.uncertainty_factors,
                    "uncertainty_metrics": result.uncertainty_metrics.dict() if result.uncertainty_metrics else None
                }
            else:
                raise Exception("No verification result returned")
            
        except Exception as e:
            logger.error(f"Single claim verification failed for {processing_id}: {e}")
            return self._create_error_response(
                processing_id, "verification_error", str(e), start_time
            )
    
    async def get_service_capabilities(self) -> Dict[str, Any]:
        """Get information about service capabilities."""
        try:
            # Initialize if not already done
            if not self.initialized:
                await self.initialize()
            
            return {
                "success": True,
                "service_info": {
                    "name": "DSPy Fact-Checking Service",
                    "version": "1.0.0",
                    "description": "Document-aware fact-checking using DSPy modules"
                },
                "capabilities": {
                    "document_types": list(self.fact_checkers.keys()),
                    "verification_depths": ["quick", "standard", "thorough"],
                    "specialized_modules": [
                        "AcademicCitationVerifier", "MethodologyAnalyzer",
                        "NewsSourceCredibilityAnalyzer", "NewsBiasDetector",
                        "LegalPrecedentChecker", "StatuteVerifier"
                    ],
                    "features": {
                        "claim_extraction": True,
                        "claim_verification": True,
                        "uncertainty_quantification": True,
                        "context_preservation": True,
                        "citation_verification": True,
                        "specialized_analysis": True,
                        "parallel_processing": True,
                        "caching": True
                    }
                },
                "availability": {
                    "data_models": DATA_MODELS_AVAILABLE,
                    "modules": MODULES_AVAILABLE,
                    "initialized": self.initialized,
                    "fact_checkers": len(self.fact_checkers)
                },
                "limits": {
                    "max_claims_per_document": 100,
                    "max_timeout": "600s",
                    "supported_document_types": list(self.fact_checkers.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get service capabilities: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "capability_error"
            }
    
    def _convert_to_api_response(
        self, 
        result: DocumentFactCheckResult, 
        processing_id: str, 
        start_time: datetime
    ) -> Dict[str, Any]:
        """Convert DocumentFactCheckResult to API response format."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "processing_id": processing_id,
            "document_type": result.document_type.value,
            "processing_time": processing_time,
            "processed_at": result.processing_timestamp.isoformat(),
            "extraction_results": {
                "total_claims_extracted": result.total_claims_extracted,
                "claims_processed": result.claims_processed,
                "extraction_confidence": result.extraction_confidence
            },
            "verification_results": {
                "overall_accuracy_score": result.overall_accuracy_score,
                "supported_claims": result.supported_claims,
                "refuted_claims": result.refuted_claims,
                "insufficient_evidence_claims": result.insufficient_evidence_claims,
                "conflicting_claims": result.conflicting_claims
            },
            "individual_claims": [
                {
                    "claim_id": vr.claim.claim_id,
                    "claim_text": vr.claim.text,
                    "claim_type": vr.claim.claim_type.value,
                    "verification_result": vr.verification_result.value,
                    "confidence_score": vr.confidence_score,
                    "evidence_count": len(vr.supporting_evidence),
                    "uncertainty_factors": vr.uncertainty_factors,
                    "processing_time": vr.processing_time
                }
                for vr in result.verification_results
            ],
            "analysis": {
                "key_findings": result.key_findings,
                "credibility_assessment": result.credibility_assessment,
                "recommendations": result.recommendations
            },
            "processing_metadata": result.processing_metadata,
            "processing_options": result.processing_options.dict()
        }
    
    def _create_error_response(
        self, 
        processing_id: str, 
        error_type: str, 
        error_message: str, 
        start_time: datetime
    ) -> Dict[str, Any]:
        """Create standardized error response."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": False,
            "processing_id": processing_id,
            "error": error_message,
            "error_type": error_type,
            "processing_time": processing_time,
            "processed_at": datetime.now().isoformat()
        }
