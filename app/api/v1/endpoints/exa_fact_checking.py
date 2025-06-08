"""
API endpoints for Exa.ai-enhanced fact-checking with hallucination detection.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from app.services.exa_fact_checking_service import exa_fact_checking_service
from app.core.search.models import SearchType, EnhancedFactCheckResult, HallucinationResult
from app.core.search.exceptions import SearchProviderError, HallucinationDetectionError
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exa", tags=["Exa.ai Fact-Checking"])


# Request Models
class ExaFactCheckRequest(BaseModel):
    """Request model for Exa.ai fact-checking."""
    claim: str = Field(..., description="The claim to fact-check", min_length=1, max_length=5000)
    context: Optional[str] = Field(None, description="Optional context for the claim", max_length=2000)
    search_strategy: str = Field("intelligent", description="Search strategy", regex="^(parallel|sequential|intelligent)$")
    require_both_providers: bool = Field(False, description="Whether both search providers must succeed")
    enable_hallucination_detection: bool = Field(True, description="Whether to enable hallucination detection")


class HallucinationCheckRequest(BaseModel):
    """Request model for hallucination detection only."""
    claim: str = Field(..., description="The claim to analyze for hallucinations", min_length=1, max_length=5000)
    context: Optional[str] = Field(None, description="Optional context for the claim", max_length=2000)


class ExaSearchRequest(BaseModel):
    """Request model for Exa.ai search only."""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    search_type: SearchType = Field(SearchType.NEURAL, description="Type of search to perform")
    max_results: int = Field(10, description="Maximum number of results", ge=1, le=50)


# Response Models
class ExaFactCheckResponse(BaseModel):
    """Response model for Exa.ai fact-checking."""
    success: bool = Field(..., description="Whether the fact-check was successful")
    result: Optional[EnhancedFactCheckResult] = Field(None, description="Fact-checking result")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time: float = Field(..., description="Processing time in seconds")


class HallucinationCheckResponse(BaseModel):
    """Response model for hallucination detection."""
    success: bool = Field(..., description="Whether the hallucination check was successful")
    result: Optional[HallucinationResult] = Field(None, description="Hallucination detection result")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time: float = Field(..., description="Processing time in seconds")


class ExaSearchResponse(BaseModel):
    """Response model for Exa.ai search."""
    success: bool = Field(..., description="Whether the search was successful")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Search results")
    total_results: int = Field(0, description="Total number of results")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time: float = Field(..., description="Processing time in seconds")


class ServiceStatsResponse(BaseModel):
    """Response model for service statistics."""
    success: bool = Field(..., description="Whether stats retrieval was successful")
    stats: Optional[Dict[str, Any]] = Field(None, description="Service statistics")
    error: Optional[str] = Field(None, description="Error message if failed")


# API Endpoints
@router.post("/fact-check", response_model=ExaFactCheckResponse)
async def fact_check_with_exa(
    request: ExaFactCheckRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Perform enhanced fact-checking using Exa.ai neural search and hallucination detection.
    
    This endpoint combines:
    - Exa.ai neural search for semantic understanding
    - Tavily web search for broad coverage
    - Advanced hallucination detection
    - Enhanced confidence scoring
    
    Args:
        request: Fact-checking request parameters
        current_user: Current authenticated user
        
    Returns:
        Enhanced fact-checking result with dual search and hallucination analysis
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Exa.ai fact-check request from user {current_user.get('username', 'unknown')}")
        
        # Ensure service is initialized
        if not exa_fact_checking_service.dual_orchestrator:
            await exa_fact_checking_service.initialize()
        
        # Perform enhanced fact-checking
        result = await exa_fact_checking_service.fact_check_with_exa(
            claim=request.claim,
            context=request.context,
            search_strategy=request.search_strategy,
            require_both_providers=request.require_both_providers,
            enable_hallucination_detection=request.enable_hallucination_detection
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Exa.ai fact-check completed: verdict={result.verdict}, "
            f"confidence={result.confidence:.3f}, time={processing_time:.2f}s"
        )
        
        return ExaFactCheckResponse(
            success=True,
            result=result,
            processing_time=processing_time
        )
        
    except SearchProviderError as e:
        processing_time = time.time() - start_time
        logger.error(f"Search provider error in Exa.ai fact-check: {e}")
        
        return ExaFactCheckResponse(
            success=False,
            error=f"Search provider error: {str(e)}",
            processing_time=processing_time
        )
        
    except HallucinationDetectionError as e:
        processing_time = time.time() - start_time
        logger.error(f"Hallucination detection error: {e}")
        
        return ExaFactCheckResponse(
            success=False,
            error=f"Hallucination detection error: {str(e)}",
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Unexpected error in Exa.ai fact-check: {e}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/hallucination-check", response_model=HallucinationCheckResponse)
async def check_hallucination(
    request: HallucinationCheckRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Perform hallucination detection on a claim using Exa.ai's methodology.
    
    This endpoint specifically focuses on detecting whether a claim is likely
    to be a hallucination by analyzing evidence consistency and source credibility.
    
    Args:
        request: Hallucination check request parameters
        current_user: Current authenticated user
        
    Returns:
        Detailed hallucination analysis result
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Hallucination check request from user {current_user.get('username', 'unknown')}")
        
        # Perform hallucination detection
        result = await exa_fact_checking_service.check_hallucination_only(
            claim=request.claim,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Hallucination check completed: is_hallucination={result.is_hallucination}, "
            f"confidence={result.confidence_score:.3f}, time={processing_time:.2f}s"
        )
        
        return HallucinationCheckResponse(
            success=True,
            result=result,
            processing_time=processing_time
        )
        
    except HallucinationDetectionError as e:
        processing_time = time.time() - start_time
        logger.error(f"Hallucination detection error: {e}")
        
        return HallucinationCheckResponse(
            success=False,
            error=f"Hallucination detection error: {str(e)}",
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Unexpected error in hallucination check: {e}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/search", response_model=ExaSearchResponse)
async def search_with_exa(
    request: ExaSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Perform search using Exa.ai neural search capabilities.
    
    This endpoint provides direct access to Exa.ai's neural search
    for semantic understanding and content discovery.
    
    Args:
        request: Search request parameters
        current_user: Current authenticated user
        
    Returns:
        Search results from Exa.ai
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Exa.ai search request from user {current_user.get('username', 'unknown')}")
        
        # Perform Exa.ai search
        results = await exa_fact_checking_service.search_with_exa_only(
            query=request.query,
            search_type=request.search_type,
            max_results=request.max_results
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Exa.ai search completed: {len(results)} results, time={processing_time:.2f}s"
        )
        
        return ExaSearchResponse(
            success=True,
            results=results,
            total_results=len(results),
            processing_time=processing_time
        )
        
    except SearchProviderError as e:
        processing_time = time.time() - start_time
        logger.error(f"Search provider error in Exa.ai search: {e}")
        
        return ExaSearchResponse(
            success=False,
            error=f"Search provider error: {str(e)}",
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Unexpected error in Exa.ai search: {e}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/stats", response_model=ServiceStatsResponse)
async def get_exa_service_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get Exa.ai fact-checking service statistics.
    
    Returns comprehensive statistics about the service performance,
    including search provider status, success rates, and timing metrics.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Service statistics and performance metrics
    """
    try:
        logger.info(f"Service stats request from user {current_user.get('username', 'unknown')}")
        
        # Get service statistics
        stats = await exa_fact_checking_service.get_service_stats()
        
        logger.info("Service stats retrieved successfully")
        
        return ServiceStatsResponse(
            success=True,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Error retrieving service stats: {e}")
        
        return ServiceStatsResponse(
            success=False,
            error=f"Failed to retrieve stats: {str(e)}"
        )


@router.get("/health")
async def exa_service_health():
    """
    Check Exa.ai service health status.
    
    Returns the health status of all Exa.ai service components
    including search providers and orchestrator.
    
    Returns:
        Health status information
    """
    try:
        health_status = {
            "service": "exa_fact_checking",
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "components": {}
        }
        
        # Check if service is initialized
        if exa_fact_checking_service.dual_orchestrator:
            # Get provider status
            if exa_fact_checking_service.exa_provider:
                exa_status = await exa_fact_checking_service.exa_provider.get_status()
                health_status["components"]["exa_provider"] = exa_status.dict()
            
            if exa_fact_checking_service.tavily_provider:
                tavily_status = await exa_fact_checking_service.tavily_provider.get_status()
                health_status["components"]["tavily_provider"] = tavily_status.dict()
            
            if exa_fact_checking_service.hallucination_detector:
                health_status["components"]["hallucination_detector"] = {
                    "status": "available",
                    "threshold": exa_fact_checking_service.settings.HALLUCINATION_CONFIDENCE_THRESHOLD
                }
        else:
            health_status["status"] = "not_initialized"
            health_status["components"]["initialization"] = {
                "status": "pending",
                "message": "Service not yet initialized"
            }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        
        return {
            "service": "exa_fact_checking",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }
