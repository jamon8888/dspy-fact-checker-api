"""
Usage Tracking Middleware

Middleware for tracking API usage for billing and quota management.
"""

import logging
import time
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.services.subscription_service import subscription_service
from app.services.auth_service import auth_service
from app.db.database import get_db

logger = logging.getLogger(__name__)


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track API usage for billing and quota management."""
    
    def __init__(self, app, track_anonymous: bool = True):
        """Initialize usage tracking middleware."""
        super().__init__(app)
        self.track_anonymous = track_anonymous
        self.logger = logging.getLogger(__name__ + ".UsageTrackingMiddleware")
        
        # Define which endpoints to track
        self.tracked_endpoints = {
            "/api/v1/text/fact-check": "text_requests",
            "/api/v1/documents/upload": "document_requests",
            "/api/v1/documents/fact-check": "document_requests",
            "/api/v1/urls/fact-check": "url_requests",
            "/api/v1/dspy/fact-check": "text_requests",
            "/api/v1/optimization/optimize-document-processing": "api_calls",
            "/api/v1/optimization/recommend-model": "api_calls"
        }
        
        # Endpoints that don't count towards usage
        self.excluded_endpoints = {
            "/api/v1/health",
            "/api/v1/auth/",
            "/api/v1/billing/",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track usage."""
        start_time = time.time()
        
        # Check if this endpoint should be tracked
        should_track = self._should_track_endpoint(request.url.path)
        
        if not should_track:
            # Process request without tracking
            response = await call_next(request)
            return response
        
        # Get user information
        user = await self._get_user_from_request(request)
        user_id = user.id if user else None
        
        # Check quota limits before processing (for authenticated users)
        if user_id:
            usage_type = self._get_usage_type(request.url.path)
            if usage_type:
                quota_check = await self._check_quota_limits(user_id, usage_type)
                if not quota_check.get("allowed", False):
                    # Return quota exceeded response
                    from fastapi import HTTPException, status
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "Quota exceeded",
                            "usage_type": usage_type,
                            "current_usage": quota_check.get("current_usage", 0),
                            "limit": quota_check.get("limit", 0),
                            "overage_cost": quota_check.get("overage_cost", 0.0)
                        }
                    )
        
        # Process the request
        response = await call_next(request)
        
        # Track usage after successful request
        if response.status_code < 400:  # Only track successful requests
            processing_time = time.time() - start_time
            await self._track_usage(
                request=request,
                response=response,
                user_id=user_id,
                processing_time=processing_time
            )
        
        return response
    
    def _should_track_endpoint(self, path: str) -> bool:
        """Check if endpoint should be tracked."""
        # Check excluded endpoints
        for excluded in self.excluded_endpoints:
            if path.startswith(excluded):
                return False
        
        # Check if it's a tracked endpoint
        return any(path.startswith(endpoint) for endpoint in self.tracked_endpoints.keys())
    
    def _get_usage_type(self, path: str) -> Optional[str]:
        """Get usage type for endpoint."""
        for endpoint, usage_type in self.tracked_endpoints.items():
            if path.startswith(endpoint):
                return usage_type
        return "api_calls"  # Default
    
    async def _get_user_from_request(self, request: Request) -> Optional:
        """Extract user from request authentication."""
        try:
            # Check for Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header:
                return None
            
            # Extract token
            if not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Get database session
            db = next(get_db())
            
            try:
                # Try JWT token first
                payload = auth_service.verify_token(token)
                if payload:
                    user_id = payload.get("sub")
                    if user_id:
                        from app.models.user import User
                        user = db.query(User).filter(User.id == int(user_id)).first()
                        if user and user.is_active:
                            return user
                
                # Try API key
                user = await auth_service.verify_api_key(db, token)
                if user:
                    return user
                
                return None
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error extracting user from request: {e}")
            return None
    
    async def _check_quota_limits(self, user_id: int, usage_type: str) -> dict:
        """Check quota limits for user."""
        try:
            db = next(get_db())
            try:
                quota_check = await subscription_service.check_quota_limits(
                    db=db,
                    user_id=user_id,
                    usage_type=usage_type,
                    requested_usage=1
                )
                return quota_check
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error checking quota limits: {e}")
            return {"allowed": True}  # Allow on error to avoid blocking
    
    async def _track_usage(
        self,
        request: Request,
        response: Response,
        user_id: Optional[int],
        processing_time: float
    ):
        """Track usage for billing and analytics."""
        try:
            if not user_id and not self.track_anonymous:
                return
            
            usage_type = self._get_usage_type(request.url.path)
            if not usage_type:
                return
            
            # Extract additional metadata
            metadata = {
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "processing_time": processing_time,
                "user_agent": request.headers.get("user-agent"),
                "ip_address": request.client.host if request.client else None
            }
            
            # Extract model information from response headers if available
            model_used = response.headers.get("X-Model-Used")
            if model_used:
                metadata["model_used"] = model_used
            
            # Extract token count from response headers if available
            tokens_processed = response.headers.get("X-Tokens-Processed")
            if tokens_processed:
                try:
                    metadata["tokens_processed"] = int(tokens_processed)
                except ValueError:
                    pass
            
            # Track usage in database
            if user_id:
                db = next(get_db())
                try:
                    await subscription_service.track_usage(
                        db=db,
                        user_id=user_id,
                        usage_type=usage_type,
                        usage_count=1,
                        metadata=metadata
                    )
                finally:
                    db.close()
            
            # Log usage for analytics
            self.logger.info(
                f"Usage tracked: user_id={user_id}, type={usage_type}, "
                f"endpoint={request.url.path}, time={processing_time:.3f}s"
            )
            
        except Exception as e:
            self.logger.error(f"Error tracking usage: {e}")


class QuotaEnforcementMiddleware(BaseHTTPMiddleware):
    """Middleware specifically for quota enforcement."""
    
    def __init__(self, app):
        """Initialize quota enforcement middleware."""
        super().__init__(app)
        self.logger = logging.getLogger(__name__ + ".QuotaEnforcementMiddleware")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Enforce quota limits before processing requests."""
        # Check if this is a quota-limited endpoint
        if not self._is_quota_limited_endpoint(request.url.path):
            return await call_next(request)
        
        # Get user from request
        user = await self._get_authenticated_user(request)
        if not user:
            # Allow anonymous requests (they have their own limits)
            return await call_next(request)
        
        # Check quota
        usage_type = self._get_usage_type_for_endpoint(request.url.path)
        if usage_type:
            quota_status = await self._check_user_quota(user.id, usage_type)
            
            if not quota_status.get("allowed", True):
                from fastapi import HTTPException, status
                from fastapi.responses import JSONResponse
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Quota exceeded",
                        "message": f"You have exceeded your {usage_type} quota",
                        "quota_info": {
                            "current_usage": quota_status.get("current_usage", 0),
                            "limit": quota_status.get("limit", 0),
                            "remaining": quota_status.get("remaining", 0),
                            "overage": quota_status.get("overage", 0),
                            "overage_cost": quota_status.get("overage_cost", 0.0)
                        },
                        "upgrade_url": "/billing/upgrade"
                    }
                )
        
        return await call_next(request)
    
    def _is_quota_limited_endpoint(self, path: str) -> bool:
        """Check if endpoint is subject to quota limits."""
        quota_limited_endpoints = [
            "/api/v1/text/fact-check",
            "/api/v1/documents/upload",
            "/api/v1/documents/fact-check",
            "/api/v1/urls/fact-check",
            "/api/v1/dspy/fact-check"
        ]
        
        return any(path.startswith(endpoint) for endpoint in quota_limited_endpoints)
    
    def _get_usage_type_for_endpoint(self, path: str) -> Optional[str]:
        """Get usage type for endpoint."""
        endpoint_mapping = {
            "/api/v1/text/fact-check": "text_requests",
            "/api/v1/documents/upload": "document_requests",
            "/api/v1/documents/fact-check": "document_requests",
            "/api/v1/urls/fact-check": "url_requests",
            "/api/v1/dspy/fact-check": "text_requests"
        }
        
        for endpoint, usage_type in endpoint_mapping.items():
            if path.startswith(endpoint):
                return usage_type
        
        return None
    
    async def _get_authenticated_user(self, request: Request):
        """Get authenticated user from request."""
        try:
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header[7:]
            db = next(get_db())
            
            try:
                # Try JWT token
                payload = auth_service.verify_token(token)
                if payload:
                    user_id = payload.get("sub")
                    if user_id:
                        from app.models.user import User
                        user = db.query(User).filter(User.id == int(user_id)).first()
                        if user and user.is_active:
                            return user
                
                # Try API key
                user = await auth_service.verify_api_key(db, token)
                return user
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error getting authenticated user: {e}")
            return None
    
    async def _check_user_quota(self, user_id: int, usage_type: str) -> dict:
        """Check user's quota for usage type."""
        try:
            db = next(get_db())
            try:
                return await subscription_service.check_quota_limits(
                    db=db,
                    user_id=user_id,
                    usage_type=usage_type,
                    requested_usage=1
                )
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error checking user quota: {e}")
            return {"allowed": True}  # Allow on error
