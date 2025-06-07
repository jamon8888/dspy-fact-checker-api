"""
Context7 MCP server integration for enhanced context management.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid

from app.core.config import get_settings

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    logger.warning("httpx not available for context7 integration")
    HTTPX_AVAILABLE = False


class Context7Error(Exception):
    """Base exception for Context7 errors."""
    pass


class Context7ConfigurationError(Context7Error):
    """Configuration error for Context7."""
    pass


class Context7ConnectionError(Context7Error):
    """Connection error for Context7."""
    pass


class Context7ProcessingError(Context7Error):
    """Processing error for Context7."""
    pass


class Context7Integration:
    """
    Integration with context7 MCP server for enhanced context management.
    
    Context7 provides:
    - Intelligent context extraction and management
    - Document relationship mapping
    - Semantic search capabilities
    - Context-aware fact-checking support
    - Multi-document analysis
    """
    
    def __init__(self, server_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize Context7 integration."""
        if not HTTPX_AVAILABLE:
            raise Context7ConfigurationError(
                "httpx is required for Context7 integration. Please install httpx>=0.24.0"
            )
        
        self.settings = get_settings()
        self.server_url = server_url or self.settings.CONTEXT7_SERVER_URL or "http://localhost:3000"
        self.api_key = api_key or self.settings.CONTEXT7_API_KEY
        
        # Configuration
        self.timeout = 30.0
        self.max_retries = 3
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "DSPy-FactChecker/1.0"
            }
        )
        
        if self.api_key:
            self.client.headers["Authorization"] = f"Bearer {self.api_key}"
        
        logger.info(f"Context7 integration initialized with server: {self.server_url}")
    
    async def store_document_context(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any],
        document_type: str = "document",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Store document context in Context7.
        
        Args:
            document_id: Unique document identifier
            content: Document content (text)
            metadata: Document metadata
            document_type: Type of document
            **kwargs: Additional context data
            
        Returns:
            Context storage result
        """
        try:
            context_data = {
                "id": document_id,
                "type": document_type,
                "content": content,
                "metadata": {
                    **metadata,
                    "stored_at": datetime.now().isoformat(),
                    "source": "dspy-fact-checker"
                },
                "embeddings": kwargs.get("embeddings"),
                "tags": kwargs.get("tags", []),
                "relationships": kwargs.get("relationships", [])
            }
            
            response = await self._make_request(
                "POST",
                "/api/v1/context/store",
                data=context_data
            )
            
            logger.info(f"Document context stored successfully: {document_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to store document context: {e}")
            raise Context7ProcessingError(f"Failed to store context: {str(e)}")
    
    async def retrieve_document_context(
        self,
        document_id: str,
        include_relationships: bool = True,
        include_embeddings: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve document context from Context7.
        
        Args:
            document_id: Document identifier
            include_relationships: Whether to include related documents
            include_embeddings: Whether to include embeddings
            
        Returns:
            Document context or None if not found
        """
        try:
            params = {
                "include_relationships": include_relationships,
                "include_embeddings": include_embeddings
            }
            
            response = await self._make_request(
                "GET",
                f"/api/v1/context/{document_id}",
                params=params
            )
            
            return response
            
        except Exception as e:
            if "404" in str(e):
                return None
            logger.error(f"Failed to retrieve document context: {e}")
            raise Context7ProcessingError(f"Failed to retrieve context: {str(e)}")
    
    async def search_context(
        self,
        query: str,
        document_types: Optional[List[str]] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant context using semantic search.
        
        Args:
            query: Search query
            document_types: Filter by document types
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            **kwargs: Additional search parameters
            
        Returns:
            List of relevant context items
        """
        try:
            search_data = {
                "query": query,
                "document_types": document_types,
                "limit": limit,
                "similarity_threshold": similarity_threshold,
                "include_metadata": kwargs.get("include_metadata", True),
                "include_content": kwargs.get("include_content", True),
                "filters": kwargs.get("filters", {})
            }
            
            response = await self._make_request(
                "POST",
                "/api/v1/context/search",
                data=search_data
            )
            
            return response.get("results", [])
            
        except Exception as e:
            logger.error(f"Failed to search context: {e}")
            raise Context7ProcessingError(f"Failed to search context: {str(e)}")
    
    async def analyze_document_relationships(
        self,
        document_id: str,
        analysis_type: str = "semantic",
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Analyze relationships between documents.
        
        Args:
            document_id: Primary document identifier
            analysis_type: Type of analysis (semantic, temporal, topical)
            depth: Analysis depth (number of relationship levels)
            
        Returns:
            Relationship analysis results
        """
        try:
            analysis_data = {
                "document_id": document_id,
                "analysis_type": analysis_type,
                "depth": depth,
                "include_scores": True,
                "include_paths": True
            }
            
            response = await self._make_request(
                "POST",
                "/api/v1/context/analyze-relationships",
                data=analysis_data
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to analyze document relationships: {e}")
            raise Context7ProcessingError(f"Failed to analyze relationships: {str(e)}")
    
    async def extract_context_for_fact_checking(
        self,
        claim: str,
        document_context: Optional[Dict[str, Any]] = None,
        search_related: bool = True,
        max_context_items: int = 5
    ) -> Dict[str, Any]:
        """
        Extract relevant context for fact-checking a specific claim.
        
        Args:
            claim: Claim to fact-check
            document_context: Source document context
            search_related: Whether to search for related context
            max_context_items: Maximum context items to return
            
        Returns:
            Relevant context for fact-checking
        """
        try:
            extraction_data = {
                "claim": claim,
                "document_context": document_context,
                "search_related": search_related,
                "max_context_items": max_context_items,
                "analysis_types": ["semantic", "factual", "temporal"],
                "include_confidence_scores": True
            }
            
            response = await self._make_request(
                "POST",
                "/api/v1/context/extract-for-fact-checking",
                data=extraction_data
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to extract context for fact-checking: {e}")
            raise Context7ProcessingError(f"Failed to extract fact-checking context: {str(e)}")
    
    async def update_document_context(
        self,
        document_id: str,
        updates: Dict[str, Any],
        merge_strategy: str = "merge"
    ) -> Dict[str, Any]:
        """
        Update existing document context.
        
        Args:
            document_id: Document identifier
            updates: Context updates
            merge_strategy: How to merge updates (merge, replace, append)
            
        Returns:
            Update result
        """
        try:
            update_data = {
                "updates": updates,
                "merge_strategy": merge_strategy,
                "updated_at": datetime.now().isoformat()
            }
            
            response = await self._make_request(
                "PATCH",
                f"/api/v1/context/{document_id}",
                data=update_data
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to update document context: {e}")
            raise Context7ProcessingError(f"Failed to update context: {str(e)}")
    
    async def delete_document_context(self, document_id: str) -> bool:
        """
        Delete document context from Context7.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            await self._make_request(
                "DELETE",
                f"/api/v1/context/{document_id}"
            )
            
            logger.info(f"Document context deleted successfully: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document context: {e}")
            return False
    
    async def get_context_statistics(self) -> Dict[str, Any]:
        """
        Get Context7 statistics and health information.
        
        Returns:
            Context7 statistics
        """
        try:
            response = await self._make_request(
                "GET",
                "/api/v1/context/statistics"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to get context statistics: {e}")
            raise Context7ProcessingError(f"Failed to get statistics: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        Check if Context7 server is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self._make_request(
                "GET",
                "/health",
                timeout=5.0
            )
            
            return response.get("status") == "healthy"
            
        except Exception as e:
            logger.warning(f"Context7 health check failed: {e}")
            return False
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Context7 server."""
        url = f"{self.server_url.rstrip('/')}{endpoint}"
        
        request_kwargs = {
            "method": method,
            "url": url,
            "timeout": timeout or self.timeout
        }
        
        if data:
            request_kwargs["json"] = data
        
        if params:
            request_kwargs["params"] = params
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(**request_kwargs)
                response.raise_for_status()
                
                # Handle empty responses
                if not response.content:
                    return {}
                
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise Context7ProcessingError(f"Not found: {endpoint}")
                elif e.response.status_code == 401:
                    raise Context7ConfigurationError("Authentication failed - check API key")
                elif e.response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise Context7ProcessingError("Rate limit exceeded")
                else:
                    raise Context7ProcessingError(f"HTTP {e.response.status_code}: {e.response.text}")
                    
            except httpx.ConnectError:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise Context7ConnectionError(f"Failed to connect to Context7 server: {self.server_url}")
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise Context7ProcessingError(f"Request failed: {str(e)}")
        
        raise Context7ProcessingError("Max retries exceeded")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
