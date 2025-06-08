"""
Tests for Exa.ai integration components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from app.core.search.models import SearchQuery, SearchResult, SearchType
from app.core.search.exa_search import ExaSearchProvider
from app.core.search.tavily_search import TavilySearchProvider
from app.core.search.dual_search import DualSearchOrchestrator
from app.core.search.hallucination_detector import HallucinationDetector
from app.core.search.exceptions import SearchProviderError, SearchConfigurationError
from app.services.exa_fact_checking_service import ExaFactCheckingService


class TestSearchModels:
    """Test search models and data structures."""
    
    def test_search_query_creation(self):
        """Test SearchQuery model creation."""
        query = SearchQuery(
            query="test query",
            max_results=5,
            search_type=SearchType.NEURAL
        )
        
        assert query.query == "test query"
        assert query.max_results == 5
        assert query.search_type == SearchType.NEURAL
        assert query.use_autoprompt is True
    
    def test_search_result_creation(self):
        """Test SearchResult model creation."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            content="Test content",
            score=0.95,
            source="exa"
        )
        
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.content == "Test content"
        assert result.score == 0.95
        assert result.source == "exa"


class TestExaSearchProvider:
    """Test Exa.ai search provider."""
    
    def test_initialization_without_api_key(self):
        """Test that initialization fails without API key."""
        with patch('app.core.search.exa_search.get_settings') as mock_settings:
            mock_settings.return_value.EXA_API_KEY = None
            
            with pytest.raises(SearchConfigurationError):
                ExaSearchProvider()
    
    @patch('app.core.search.exa_search.Exa')
    def test_initialization_with_api_key(self, mock_exa):
        """Test successful initialization with API key."""
        with patch('app.core.search.exa_search.get_settings') as mock_settings:
            mock_settings.return_value.EXA_API_KEY = "test_key"
            mock_settings.return_value.EXA_TIMEOUT = 30
            mock_settings.return_value.EXA_MAX_RETRIES = 3
            mock_settings.return_value.EXA_RATE_LIMIT_CALLS = 100
            mock_settings.return_value.EXA_RATE_LIMIT_PERIOD = 60
            
            provider = ExaSearchProvider("test_key")
            
            assert provider.api_key == "test_key"
            assert provider.name == "exa"
            mock_exa.assert_called_once_with(api_key="test_key")
    
    @patch('app.core.search.exa_search.Exa')
    @pytest.mark.asyncio
    async def test_search_neural(self, mock_exa):
        """Test neural search functionality."""
        # Mock Exa client
        mock_client = Mock()
        mock_exa.return_value = mock_client
        
        # Mock search results
        mock_result = Mock()
        mock_result.title = "Test Title"
        mock_result.url = "https://example.com"
        mock_result.text = "Test content"
        mock_result.score = 0.95
        mock_result.highlights = ["highlight1", "highlight2"]
        
        mock_response = Mock()
        mock_response.results = [mock_result]
        mock_client.search_and_contents.return_value = mock_response
        
        with patch('app.core.search.exa_search.get_settings') as mock_settings:
            mock_settings.return_value.EXA_API_KEY = "test_key"
            mock_settings.return_value.EXA_TIMEOUT = 30
            mock_settings.return_value.EXA_MAX_RETRIES = 3
            mock_settings.return_value.EXA_RATE_LIMIT_CALLS = 100
            mock_settings.return_value.EXA_RATE_LIMIT_PERIOD = 60
            
            provider = ExaSearchProvider("test_key")
            
            query = SearchQuery(
                query="test query",
                search_type=SearchType.NEURAL,
                max_results=5
            )
            
            with patch('asyncio.to_thread', return_value=mock_response):
                results = await provider.search(query)
            
            assert len(results) == 1
            assert results[0].title == "Test Title"
            assert results[0].url == "https://example.com"
            assert results[0].content == "Test content"
            assert results[0].score == 0.95
            assert results[0].source == "exa"


class TestTavilySearchProvider:
    """Test Tavily search provider."""
    
    def test_initialization_without_api_key(self):
        """Test that initialization fails without API key."""
        with patch('app.core.search.tavily_search.get_settings') as mock_settings:
            mock_settings.return_value.TAVILY_API_KEY = None
            
            with pytest.raises(SearchConfigurationError):
                TavilySearchProvider()
    
    @patch('app.core.search.tavily_search.TavilyClient')
    def test_initialization_with_api_key(self, mock_tavily):
        """Test successful initialization with API key."""
        with patch('app.core.search.tavily_search.get_settings') as mock_settings:
            mock_settings.return_value.TAVILY_API_KEY = "test_key"
            
            provider = TavilySearchProvider("test_key")
            
            assert provider.api_key == "test_key"
            assert provider.name == "tavily"
            mock_tavily.assert_called_once_with(api_key="test_key")


class TestDualSearchOrchestrator:
    """Test dual search orchestrator."""
    
    @pytest.fixture
    def mock_providers(self):
        """Create mock search providers."""
        exa_provider = Mock(spec=ExaSearchProvider)
        exa_provider.name = "exa"
        exa_provider.search_with_retry = AsyncMock()
        exa_provider.get_status = AsyncMock()
        exa_provider.reset_metrics = Mock()
        
        tavily_provider = Mock(spec=TavilySearchProvider)
        tavily_provider.name = "tavily"
        tavily_provider.search_with_retry = AsyncMock()
        tavily_provider.get_status = AsyncMock()
        tavily_provider.reset_metrics = Mock()
        
        return exa_provider, tavily_provider
    
    def test_initialization(self, mock_providers):
        """Test orchestrator initialization."""
        exa_provider, tavily_provider = mock_providers
        
        orchestrator = DualSearchOrchestrator(exa_provider, tavily_provider)
        
        assert orchestrator.exa_provider == exa_provider
        assert orchestrator.tavily_provider == tavily_provider
    
    @pytest.mark.asyncio
    async def test_parallel_search_success(self, mock_providers):
        """Test successful parallel search."""
        exa_provider, tavily_provider = mock_providers
        
        # Mock search results
        exa_results = [
            SearchResult(
                title="Exa Result",
                url="https://exa.example.com",
                content="Exa content",
                score=0.9,
                source="exa"
            )
        ]
        
        tavily_results = [
            SearchResult(
                title="Tavily Result",
                url="https://tavily.example.com",
                content="Tavily content",
                score=0.8,
                source="tavily"
            )
        ]
        
        exa_provider.search_with_retry.return_value = exa_results
        tavily_provider.search_with_retry.return_value = tavily_results
        
        with patch('app.core.search.dual_search.get_settings') as mock_settings:
            mock_settings.return_value.DUAL_SEARCH_TIMEOUT = 10
            mock_settings.return_value.SEARCH_RESULT_AGGREGATION = True
            mock_settings.return_value.SEARCH_MAX_RESULTS = 10
            
            orchestrator = DualSearchOrchestrator(exa_provider, tavily_provider)
            
            query = SearchQuery(query="test query", max_results=10)
            result = await orchestrator.search(query, strategy="parallel")
            
            assert result.query == "test query"
            assert len(result.exa_results) == 1
            assert len(result.tavily_results) == 1
            assert result.exa_success is True
            assert result.tavily_success is True
            assert result.search_strategy == "parallel"


class TestHallucinationDetector:
    """Test hallucination detector."""
    
    @pytest.fixture
    def mock_exa_provider(self):
        """Create mock Exa provider for hallucination detection."""
        provider = Mock(spec=ExaSearchProvider)
        provider.search = AsyncMock()
        return provider
    
    def test_initialization(self, mock_exa_provider):
        """Test hallucination detector initialization."""
        with patch('app.core.search.hallucination_detector.get_settings') as mock_settings:
            mock_settings.return_value.HALLUCINATION_CONFIDENCE_THRESHOLD = 0.7
            
            detector = HallucinationDetector(mock_exa_provider, 0.8)
            
            assert detector.exa_client == mock_exa_provider
            assert detector.confidence_threshold == 0.8
    
    @pytest.mark.asyncio
    async def test_key_fact_extraction(self, mock_exa_provider):
        """Test key fact extraction from claims."""
        with patch('app.core.search.hallucination_detector.get_settings') as mock_settings:
            mock_settings.return_value.HALLUCINATION_CONFIDENCE_THRESHOLD = 0.7
            
            detector = HallucinationDetector(mock_exa_provider)
            
            claim = "John Smith founded Microsoft in 1975 and made $1 billion."
            facts = await detector._extract_key_facts(claim)
            
            assert len(facts) > 0
            # Should extract person, organization, date, and statistic
            fact_types = [fact.split(':')[0] for fact in facts if ':' in fact]
            assert any('person' in fact_type for fact_type in fact_types)


class TestExaFactCheckingService:
    """Test Exa.ai fact-checking service."""
    
    def test_initialization(self):
        """Test service initialization."""
        service = ExaFactCheckingService()
        
        assert service.exa_provider is None
        assert service.tavily_provider is None
        assert service.dual_orchestrator is None
        assert service.hallucination_detector is None
    
    @pytest.mark.asyncio
    async def test_service_stats(self):
        """Test service statistics retrieval."""
        service = ExaFactCheckingService()
        
        stats = await service.get_service_stats()
        
        assert "fact_checks_performed" in stats
        assert "successful_fact_checks" in stats
        assert "success_rate" in stats
        assert "average_processing_time" in stats


# Integration test (requires actual API keys - skip in CI)
@pytest.mark.skip(reason="Requires actual API keys")
class TestRealIntegration:
    """Integration tests with real APIs (requires API keys)."""
    
    @pytest.mark.asyncio
    async def test_real_exa_search(self):
        """Test real Exa.ai search (requires API key)."""
        import os
        
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            pytest.skip("EXA_API_KEY not set")
        
        provider = ExaSearchProvider(api_key)
        query = SearchQuery(
            query="artificial intelligence",
            search_type=SearchType.NEURAL,
            max_results=3
        )
        
        results = await provider.search(query)
        
        assert len(results) <= 3
        assert all(result.source == "exa" for result in results)
        assert all(result.score >= 0 for result in results)
    
    @pytest.mark.asyncio
    async def test_real_hallucination_detection(self):
        """Test real hallucination detection (requires API key)."""
        import os
        
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            pytest.skip("EXA_API_KEY not set")
        
        provider = ExaSearchProvider(api_key)
        detector = HallucinationDetector(provider)
        
        # Test with a likely true claim
        true_claim = "The Earth orbits around the Sun."
        result = await detector.detect_hallucination(true_claim)
        
        assert result.claim == true_claim
        assert isinstance(result.is_hallucination, bool)
        assert 0 <= result.confidence_score <= 1
        assert len(result.key_facts) > 0
