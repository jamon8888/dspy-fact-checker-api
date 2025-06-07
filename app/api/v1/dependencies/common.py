"""
Common dependencies for the DSPy-Enhanced Fact-Checker API Platform.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import time
import uuid
import logging
from functools import wraps

from app.core.config import get_settings, Settings
from app.api.v1.models.base import ValidationErrorResponse, ValidationErrorDetail

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_request_id(request: Request) -> str:
    """Generate or retrieve request ID for tracking."""
    request_id = getattr(request.state, 'request_id', None)
    if not request_id:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
    return request_id


async def get_client_ip(request: Request) -> str:
    """Get client IP address."""
    # Check for forwarded headers first
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"


async def get_user_agent(request: Request) -> str:
    """Get user agent string."""
    return request.headers.get('User-Agent', 'unknown')


class RateLimiter:
    """Simple rate limiter for API endpoints."""
    
    def __init__(self):
        self.requests = {}  # In production, use Redis
        
    async def check_limit(
        self, 
        identifier: str, 
        max_requests: int = 60, 
        window_seconds: int = 60
    ) -> bool:
        """Check if request is within rate limits."""
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier] 
                if req_time > window_start
            ]
        else:
            self.requests[identifier] = []
        
        # Check limit
        if len(self.requests[identifier]) >= max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(current_time)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> None:
    """Check rate limits for the request."""
    client_ip = await get_client_ip(request)
    
    # Check rate limit
    allowed = await rate_limiter.check_limit(
        identifier=client_ip,
        max_requests=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        window_seconds=60
    )
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )


async def validate_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings)
) -> Optional[str]:
    """Validate API key (placeholder for future authentication)."""
    # For now, API is open. In production, implement proper API key validation
    if credentials:
        return credentials.credentials
    return None


async def get_processing_options(
    perform_ocr: bool = True,
    force_ocr: bool = False,
    preserve_formatting: bool = True,
    extract_tables: bool = True,
    extract_images: bool = True,
    language_detection: bool = True,
    content_segmentation: str = "auto",
    confidence_threshold: float = 0.7,
    max_processing_time: int = 300
) -> Dict[str, Any]:
    """Get processing options from query parameters."""
    
    # Validate content_segmentation
    valid_segmentation = ["auto", "semantic", "paragraph", "sentence"]
    if content_segmentation not in valid_segmentation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content_segmentation. Must be one of: {valid_segmentation}"
        )
    
    # Validate confidence_threshold
    if not 0.0 <= confidence_threshold <= 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="confidence_threshold must be between 0.0 and 1.0"
        )
    
    # Validate max_processing_time
    if not 30 <= max_processing_time <= 1800:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_processing_time must be between 30 and 1800 seconds"
        )
    
    return {
        "perform_ocr": perform_ocr,
        "force_ocr": force_ocr,
        "preserve_formatting": preserve_formatting,
        "extract_tables": extract_tables,
        "extract_images": extract_images,
        "language_detection": language_detection,
        "content_segmentation": content_segmentation,
        "confidence_threshold": confidence_threshold,
        "max_processing_time": max_processing_time
    }


async def validate_file_upload(
    filename: str,
    file_size: int,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Validate uploaded file."""
    
    # Check filename
    if not filename or '.' not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename. Must include file extension."
        )
    
    # Check file extension
    extension = filename.split('.')[-1].lower()
    if extension not in settings.SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Supported: {', '.join(settings.SUPPORTED_FORMATS)}"
        )
    
    # Check file size
    if file_size > settings.MAX_FILE_SIZE:
        max_size_mb = settings.MAX_FILE_SIZE // 1024 // 1024
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {max_size_mb}MB"
        )
    
    return {
        "filename": filename,
        "extension": extension,
        "file_size": file_size,
        "is_valid": True
    }


def handle_validation_error(func):
    """Decorator to handle Pydantic validation errors."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            # Convert ValueError to proper validation error response
            error_detail = ValidationErrorDetail(
                field="unknown",
                message=str(e),
                value=None
            )
            
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ValidationErrorResponse(
                    validation_errors=[error_detail],
                    message="Validation error occurred"
                ).dict()
            )
    return wrapper


async def get_pagination_params(
    page: int = 1,
    page_size: int = 20
) -> Dict[str, int]:
    """Get pagination parameters with validation."""
    
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be >= 1"
        )
    
    if not 1 <= page_size <= 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100"
        )
    
    return {
        "page": page,
        "page_size": page_size,
        "offset": (page - 1) * page_size
    }


async def log_request(
    request: Request,
    request_id: str = Depends(get_request_id),
    client_ip: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent)
) -> None:
    """Log incoming request details."""
    
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path} "
        f"from {client_ip} ({user_agent})"
    )
    
    # Store in request state for response logging
    request.state.start_time = time.time()


async def estimate_processing_cost(
    file_size: Optional[int] = None,
    text_length: Optional[int] = None,
    processing_options: Optional[Dict[str, Any]] = None
) -> float:
    """Estimate processing cost based on input characteristics."""
    
    base_cost = 0.01  # Base cost in USD
    
    # File size factor
    if file_size:
        size_mb = file_size / (1024 * 1024)
        base_cost += size_mb * 0.005  # $0.005 per MB
    
    # Text length factor
    if text_length:
        base_cost += (text_length / 1000) * 0.001  # $0.001 per 1000 chars
    
    # Processing options factor
    if processing_options:
        if processing_options.get('force_ocr', False):
            base_cost *= 1.5  # 50% increase for forced OCR
        
        if processing_options.get('extract_tables', False):
            base_cost *= 1.2  # 20% increase for table extraction
        
        if processing_options.get('extract_images', False):
            base_cost *= 1.1  # 10% increase for image extraction
    
    return round(base_cost, 4)


async def estimate_processing_time(
    file_size: Optional[int] = None,
    text_length: Optional[int] = None,
    processing_options: Optional[Dict[str, Any]] = None
) -> int:
    """Estimate processing time in seconds."""
    
    base_time = 5  # Base time in seconds
    
    # File size factor
    if file_size:
        size_mb = file_size / (1024 * 1024)
        base_time += int(size_mb * 2)  # 2 seconds per MB
    
    # Text length factor
    if text_length:
        base_time += int(text_length / 5000)  # 1 second per 5000 chars
    
    # Processing options factor
    if processing_options:
        if processing_options.get('force_ocr', False):
            base_time *= 2  # Double time for OCR
        
        if processing_options.get('extract_tables', False):
            base_time += 10  # Additional 10 seconds for tables
        
        if processing_options.get('extract_images', False):
            base_time += 5  # Additional 5 seconds for images
    
    return max(base_time, 5)  # Minimum 5 seconds
