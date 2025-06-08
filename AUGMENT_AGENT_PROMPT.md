# 🤖 **AUGMENT REMOTE AGENT PROMPT: EXA.AI INTEGRATION**

## **📋 AGENT MISSION BRIEFING**

You are an expert AI software engineer tasked with implementing Exa.ai search integration with hallucination detection capabilities into an existing DSPy-Enhanced Fact-Checker API Platform. Your mission is to enhance the current fact-checking system by adding dual search capabilities (Exa.ai + Tavily) following the comprehensive implementation plan already created.

## **🎯 PROJECT OBJECTIVES**

### **Primary Goals**
1. **Integrate Exa.ai Search**: Add Exa.ai neural search alongside existing Tavily search
2. **Implement Hallucination Detection**: Follow Exa.ai's methodology from https://docs.exa.ai/examples/identifying-hallucinations-with-exa
3. **Create Dual Search System**: Build orchestrator for parallel search execution
4. **Enhance Fact-Checking**: Improve accuracy to >95% with cross-verification
5. **Maintain Performance**: Keep response times <5 seconds

### **Success Criteria**
- [ ] All 13 implementation tasks completed successfully
- [ ] >95% fact-checking accuracy achieved
- [ ] >90% hallucination detection accuracy
- [ ] <5 second response time for dual search operations
- [ ] 99.9% uptime with proper error handling
- [ ] Comprehensive test coverage >95%
- [ ] Complete documentation and deployment ready

## **📊 CURRENT SYSTEM ANALYSIS**

### **Existing Architecture**
```
DSPy-Enhanced Fact-Checker API
├── FastAPI REST API with OpenAPI docs
├── Tavily Search Integration (primary search)
├── DSPy Framework for AI optimization
├── Mistral OCR with local fallbacks
├── PostgreSQL database with Redis caching
├── JWT authentication and RBAC
├── Celery background task processing
└── Docker/Kubernetes deployment ready
```

### **Key Files to Understand**
- `app/main.py` - FastAPI application entry point
- `app/core/config.py` - Configuration management
- `app/services/` - Business logic services
- `app/api/v1/endpoints/` - API endpoints
- `requirements.txt` - Current dependencies
- `docker-compose.prod.yml` - Production deployment

## **🏗️ IMPLEMENTATION PLAN**

### **Phase 1: Foundation (Tasks 1.1-1.4)**

#### **Task 1.1: Environment & API Setup**
```python
# Add to requirements.txt
exa-py>=1.0.0

# Add to app/core/config.py
EXA_API_KEY: str = Field(..., env="EXA_API_KEY")
EXA_BASE_URL: str = Field("https://api.exa.ai", env="EXA_BASE_URL")
EXA_RATE_LIMIT_CALLS: int = Field(100, env="EXA_RATE_LIMIT_CALLS")
EXA_RATE_LIMIT_PERIOD: int = Field(60, env="EXA_RATE_LIMIT_PERIOD")
EXA_TIMEOUT: int = Field(30, env="EXA_TIMEOUT")

# Update .env.example
EXA_API_KEY=your_exa_api_key_here
```

#### **Task 1.2: Search Abstraction Layer**
Create `app/core/search/` module with:
- `base_search.py` - Abstract BaseSearchProvider class
- `models.py` - SearchResult, SearchQuery, DualSearchResult models
- `factory.py` - SearchProviderFactory for provider instantiation
- `exceptions.py` - Custom search-related exceptions

#### **Task 1.3: Exa.ai Search Implementation**
Create `app/core/search/exa_search.py`:
```python
from exa_py import Exa
from .base_search import BaseSearchProvider
from .models import SearchQuery, SearchResult

class ExaSearchProvider(BaseSearchProvider):
    def __init__(self, api_key: str):
        self.client = Exa(api_key=api_key)
        self.rate_limiter = RateLimiter(calls=100, period=60)
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        # Implement neural search with error handling
        pass
    
    async def similarity_search(self, query: str, url: str) -> List[SearchResult]:
        # Implement similarity search for hallucination detection
        pass
```

#### **Task 1.4: Tavily Integration Refactor**
Refactor existing Tavily code to use new abstraction layer while maintaining backward compatibility.

### **Phase 2: Core Integration (Tasks 2.1-2.2)**

#### **Task 2.1: Hallucination Detection**
Create `app/core/search/hallucination_detector.py`:
```python
class HallucinationDetector:
    def __init__(self, exa_client: ExaSearchProvider):
        self.exa_client = exa_client
        self.dspy_module = HallucinationCheckModule()
    
    async def detect_hallucination(self, claim: str) -> HallucinationResult:
        # Follow Exa.ai's methodology:
        # 1. Extract key facts from claim
        # 2. Search for supporting evidence
        # 3. Analyze evidence consistency
        # 4. Generate hallucination assessment
        pass
```

#### **Task 2.2: Dual Search Orchestrator**
Create `app/core/search/dual_search.py`:
```python
class DualSearchOrchestrator:
    def __init__(self, exa_provider: ExaSearchProvider, tavily_provider: TavilySearchProvider):
        self.exa_provider = exa_provider
        self.tavily_provider = tavily_provider
    
    async def search(self, query: SearchQuery) -> DualSearchResult:
        # Execute parallel search with fallback handling
        pass
```

### **Phase 3: Enhancement (Tasks 3.1-3.3)**

#### **Task 3.1: Enhanced Fact-Checking Service**
Update `app/services/enhanced_fact_checking_service.py`:
```python
class EnhancedFactCheckingService:
    async def fact_check_with_hallucination_detection(self, claim: str) -> EnhancedFactCheckResult:
        # Integrate dual search and hallucination detection
        pass
```

#### **Task 3.2: API Endpoints Enhancement**
Add `app/api/v1/endpoints/hallucination.py`:
```python
@router.post("/hallucination-check", response_model=HallucinationResult)
async def check_hallucination(request: HallucinationRequest):
    # New endpoint for hallucination detection
    pass
```

#### **Task 3.3: Performance Optimization**
- Implement advanced caching strategies
- Add request deduplication
- Optimize parallel search execution
- Add performance monitoring

### **Phase 4: Testing & Deployment (Tasks 4.1-4.3)**

#### **Task 4.1: Comprehensive Testing**
Create test files:
- `tests/test_exa_search.py`
- `tests/test_hallucination_detection.py`
- `tests/test_dual_search.py`
- `tests/test_enhanced_fact_checking.py`

#### **Task 4.2: Documentation & Deployment**
Update documentation:
- API documentation with new endpoints
- Configuration guide with Exa.ai settings
- Integration guide for developers
- Deployment scripts and monitoring

#### **Task 4.3: Production Deployment**
- Deploy to staging environment
- Run comprehensive tests
- Deploy to production with monitoring

## **🔧 TECHNICAL REQUIREMENTS**

### **Code Quality Standards**
- Follow existing code style (Black, isort, flake8)
- Add comprehensive type hints
- Write detailed docstrings for all functions
- Maintain >95% test coverage
- Follow existing error handling patterns

### **Performance Requirements**
- Response time <5 seconds for dual search
- Parallel execution for search operations
- Implement proper caching strategies
- Add rate limiting and quota management
- Graceful degradation on API failures

### **Security Requirements**
- Secure API key management
- Input validation for all endpoints
- Rate limiting to prevent abuse
- Proper error handling without exposing internals
- Audit logging for search operations

## **📋 IMPLEMENTATION CHECKLIST**

### **Phase 1: Foundation**
- [ ] Add Exa.ai dependencies to requirements.txt
- [ ] Update configuration with Exa.ai settings
- [ ] Create search abstraction layer
- [ ] Implement ExaSearchProvider class
- [ ] Refactor Tavily integration
- [ ] Add comprehensive error handling
- [ ] Write unit tests for new components

### **Phase 2: Core Integration**
- [ ] Implement HallucinationDetector class
- [ ] Create DualSearchOrchestrator
- [ ] Add parallel search execution
- [ ] Implement result aggregation logic
- [ ] Add fallback mechanisms
- [ ] Integrate with DSPy framework
- [ ] Write integration tests

### **Phase 3: Enhancement**
- [ ] Update FactCheckingService with dual search
- [ ] Add new API endpoints
- [ ] Implement cross-verification logic
- [ ] Add performance optimizations
- [ ] Update API documentation
- [ ] Add monitoring and metrics

### **Phase 4: Testing & Deployment**
- [ ] Write comprehensive test suite
- [ ] Add performance and load tests
- [ ] Update all documentation
- [ ] Prepare deployment scripts
- [ ] Deploy to staging and test
- [ ] Deploy to production with monitoring

## **🎯 SPECIFIC INSTRUCTIONS**

### **Code Implementation Guidelines**
1. **Follow Existing Patterns**: Study the current codebase structure and follow established patterns
2. **Maintain Backward Compatibility**: Ensure existing Tavily functionality continues to work
3. **Error Handling**: Implement robust error handling with proper logging
4. **Testing**: Write tests for every new component and function
5. **Documentation**: Update docstrings and API documentation

### **Exa.ai Integration Specifics**
1. **Neural Search**: Use Exa.ai's neural search for semantic understanding
2. **Similarity Search**: Implement similarity search for hallucination detection
3. **Rate Limiting**: Respect Exa.ai's API rate limits
4. **Error Handling**: Handle API failures gracefully with fallback to Tavily
5. **Caching**: Cache Exa.ai results to reduce API calls

### **Hallucination Detection Implementation**
1. **Follow Exa.ai Guide**: Implement exactly as described in their documentation
2. **Key Fact Extraction**: Extract key facts from claims for verification
3. **Evidence Gathering**: Search for supporting evidence using neural search
4. **Consistency Analysis**: Analyze evidence consistency for hallucination detection
5. **Confidence Scoring**: Provide confidence scores for detection results

## **📊 VALIDATION CRITERIA**

### **Functional Testing**
- [ ] All new API endpoints working correctly
- [ ] Dual search returning aggregated results
- [ ] Hallucination detection providing accurate assessments
- [ ] Fallback mechanisms working when APIs fail
- [ ] Existing functionality unchanged

### **Performance Testing**
- [ ] Response times <5 seconds for dual search
- [ ] Parallel search execution working
- [ ] Caching reducing API calls
- [ ] Rate limiting preventing overuse
- [ ] System handling concurrent requests

### **Accuracy Testing**
- [ ] Fact-checking accuracy >95%
- [ ] Hallucination detection accuracy >90%
- [ ] False positive rate <5%
- [ ] Cross-verification improving results
- [ ] Confidence scores meaningful

## **🚀 DEPLOYMENT INSTRUCTIONS**

### **Environment Setup**
1. Add Exa.ai API key to environment variables
2. Update Docker configurations with new dependencies
3. Configure rate limiting and caching settings
4. Set up monitoring for new components

### **Staging Deployment**
1. Deploy to staging environment
2. Run comprehensive test suite
3. Validate all functionality working
4. Performance test with realistic load

### **Production Deployment**
1. Deploy with blue-green strategy
2. Monitor all metrics closely
3. Validate functionality in production
4. Set up alerting for failures

## **📞 SUPPORT & RESOURCES**

### **Documentation References**
- [Exa.ai API Documentation](https://docs.exa.ai/)
- [Exa.ai Hallucination Detection Guide](https://docs.exa.ai/examples/identifying-hallucinations-with-exa)
- [Current Implementation Plan](docs/EXA_INTEGRATION_PLAN.md)
- [Technical Specification](docs/EXA_TECHNICAL_SPEC.md)
- [Task Master Plan](TASKMASTER_EXA_INTEGRATION.md)

### **Existing Codebase**
- Study current Tavily integration patterns
- Follow existing error handling approaches
- Use established configuration management
- Maintain current API response formats
- Follow existing testing patterns

## **💻 DETAILED CODE IMPLEMENTATION GUIDE**

### **Step-by-Step Implementation**

#### **1. Environment Setup**
```bash
# Add to requirements.txt
exa-py>=1.0.0
asyncio-throttle>=1.0.0
```

#### **2. Configuration Updates**
```python
# app/core/config.py - Add these fields to Settings class
class Settings(BaseSettings):
    # ... existing fields ...

    # Exa.ai Configuration
    EXA_API_KEY: str = Field(..., env="EXA_API_KEY")
    EXA_BASE_URL: str = Field("https://api.exa.ai", env="EXA_BASE_URL")
    EXA_RATE_LIMIT_CALLS: int = Field(100, env="EXA_RATE_LIMIT_CALLS")
    EXA_RATE_LIMIT_PERIOD: int = Field(60, env="EXA_RATE_LIMIT_PERIOD")
    EXA_TIMEOUT: int = Field(30, env="EXA_TIMEOUT")
    EXA_MAX_RETRIES: int = Field(3, env="EXA_MAX_RETRIES")

    # Search Configuration
    SEARCH_DEFAULT_PROVIDER: str = Field("dual", env="SEARCH_DEFAULT_PROVIDER")
    SEARCH_PARALLEL_ENABLED: bool = Field(True, env="SEARCH_PARALLEL_ENABLED")
    SEARCH_CACHE_TTL: int = Field(3600, env="SEARCH_CACHE_TTL")
    SEARCH_MAX_RESULTS: int = Field(10, env="SEARCH_MAX_RESULTS")

    # Hallucination Detection
    HALLUCINATION_CONFIDENCE_THRESHOLD: float = Field(0.7, env="HALLUCINATION_CONFIDENCE_THRESHOLD")
    HALLUCINATION_DETECTION_ENABLED: bool = Field(True, env="HALLUCINATION_DETECTION_ENABLED")
```

#### **3. Search Models**
```python
# app/core/search/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class SearchType(str, Enum):
    NEURAL = "neural"
    KEYWORD = "keyword"
    SIMILARITY = "similarity"

class SearchQuery(BaseModel):
    query: str = Field(..., description="Search query text")
    max_results: int = Field(10, description="Maximum number of results")
    search_type: SearchType = Field(SearchType.NEURAL, description="Type of search")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    use_autoprompt: bool = Field(True, description="Use Exa.ai autoprompt")

class SearchResult(BaseModel):
    title: str = Field(..., description="Result title")
    url: str = Field(..., description="Result URL")
    content: str = Field(..., description="Result content")
    score: float = Field(..., description="Relevance score")
    source: str = Field(..., description="Search provider")
    published_date: Optional[str] = Field(None, description="Publication date")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class DualSearchResult(BaseModel):
    query: str = Field(..., description="Original search query")
    exa_results: List[SearchResult] = Field(default_factory=list, description="Exa.ai results")
    tavily_results: List[SearchResult] = Field(default_factory=list, description="Tavily results")
    aggregated_results: List[SearchResult] = Field(default_factory=list, description="Combined results")
    search_strategy: str = Field(..., description="Search strategy used")
    processing_time: float = Field(..., description="Total processing time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Search metadata")

class HallucinationResult(BaseModel):
    claim: str = Field(..., description="Original claim")
    is_hallucination: bool = Field(..., description="Whether claim is hallucination")
    confidence_score: float = Field(..., description="Confidence in assessment")
    evidence: List[SearchResult] = Field(default_factory=list, description="Supporting evidence")
    key_facts: List[str] = Field(default_factory=list, description="Extracted key facts")
    analysis: str = Field(..., description="Detailed analysis")
    processing_time: float = Field(..., description="Processing time")
```

#### **4. Base Search Provider**
```python
# app/core/search/base_search.py
from abc import ABC, abstractmethod
from typing import List
from .models import SearchQuery, SearchResult

class BaseSearchProvider(ABC):
    """Abstract base class for search providers"""

    @abstractmethod
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Execute search and return results"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if search provider is healthy"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name"""
        pass
```

#### **5. Exa.ai Search Provider Implementation**
```python
# app/core/search/exa_search.py
import asyncio
import time
from typing import List
from exa_py import Exa
from asyncio_throttle import Throttler
from .base_search import BaseSearchProvider
from .models import SearchQuery, SearchResult, SearchType
from .exceptions import SearchProviderError
from app.core.config import get_settings

class ExaSearchProvider(BaseSearchProvider):
    def __init__(self, api_key: str):
        self.client = Exa(api_key=api_key)
        self.settings = get_settings()
        self.throttler = Throttler(
            rate_limit=self.settings.EXA_RATE_LIMIT_CALLS,
            period=self.settings.EXA_RATE_LIMIT_PERIOD
        )

    @property
    def provider_name(self) -> str:
        return "exa"

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Execute Exa.ai search"""
        async with self.throttler:
            try:
                start_time = time.time()

                if query.search_type == SearchType.NEURAL:
                    results = await self._neural_search(query)
                elif query.search_type == SearchType.SIMILARITY:
                    results = await self._similarity_search(query)
                else:
                    results = await self._keyword_search(query)

                processing_time = time.time() - start_time
                return [self._parse_result(r, processing_time) for r in results.results]

            except Exception as e:
                logger.error(f"Exa search failed: {e}")
                raise SearchProviderError(f"Exa search failed: {e}")

    async def _neural_search(self, query: SearchQuery):
        """Execute neural search using Exa.ai"""
        return await asyncio.to_thread(
            self.client.search_and_contents,
            query.query,
            num_results=query.max_results,
            use_autoprompt=query.use_autoprompt,
            text=True,
            highlights=True
        )

    async def _similarity_search(self, query: SearchQuery):
        """Execute similarity search for hallucination detection"""
        # Implementation for similarity search
        pass

    def _parse_result(self, result, processing_time: float) -> SearchResult:
        """Parse Exa.ai result into SearchResult model"""
        return SearchResult(
            title=result.title or "",
            url=result.url,
            content=result.text or "",
            score=result.score or 0.0,
            source="exa",
            published_date=getattr(result, 'published_date', None),
            metadata={
                "highlights": getattr(result, 'highlights', []),
                "processing_time": processing_time
            }
        )

    async def health_check(self) -> bool:
        """Check Exa.ai API health"""
        try:
            test_query = SearchQuery(query="test", max_results=1)
            await self.search(test_query)
            return True
        except Exception:
            return False
```

#### **6. Hallucination Detection Implementation**
```python
# app/core/search/hallucination_detector.py
import time
from typing import List
from .exa_search import ExaSearchProvider
from .models import SearchQuery, HallucinationResult, SearchType
from app.core.dspy_modules.specialized import HallucinationCheckModule

class HallucinationDetector:
    def __init__(self, exa_client: ExaSearchProvider, confidence_threshold: float = 0.7):
        self.exa_client = exa_client
        self.confidence_threshold = confidence_threshold
        self.dspy_module = HallucinationCheckModule()

    async def detect_hallucination(self, claim: str, context: str = None) -> HallucinationResult:
        """
        Detect hallucinations using Exa.ai's methodology
        Following: https://docs.exa.ai/examples/identifying-hallucinations-with-exa
        """
        start_time = time.time()

        try:
            # Step 1: Extract key facts from claim
            key_facts = await self._extract_key_facts(claim)

            # Step 2: Search for supporting evidence using neural search
            evidence_results = []
            for fact in key_facts:
                search_query = SearchQuery(
                    query=fact,
                    search_type=SearchType.NEURAL,
                    max_results=5,
                    use_autoprompt=True
                )
                results = await self.exa_client.search(search_query)
                evidence_results.extend(results)

            # Step 3: Analyze evidence consistency
            consistency_score = await self._analyze_consistency(claim, evidence_results)

            # Step 4: Generate hallucination assessment
            is_hallucination = consistency_score < self.confidence_threshold
            analysis = await self._generate_analysis(claim, evidence_results, consistency_score)

            processing_time = time.time() - start_time

            return HallucinationResult(
                claim=claim,
                is_hallucination=is_hallucination,
                confidence_score=consistency_score,
                evidence=evidence_results,
                key_facts=key_facts,
                analysis=analysis,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Hallucination detection failed: {e}")
            raise SearchProviderError(f"Hallucination detection failed: {e}")

    async def _extract_key_facts(self, claim: str) -> List[str]:
        """Extract key facts from claim for verification"""
        # Use DSPy module to extract key facts
        return await self.dspy_module.extract_key_facts(claim)

    async def _analyze_consistency(self, claim: str, evidence: List[SearchResult]) -> float:
        """Analyze consistency between claim and evidence"""
        # Implement consistency analysis logic
        return await self.dspy_module.analyze_consistency(claim, evidence)

    async def _generate_analysis(self, claim: str, evidence: List[SearchResult], score: float) -> str:
        """Generate detailed analysis of hallucination assessment"""
        return await self.dspy_module.generate_analysis(claim, evidence, score)
```

## **🔍 TESTING REQUIREMENTS**

### **Unit Tests Example**
```python
# tests/test_exa_search.py
import pytest
from app.core.search.exa_search import ExaSearchProvider
from app.core.search.models import SearchQuery, SearchType

@pytest.mark.asyncio
async def test_exa_neural_search():
    provider = ExaSearchProvider(api_key="test_key")
    query = SearchQuery(
        query="artificial intelligence",
        search_type=SearchType.NEURAL,
        max_results=5
    )
    results = await provider.search(query)
    assert len(results) <= 5
    assert all(result.source == "exa" for result in results)

@pytest.mark.asyncio
async def test_hallucination_detection():
    # Test hallucination detection with known examples
    pass
```

## **📊 MONITORING & METRICS**

### **Add Monitoring**
```python
# app/monitoring/search_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Metrics for search operations
search_requests_total = Counter('search_requests_total', 'Total search requests', ['provider', 'type'])
search_duration_seconds = Histogram('search_duration_seconds', 'Search duration', ['provider'])
search_errors_total = Counter('search_errors_total', 'Search errors', ['provider', 'error_type'])
hallucination_detections_total = Counter('hallucination_detections_total', 'Hallucination detections', ['result'])
```

---

**🎯 MISSION SUMMARY**: Implement Exa.ai search integration with hallucination detection following the comprehensive plan, maintaining high code quality, performance, and backward compatibility while enhancing the fact-checking system's accuracy and capabilities.**
