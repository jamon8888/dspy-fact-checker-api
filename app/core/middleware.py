"""
Custom middleware for the DSPy-Enhanced Fact-Checker API Platform.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
import logging
from app.core.json_response import create_json_response
from typing import Callable

from app.api.v1.models.base import ErrorResponse, ResponseStatus

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response with logging."""
        
        # Generate request ID if not present
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get('User-Agent', 'unknown')
        
        # Log request
        start_time = time.time()
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path} "
            f"from {client_ip} ({user_agent})"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            logger.info(
                f"Response {request_id}: {response.status_code} "
                f"({process_time:.3f}s)"
            )
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"Error {request_id}: {str(e)} ({process_time:.3f}s)",
                exc_info=True
            )
            
            # Return error response
            return create_json_response(
                content=ErrorResponse(
                    status=ResponseStatus.ERROR,
                    message="Internal server error",
                    request_id=request_id,
                    error_code="internal_error"
                ).dict(),
                status_code=500,
                headers={"X-Request-ID": request_id}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )
        
        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Middleware for adding cache control headers."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add cache control headers based on endpoint."""
        
        response = await call_next(request)
        
        # Set cache headers based on path
        path = request.url.path
        
        if path.startswith('/health'):
            # Health endpoints - short cache
            response.headers["Cache-Control"] = "public, max-age=60"
        elif path.startswith('/api/v1/documents/status'):
            # Status endpoints - no cache
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        elif path.startswith('/api/v1/documents/results'):
            # Results endpoints - longer cache
            response.headers["Cache-Control"] = "public, max-age=3600"
        elif path.startswith('/docs') or path.startswith('/openapi.json'):
            # Documentation - medium cache
            response.headers["Cache-Control"] = "public, max-age=1800"
        else:
            # Default - no cache for API endpoints
            response.headers["Cache-Control"] = "no-cache"
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware for response compression hints."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add compression hints to response."""
        
        response = await call_next(request)
        
        # Add compression hint for JSON responses
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            response.headers["Vary"] = "Accept-Encoding"
        
        return response


class APIVersionMiddleware(BaseHTTPMiddleware):
    """Middleware for API versioning."""
    
    def __init__(self, app: ASGIApp, api_version: str = "1.0.0"):
        super().__init__(app)
        self.api_version = api_version
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add API version to response headers."""
        
        response = await call_next(request)
        
        # Add API version header
        response.headers["X-API-Version"] = self.api_version
        
        # Add deprecation warnings for old versions if needed
        # TODO: Implement version deprecation logic
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting (basic implementation)."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.requests = {}  # In production, use Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting."""
        
        # Skip rate limiting for health checks
        if request.url.path.startswith('/health'):
            return await call_next(request)
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        
        # Check rate limit (basic implementation)
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        # Check limit (60 requests per minute)
        if len(self.requests[client_ip]) >= 60:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return create_json_response(
                content=ErrorResponse(
                    status=ResponseStatus.ERROR,
                    message="Rate limit exceeded. Please try again later.",
                    error_code="rate_limit_exceeded"
                ).dict(),
                status_code=429,
                headers={
                    "X-RateLimit-Limit": "60",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(window_start + 60)),
                    "Retry-After": "60"
                }
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = 60 - len(self.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = "60"
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(window_start + 60))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
