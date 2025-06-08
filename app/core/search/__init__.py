"""
Search module for the DSPy-Enhanced Fact-Checker API Platform.

This module provides a unified search abstraction layer supporting multiple
search providers including Exa.ai neural search and Tavily web search.
"""

from .base_search import BaseSearchProvider
from .models import (
    SearchQuery,
    SearchResult,
    DualSearchResult,
    HallucinationResult,
    SearchType
)
from .exceptions import (
    SearchProviderError,
    SearchTimeoutError,
    SearchRateLimitError,
    SearchOrchestrationError
)

__all__ = [
    "BaseSearchProvider",
    "SearchQuery",
    "SearchResult", 
    "DualSearchResult",
    "HallucinationResult",
    "SearchType",
    "SearchProviderError",
    "SearchTimeoutError",
    "SearchRateLimitError",
    "SearchOrchestrationError"
]
