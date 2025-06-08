"""
API v1 router configuration for the DSPy-Enhanced Fact-Checker API Platform.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, documents, text, urls, ocr, content_extraction, focused_documents, dspy_fact_checking, enhanced_fact_checking, exa_fact_checking, optimization, auth, billing, monitoring


# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["document-processing"]
)

api_router.include_router(
    text.router,
    prefix="/text",
    tags=["text-processing"]
)

api_router.include_router(
    urls.router,
    prefix="/urls",
    tags=["url-processing"]
)

api_router.include_router(
    ocr.router,
    prefix="/ocr",
    tags=["optical-character-recognition"]
)

api_router.include_router(
    content_extraction.router,
    prefix="/content",
    tags=["content-extraction"]
)

api_router.include_router(
    focused_documents.router,
    prefix="/focused",
    tags=["focused-document-processing"]
)

api_router.include_router(
    dspy_fact_checking.router,
    prefix="/dspy",
    tags=["dspy-fact-checking"]
)

api_router.include_router(
    enhanced_fact_checking.router,
    prefix="/enhanced-fact-check",
    tags=["enhanced-fact-checking"]
)

api_router.include_router(
    exa_fact_checking.router,
    prefix="/exa-fact-check",
    tags=["exa-fact-checking"]
)

api_router.include_router(
    optimization.router,
    prefix="/optimization",
    tags=["optimization"]
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    billing.router,
    prefix="/billing",
    tags=["billing"]
)

api_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["monitoring"]
)
