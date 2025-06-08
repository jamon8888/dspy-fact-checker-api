"""
Configuration settings for the DSPy-Enhanced Fact-Checker API Platform.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    APP_NAME: str = "DSPy-Enhanced Fact-Checker API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=1, env="WORKERS")
    
    # Security settings
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/factchecker",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Qdrant vector database settings
    QDRANT_URL: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    QDRANT_API_KEY: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = Field(default="fact_checker_embeddings", env="QDRANT_COLLECTION_NAME")
    
    # Celery settings
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")

    # Database settings
    DATABASE_HOST: str = Field(default="localhost", env="DATABASE_HOST")
    DATABASE_PORT: int = Field(default=5432, env="DATABASE_PORT")
    DATABASE_NAME: str = Field(default="fact_checker", env="DATABASE_NAME")
    DATABASE_USER: str = Field(default="postgres", env="DATABASE_USER")
    DATABASE_PASSWORD: str = Field(default="password", env="DATABASE_PASSWORD")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")

    # AI Model API Keys
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENROUTER_API_KEY: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    PERPLEXITY_API_KEY: Optional[str] = Field(default=None, env="PERPLEXITY_API_KEY")
    MISTRAL_API_KEY: Optional[str] = Field(default=None, env="MISTRAL_API_KEY")

    # Search Provider API Keys
    EXA_API_KEY: Optional[str] = Field(default=None, env="EXA_API_KEY")
    TAVILY_API_KEY: Optional[str] = Field(default=None, env="TAVILY_API_KEY")
    
    # Document processing settings
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    SUPPORTED_FORMATS: List[str] = Field(
        default=["pdf", "doc", "docx", "txt"],
        env="SUPPORTED_FORMATS"
    )
    PROCESSING_TIMEOUT: int = Field(default=300, env="PROCESSING_TIMEOUT")  # 5 minutes
    
    # Docling settings
    DOCLING_MAX_PAGES: int = Field(default=1000, env="DOCLING_MAX_PAGES")
    DOCLING_EXTRACT_TABLES: bool = Field(default=True, env="DOCLING_EXTRACT_TABLES")
    DOCLING_EXTRACT_IMAGES: bool = Field(default=True, env="DOCLING_EXTRACT_IMAGES")
    
    # OCR settings
    OCR_CONFIDENCE_THRESHOLD: float = Field(default=0.7, env="OCR_CONFIDENCE_THRESHOLD")
    OCR_MAX_PAGES: int = Field(default=100, env="OCR_MAX_PAGES")
    
    # DSPy settings
    DSPY_DEFAULT_MODEL: str = Field(default="gpt-4o-mini", env="DSPY_DEFAULT_MODEL")
    DSPY_OPTIMIZATION_ENABLED: bool = Field(default=True, env="DSPY_OPTIMIZATION_ENABLED")
    DSPY_CACHE_ENABLED: bool = Field(default=True, env="DSPY_CACHE_ENABLED")
    
    # Rate limiting settings
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    RATE_LIMIT_REQUESTS_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_REQUESTS_PER_HOUR")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Monitoring settings
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")

    # Background processing settings
    MAX_CONCURRENT_JOBS: int = Field(default=10, env="MAX_CONCURRENT_JOBS")
    JOB_TIMEOUT: int = Field(default=3600, env="JOB_TIMEOUT")  # 1 hour

    # Caching settings
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    SESSION_TTL: int = Field(default=86400, env="SESSION_TTL")  # 24 hours

    # File upload settings
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    TEMP_DIR: str = Field(default="temp", env="TEMP_DIR")

    # Document processing settings
    PROCESSING_TIMEOUT: int = Field(default=300, env="PROCESSING_TIMEOUT")  # 5 minutes

    # Docling-specific settings
    DOCLING_EXTRACT_IMAGES: bool = Field(default=True, env="DOCLING_EXTRACT_IMAGES")
    DOCLING_EXTRACT_TABLES: bool = Field(default=True, env="DOCLING_EXTRACT_TABLES")
    DOCLING_MAX_PAGES: int = Field(default=1000, env="DOCLING_MAX_PAGES")
    DOCLING_DO_OCR: bool = Field(default=False, env="DOCLING_DO_OCR")  # We'll use Mistral OCR

    # Mistral OCR settings
    MISTRAL_API_KEY: str = Field(default="", env="MISTRAL_API_KEY")
    MISTRAL_OCR_MODEL: str = Field(default="mistral-ocr-latest", env="MISTRAL_OCR_MODEL")
    MISTRAL_OCR_TIMEOUT: int = Field(default=300, env="MISTRAL_OCR_TIMEOUT")  # 5 minutes
    MISTRAL_OCR_MAX_FILE_SIZE: int = Field(default=50*1024*1024, env="MISTRAL_OCR_MAX_FILE_SIZE")  # 50MB
    MISTRAL_OCR_INCLUDE_IMAGES: bool = Field(default=True, env="MISTRAL_OCR_INCLUDE_IMAGES")

    # Context7 MCP server settings
    CONTEXT7_SERVER_URL: str = Field(default="http://localhost:3000", env="CONTEXT7_SERVER_URL")
    CONTEXT7_API_KEY: str = Field(default="", env="CONTEXT7_API_KEY")
    CONTEXT7_TIMEOUT: int = Field(default=30, env="CONTEXT7_TIMEOUT")  # 30 seconds
    CONTEXT7_MAX_RETRIES: int = Field(default=3, env="CONTEXT7_MAX_RETRIES")
    CONTEXT7_ENABLE_CONTEXT_STORAGE: bool = Field(default=True, env="CONTEXT7_ENABLE_CONTEXT_STORAGE")

    # Exa.ai Configuration
    EXA_BASE_URL: str = Field(default="https://api.exa.ai", env="EXA_BASE_URL")
    EXA_RATE_LIMIT_CALLS: int = Field(default=100, env="EXA_RATE_LIMIT_CALLS")
    EXA_RATE_LIMIT_PERIOD: int = Field(default=60, env="EXA_RATE_LIMIT_PERIOD")
    EXA_TIMEOUT: int = Field(default=30, env="EXA_TIMEOUT")
    EXA_MAX_RETRIES: int = Field(default=3, env="EXA_MAX_RETRIES")

    # Search Configuration
    SEARCH_DEFAULT_PROVIDER: str = Field(default="dual", env="SEARCH_DEFAULT_PROVIDER")
    SEARCH_PARALLEL_ENABLED: bool = Field(default=True, env="SEARCH_PARALLEL_ENABLED")
    SEARCH_CACHE_TTL: int = Field(default=3600, env="SEARCH_CACHE_TTL")
    SEARCH_MAX_RESULTS: int = Field(default=10, env="SEARCH_MAX_RESULTS")

    # Hallucination Detection
    HALLUCINATION_CONFIDENCE_THRESHOLD: float = Field(default=0.7, env="HALLUCINATION_CONFIDENCE_THRESHOLD")
    HALLUCINATION_DETECTION_ENABLED: bool = Field(default=True, env="HALLUCINATION_DETECTION_ENABLED")
    HALLUCINATION_CACHE_ENABLED: bool = Field(default=True, env="HALLUCINATION_CACHE_ENABLED")

    # Dual Search Performance
    DUAL_SEARCH_TIMEOUT: int = Field(default=10, env="DUAL_SEARCH_TIMEOUT")
    SEARCH_RESULT_AGGREGATION: bool = Field(default=True, env="SEARCH_RESULT_AGGREGATION")
    INTELLIGENT_ROUTING_ENABLED: bool = Field(default=True, env="INTELLIGENT_ROUTING_ENABLED")
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed_environments = ["development", "staging", "production"]
        if v not in allowed_environments:
            raise ValueError(f"Environment must be one of: {allowed_environments}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level setting."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {allowed_levels}")
        return v.upper()
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("SUPPORTED_FORMATS", pre=True)
    def parse_supported_formats(cls, v):
        """Parse supported formats from string or list."""
        if isinstance(v, str):
            return [fmt.strip().lower() for fmt in v.split(",")]
        return [fmt.lower() for fmt in v]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env file


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
