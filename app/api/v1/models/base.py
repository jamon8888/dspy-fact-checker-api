"""
Base Pydantic models for the DSPy-Enhanced Fact-Checker API Platform.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TimestampMixin:
    """Mixin for timestamp fields."""

    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


class ResponseStatus(str, Enum):
    """Standard response status values."""
    
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStatus(str, Enum):
    """Processing status values."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Priority levels."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    status: ResponseStatus = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier")


class ErrorResponse(BaseResponse):
    """Error response model."""
    
    status: ResponseStatus = Field(default=ResponseStatus.ERROR)
    error_code: Optional[str] = Field(None, description="Error code")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class SuccessResponse(BaseResponse):
    """Success response model."""
    
    status: ResponseStatus = Field(default=ResponseStatus.SUCCESS)
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseResponse):
    """Paginated response model."""
    
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Response data")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
    
    @classmethod
    def create(
        cls,
        data: List[Dict[str, Any]],
        page: int,
        page_size: int,
        total_items: int,
        **kwargs
    ) -> "PaginatedResponse":
        """Create a paginated response."""
        
        total_pages = (total_items + page_size - 1) // page_size
        
        pagination = {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
        
        return cls(
            data=data,
            pagination=pagination,
            status=ResponseStatus.SUCCESS,
            **kwargs
        )


class HealthStatus(BaseModel):
    """Health check status model."""
    
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Environment")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")


class DetailedHealthStatus(HealthStatus):
    """Detailed health check status model."""
    
    system_info: Optional[Dict[str, Any]] = Field(None, description="System information")
    dependencies: Optional[Dict[str, str]] = Field(None, description="Dependency status")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")


class APIInfo(BaseModel):
    """API information model."""
    
    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    docs_url: Optional[str] = Field(None, description="Documentation URL")
    health_url: str = Field(..., description="Health check URL")
    endpoints: Dict[str, str] = Field(..., description="Available endpoints")


class ValidationErrorDetail(BaseModel):
    """Validation error detail model."""
    
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    value: Optional[Any] = Field(None, description="Invalid value")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response model."""
    
    error_code: str = Field(default="validation_error")
    validation_errors: List[ValidationErrorDetail] = Field(..., description="Validation errors")
