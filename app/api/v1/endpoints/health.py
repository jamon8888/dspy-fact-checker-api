"""
Health check endpoints for the DSPy-Enhanced Fact-Checker API Platform.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import time
import psutil
import logging

from app.core.config import get_settings, Settings
from app.api.v1.models.base import HealthStatus, DetailedHealthStatus, APIInfo

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_services_status() -> Dict[str, str]:
    """Get the status of all services."""
    services = {}

    # Check database
    try:
        from app.db.init_db import check_db_health
        db_health = await check_db_health()
        services["database"] = "connected" if db_health.get("connected", False) else "disconnected"
    except Exception as e:
        services["database"] = f"error: {str(e)[:50]}"

    # TODO: Check Redis
    services["redis"] = "not_configured"

    # TODO: Check Qdrant
    services["qdrant"] = "not_configured"

    # TODO: Check Celery
    services["celery"] = "not_configured"

    return services


@router.get("/", response_model=HealthStatus)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthStatus:
    """Basic health check endpoint."""
    return HealthStatus(
        service=settings.APP_NAME,
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        uptime=time.time()  # TODO: Calculate actual uptime
    )


@router.get("/detailed")
async def detailed_health_check(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """Detailed health check with system information."""
    
    # Get system information
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        },
        "services": await get_services_status()
    }


@router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """Kubernetes readiness probe endpoint."""
    # TODO: Add actual readiness checks for dependencies
    return {
        "status": "ready",
        "timestamp": time.time()
    }


@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """Kubernetes liveness probe endpoint."""
    return {
        "status": "alive",
        "timestamp": time.time()
    }
