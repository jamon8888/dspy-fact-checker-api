"""
Custom exceptions for the search module.
"""


class SearchProviderError(Exception):
    """Base exception for search provider errors."""
    
    def __init__(self, message: str, provider: str = None, original_error: Exception = None):
        self.message = message
        self.provider = provider
        self.original_error = original_error
        super().__init__(self.message)


class SearchTimeoutError(SearchProviderError):
    """Exception raised when search operation times out."""
    pass


class SearchRateLimitError(SearchProviderError):
    """Exception raised when search provider rate limit is exceeded."""
    
    def __init__(self, message: str, provider: str = None, retry_after: int = None):
        super().__init__(message, provider)
        self.retry_after = retry_after


class SearchOrchestrationError(Exception):
    """Exception raised when dual search orchestration fails."""
    
    def __init__(self, message: str, failed_providers: list = None):
        self.message = message
        self.failed_providers = failed_providers or []
        super().__init__(self.message)


class SearchConfigurationError(Exception):
    """Exception raised when search configuration is invalid."""
    pass


class HallucinationDetectionError(SearchProviderError):
    """Exception raised when hallucination detection fails."""
    pass
