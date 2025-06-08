"""
Text processing endpoints for the DSPy-Enhanced Fact-Checker API Platform.
Enhanced with unified search capabilities including Exa.ai and hallucination detection.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import uuid
import logging
import time

from app.core.config import get_settings, Settings
from app.services.unified_search_service import unified_search_service, SearchProvider, SearchMode

router = APIRouter()
logger = logging.getLogger(__name__)


class TextProcessingRequest(BaseModel):
    """Request model for text processing with enhanced search capabilities."""

    text: str = Field(..., min_length=1, max_length=50000, description="Text content to fact-check")
    context: Optional[str] = Field(None, description="Additional context for fact-checking")
    optimization_level: str = Field("standard", pattern="^(fast|standard|thorough)$")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)

    # Enhanced search options
    search_provider: str = Field("auto", description="Search provider: auto, exa, tavily, dual")
    include_hallucination_check: bool = Field(True, description="Include hallucination detection")
    max_results_per_claim: int = Field(5, ge=1, le=20, description="Max search results per claim")
    search_mode: str = Field("fact_check", description="Search mode: fact_check, research, general")


class ClaimResult(BaseModel):
    """Result model for individual claim verification with enhanced analysis."""

    claim: str
    verdict: str  # True, False, Partially True, Unverifiable, False - Likely Hallucination
    confidence: float
    evidence: List[str]
    sources: List[str]

    # Enhanced fields
    search_provider_used: str
    hallucination_analysis: Optional[Dict[str, Any]] = None
    processing_time: float
    evidence_quality_score: float


class TextProcessingResponse(BaseModel):
    """Response model for text processing."""
    
    request_id: str
    status: str
    claims: List[ClaimResult]
    overall_verdict: str
    confidence_score: float
    processing_time: float
    word_count: int
    claims_analyzed: int


@router.post("/process", response_model=TextProcessingResponse)
async def process_text(
    request: TextProcessingRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
) -> TextProcessingResponse:
    """
    Process direct text input for comprehensive fact-checking using unified search.

    Enhanced with Exa.ai neural search, hallucination detection, and multi-provider support.
    Optimized for immediate processing of shorter texts.
    """

    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Log the request
    logger.info(f"Processing enhanced text request: {request_id}")
    logger.debug(f"Text length: {len(request.text)} characters, provider: {request.search_provider}")

    try:
        # Initialize unified search service
        if not unified_search_service.initialized:
            await unified_search_service.initialize()

        # Extract claims from text (simple implementation)
        claims = await _extract_claims_from_text(request.text)

        # Process each claim with unified search
        processed_claims = []
        total_confidence = 0.0

        for claim in claims:
            claim_result = await _process_single_claim(claim, request)
            processed_claims.append(claim_result)
            total_confidence += claim_result.confidence

        # Calculate overall metrics
        overall_confidence = total_confidence / len(processed_claims) if processed_claims else 0.0
        overall_verdict = _determine_overall_verdict(processed_claims, overall_confidence)
        processing_time = time.time() - start_time

        logger.info(f"Enhanced text processing completed: {request_id}, {len(processed_claims)} claims, {processing_time:.2f}s")

        return TextProcessingResponse(
            request_id=request_id,
            status="completed",
            claims=processed_claims,
            overall_verdict=overall_verdict,
            confidence_score=overall_confidence,
            processing_time=processing_time,
            word_count=len(request.text.split()),
            claims_analyzed=len(processed_claims)
        )

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Enhanced text processing failed: {request_id}, error: {e}")

        # Return error response
        return TextProcessingResponse(
            request_id=request_id,
            status="error",
            claims=[],
            overall_verdict="error",
            confidence_score=0.0,
            processing_time=processing_time,
            word_count=len(request.text.split()),
            claims_analyzed=0
        )


@router.get("/status/{request_id}")
async def get_text_processing_status(request_id: str) -> Dict[str, Any]:
    """Get the processing status of a text fact-checking request."""
    
    # TODO: Add actual status checking logic
    logger.info(f"Checking text processing status: {request_id}")
    
    return {
        "request_id": request_id,
        "status": "completed",
        "progress": 100,
        "estimated_completion_time": None,
        "message": "Text processing completed successfully"
    }


@router.get("/results/{request_id}")
async def get_text_processing_results(request_id: str) -> TextProcessingResponse:
    """Get the fact-checking results for a processed text."""
    
    # TODO: Add actual results retrieval logic
    logger.info(f"Retrieving text processing results: {request_id}")
    
    # Mock response for now
    mock_claims = [
        ClaimResult(
            claim="Sample claim from processed text",
            verdict="SUPPORTED",
            confidence=0.90,
            evidence=["Evidence A", "Evidence B"],
            sources=["Source A", "Source B"]
        ),
        ClaimResult(
            claim="Another claim from the text",
            verdict="REFUTED",
            confidence=0.75,
            evidence=["Contradicting evidence"],
            sources=["Fact-checking source"]
        )
    ]
    
    return TextProcessingResponse(
        request_id=request_id,
        status="completed",
        claims=mock_claims,
        overall_verdict="mixed",
        confidence_score=0.82,
        processing_time=3.2,
        word_count=150,
        claims_analyzed=len(mock_claims)
    )


@router.post("/batch-process")
async def batch_process_texts(
    texts: List[TextProcessingRequest],
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Process multiple texts for fact-checking in batch.
    
    Maximum 20 texts per batch.
    """
    
    if len(texts) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 texts allowed per batch"
        )
    
    batch_id = str(uuid.uuid4())
    request_ids = []
    
    for i, text_request in enumerate(texts):
        request_id = str(uuid.uuid4())
        request_ids.append({
            "request_id": request_id,
            "text_length": len(text_request.text),
            "optimization_level": text_request.optimization_level
        })
        
        # TODO: Add actual batch processing logic
        logger.info(f"Added text {i+1} to batch: {request_id}")
    
    return {
        "batch_id": batch_id,
        "texts_accepted": len(request_ids),
        "request_ids": request_ids,
        "status": "processing",
        "estimated_completion_time": len(texts) * 2,  # Rough estimate
        "message": "Batch text processing started successfully"
    }


# Helper functions for enhanced text processing

async def _extract_claims_from_text(text: str) -> List[str]:
    """Extract factual claims from text for verification."""
    # Simple implementation - split by sentences and filter
    # In production, would use NLP models for better claim extraction

    import re

    # Split into sentences
    sentences = re.split(r'[.!?]+', text)

    # Filter for sentences that look like factual claims
    claims = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10 and not sentence.startswith(('I think', 'I believe', 'Maybe', 'Perhaps')):
            # Simple heuristics for factual claims
            if any(word in sentence.lower() for word in ['is', 'are', 'was', 'were', 'has', 'have', 'will', 'can', 'does']):
                claims.append(sentence)

    # Limit to top 5 claims for performance
    return claims[:5]


async def _process_single_claim(claim: str, request: TextProcessingRequest) -> ClaimResult:
    """Process a single claim using unified search service."""

    try:
        # Map request parameters to search service
        provider_mapping = {
            "auto": SearchProvider.AUTO,
            "exa": SearchProvider.EXA,
            "tavily": SearchProvider.TAVILY,
            "dual": SearchProvider.DUAL
        }

        mode_mapping = {
            "fact_check": SearchMode.FACT_CHECK,
            "research": SearchMode.RESEARCH,
            "general": SearchMode.GENERAL
        }

        search_provider = provider_mapping.get(request.search_provider, SearchProvider.AUTO)
        search_mode = mode_mapping.get(request.search_mode, SearchMode.FACT_CHECK)

        # Perform unified search
        result = await unified_search_service.search(
            query=claim,
            provider=search_provider,
            mode=search_mode,
            max_results=request.max_results_per_claim,
            include_hallucination_check=request.include_hallucination_check
        )

        if result["success"]:
            # Extract information from unified search result
            search_results = result["results"]
            hallucination_analysis = result.get("hallucination_analysis")

            # Build evidence and sources
            evidence = []
            sources = []

            if "evidence_summary" in search_results:
                evidence_summary = search_results["evidence_summary"]
                for source in evidence_summary.get("sources", []):
                    evidence.append(source["snippet"])
                    sources.append(source["url"])

            return ClaimResult(
                claim=claim,
                verdict=search_results.get("verdict", "Unverifiable"),
                confidence=search_results.get("confidence", 0.5),
                evidence=evidence[:3],  # Top 3 pieces of evidence
                sources=sources[:3],   # Top 3 sources
                search_provider_used=result["provider_used"],
                hallucination_analysis=hallucination_analysis,
                processing_time=result["processing_time"],
                evidence_quality_score=search_results.get("evidence_quality_score", 0.5)
            )

        else:
            # Handle search failure
            return ClaimResult(
                claim=claim,
                verdict="Error",
                confidence=0.0,
                evidence=[f"Search failed: {result.get('error', 'Unknown error')}"],
                sources=[],
                search_provider_used=request.search_provider,
                hallucination_analysis=None,
                processing_time=result.get("processing_time", 0.0),
                evidence_quality_score=0.0
            )

    except Exception as e:
        logger.error(f"Failed to process claim '{claim}': {e}")

        return ClaimResult(
            claim=claim,
            verdict="Error",
            confidence=0.0,
            evidence=[f"Processing error: {str(e)}"],
            sources=[],
            search_provider_used=request.search_provider,
            hallucination_analysis=None,
            processing_time=0.0,
            evidence_quality_score=0.0
        )


def _determine_overall_verdict(claims: List[ClaimResult], overall_confidence: float) -> str:
    """Determine overall verdict based on individual claim results."""

    if not claims:
        return "no_claims"

    # Count verdicts
    verdict_counts = {}
    for claim in claims:
        verdict = claim.verdict
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

    total_claims = len(claims)

    # Determine overall verdict
    if verdict_counts.get("True", 0) / total_claims >= 0.8:
        return "mostly_accurate"
    elif verdict_counts.get("False", 0) / total_claims >= 0.6:
        return "mostly_inaccurate"
    elif verdict_counts.get("False - Likely Hallucination", 0) > 0:
        return "contains_hallucinations"
    elif overall_confidence >= 0.7:
        return "mixed_reliable"
    elif overall_confidence >= 0.4:
        return "mixed_uncertain"
    else:
        return "unreliable"
