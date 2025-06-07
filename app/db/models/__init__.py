"""
Database models for the DSPy-Enhanced Fact-Checker API Platform.
"""

from .base import (
    Base,
    BaseModel,
    TimestampMixin,
    UUIDMixin,
    ProcessingJob,
    Document,
    TextAnalysis,
    URLAnalysis,
    FactCheckResult,
    SystemMetrics,
    UserSession
)

__all__ = [
    "Base",
    "BaseModel",
    "TimestampMixin",
    "UUIDMixin",
    "ProcessingJob",
    "Document",
    "TextAnalysis",
    "URLAnalysis",
    "FactCheckResult",
    "SystemMetrics",
    "UserSession"
]