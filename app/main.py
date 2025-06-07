"""
DSPy-Enhanced Fact-Checker API Platform
Main application entry point with FastAPI setup.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
import logging
from contextlib import asynccontextmanager
import time
import json
from datetime import datetime
from decimal import Decimal

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.logging import setup_logging
from app.core.middleware import (
    RequestLoggingMiddleware, SecurityHeadersMiddleware,
    CacheControlMiddleware, APIVersionMiddleware
)
from app.api.v1.models.base import ErrorResponse, ValidationErrorResponse, ValidationErrorDetail, ResponseStatus
from app.core.json_response import create_json_response


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


# Use the improved JSON response utility from core module


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting DSPy-Enhanced Fact-Checker API Platform...")
    
    # Initialize database connections
    try:
        from app.db.init_db import init_db
        db_success = await init_db()
        if db_success:
            logger.info("Database initialized successfully")
        else:
            logger.error("Database initialization failed")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    # Initialize Redis connection
    try:
        from app.core.redis import init_redis
        await init_redis()
        logger.info("Redis initialized successfully")
    except Exception as e:
        logger.error(f"Redis initialization error: {e}")

    # Initialize Qdrant vector database
    try:
        from app.core.qdrant import init_qdrant
        await init_qdrant()
        logger.info("Qdrant initialized successfully")
    except Exception as e:
        logger.error(f"Qdrant initialization error: {e}")

    # Initialize Celery (connection test)
    try:
        from app.core.celery import check_celery_health
        celery_health = await check_celery_health()
        if celery_health.get("status") == "healthy":
            logger.info("Celery connection verified")
        else:
            logger.warning(f"Celery health check: {celery_health}")
    except Exception as e:
        logger.error(f"Celery initialization error: {e}")
    
    logger.info("Application startup complete!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Close database connections
    try:
        from app.db.database import close_database
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    # Close Redis connection
    try:
        from app.core.redis import close_redis
        await close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")

    # Close Qdrant connection
    try:
        from app.core.qdrant import close_qdrant
        await close_qdrant()
        logger.info("Qdrant connection closed")
    except Exception as e:
        logger.error(f"Error closing Qdrant: {e}")
    
    logger.info("Application shutdown complete!")


# Create FastAPI application
app = FastAPI(
    title="DSPy-Enhanced Fact-Checker API",
    description="Advanced fact-checking platform with document processing capabilities using DSPy optimization",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# Add custom middleware (order matters - last added is executed first)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CacheControlMiddleware)
app.add_middleware(APIVersionMiddleware, api_version="1.0.0")

# Add FastAPI built-in middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    request_id = getattr(request.state, "request_id", None)

    # Convert Pydantic errors to our format
    validation_errors = []
    for error in exc.errors():
        validation_errors.append(ValidationErrorDetail(
            field=".".join(str(loc) for loc in error["loc"]),
            message=error["msg"],
            value=error.get("input")
        ))

    logger.warning(f"Validation error {request_id}: {exc}")

    return create_json_response(
        content=ValidationErrorResponse(
            status=ResponseStatus.ERROR,
            message="Validation failed",
            request_id=request_id,
            validation_errors=validation_errors
        ).dict(),
        status_code=422
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", None)

    logger.warning(f"HTTP exception {request_id}: {exc.status_code} - {exc.detail}")

    return create_json_response(
        content=ErrorResponse(
            status=ResponseStatus.ERROR,
            message=exc.detail,
            request_id=request_id,
            error_code=f"http_{exc.status_code}"
        ).dict(),
        status_code=exc.status_code
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    request_id = getattr(request.state, "request_id", None)

    logger.error(f"Global exception {request_id}: {exc}", exc_info=True)

    return create_json_response(
        content=ErrorResponse(
            status=ResponseStatus.ERROR,
            message="An unexpected error occurred. Please try again later.",
            request_id=request_id,
            error_code="internal_error"
        ).dict(),
        status_code=500
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "service": "dspy-fact-checker-api",
        "version": "1.0.0",
        "timestamp": time.time(),
        "components": {}
    }

    # Check database health
    try:
        from app.db.init_db import check_db_health
        db_health = await check_db_health()
        health_status["components"]["database"] = db_health
        if db_health.get("status") != "connected":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["database"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # Check Redis health
    try:
        from app.core.redis import RedisHealthCheck
        redis_health = await RedisHealthCheck.check_connection()
        redis_info = await RedisHealthCheck.get_info()
        health_status["components"]["redis"] = {
            "status": "connected" if redis_health else "disconnected",
            "info": redis_info
        }
        if not redis_health:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["redis"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # Check Qdrant health
    try:
        from app.core.qdrant import QdrantHealthCheck
        qdrant_health = await QdrantHealthCheck.check_connection()
        qdrant_info = await QdrantHealthCheck.get_info()
        health_status["components"]["qdrant"] = {
            "status": "connected" if qdrant_health else "disconnected",
            "info": qdrant_info
        }
        if not qdrant_health:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["qdrant"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # Check Celery health
    try:
        from app.core.celery import check_celery_health
        celery_health = await check_celery_health()
        health_status["components"]["celery"] = celery_health
        if celery_health.get("status") != "healthy":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["celery"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    return health_status


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "DSPy-Enhanced Fact-Checker API Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1"
    }


# Include API router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
