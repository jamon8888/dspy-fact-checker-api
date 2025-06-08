#!/usr/bin/env python3
"""
Script to create GitHub issues for Exa.ai integration project
Run this script to automatically create all project issues in GitHub
"""

import json
from typing import List, Dict

# GitHub Issues Configuration
GITHUB_ISSUES = [
    {
        "title": "🔧 [Phase 1.1] Environment & API Setup for Exa.ai Integration",
        "body": """## 📋 Task Description
Set up Exa.ai API integration and environment configuration.

## 🎯 Objectives
- Configure Exa.ai API access
- Update environment configuration
- Add required dependencies
- Test basic API connectivity

## 📝 Subtasks
- [ ] Obtain Exa.ai API key and set up account
- [ ] Add `EXA_API_KEY` to environment configuration
- [ ] Update `.env.example` with Exa.ai settings
- [ ] Add `exa-py` SDK to `requirements.txt`
- [ ] Test basic API connectivity

## ✅ Acceptance Criteria
- [ ] Exa.ai API key configured and working
- [ ] Environment variables properly set
- [ ] Basic API connection test passes
- [ ] Dependencies installed and working

## 📊 Details
- **Priority**: Critical
- **Estimated Time**: 1 day
- **Phase**: 1 - Foundation
- **Dependencies**: None

## 🔗 Related Documentation
- [Exa.ai API Documentation](https://docs.exa.ai/)
- [Integration Plan](docs/EXA_INTEGRATION_PLAN.md)
- [Technical Specification](docs/EXA_TECHNICAL_SPEC.md)
""",
        "labels": ["enhancement", "phase-1", "critical", "exa-integration"],
        "milestone": "Phase 1: Foundation"
    },
    
    {
        "title": "🏗️ [Phase 1.2] Create Search Abstraction Layer",
        "body": """## 📋 Task Description
Create a unified search abstraction layer to support multiple search providers.

## 🎯 Objectives
- Design abstract search interface
- Create search result models
- Implement provider factory pattern
- Add configuration management

## 📝 Subtasks
- [ ] Create `app/core/search/` module structure
- [ ] Implement `BaseSearchProvider` abstract class
- [ ] Create `SearchResult` and `SearchQuery` models
- [ ] Implement search provider factory pattern
- [ ] Add search configuration management

## ✅ Acceptance Criteria
- [ ] Abstract search interface defined
- [ ] Search result models implemented
- [ ] Provider factory working
- [ ] Configuration system in place
- [ ] Unit tests for abstraction layer

## 📊 Details
- **Priority**: Critical
- **Estimated Time**: 2 days
- **Phase**: 1 - Foundation
- **Dependencies**: Task 1.1

## 🔗 Related Files
- `app/core/search/base_search.py`
- `app/core/search/models.py`
- `app/core/search/factory.py`
""",
        "labels": ["enhancement", "phase-1", "critical", "architecture"],
        "milestone": "Phase 1: Foundation"
    },
    
    {
        "title": "🔍 [Phase 1.3] Implement Exa.ai Search Provider",
        "body": """## 📋 Task Description
Implement Exa.ai search provider with neural search capabilities.

## 🎯 Objectives
- Create ExaSearchProvider class
- Implement neural search functionality
- Add error handling and rate limiting
- Create result parsing logic

## 📝 Subtasks
- [ ] Create `ExaSearchProvider` class
- [ ] Implement basic neural search functionality
- [ ] Add error handling and rate limiting
- [ ] Create search result parsing logic
- [ ] Add basic caching mechanism
- [ ] Implement similarity search
- [ ] Add keyword search fallback

## ✅ Acceptance Criteria
- [ ] Exa.ai search provider working
- [ ] Neural search functionality implemented
- [ ] Error handling in place
- [ ] Results properly parsed and cached
- [ ] Rate limiting functional
- [ ] Unit tests passing

## 📊 Details
- **Priority**: High
- **Estimated Time**: 2 days
- **Phase**: 1 - Foundation
- **Dependencies**: Task 1.2

## 🔗 Related Files
- `app/core/search/exa_search.py`
- `tests/test_exa_search.py`
""",
        "labels": ["enhancement", "phase-1", "high", "exa-integration"],
        "milestone": "Phase 1: Foundation"
    },
    
    {
        "title": "🔄 [Phase 1.4] Refactor Tavily Integration",
        "body": """## 📋 Task Description
Refactor existing Tavily search to use new abstraction layer.

## 🎯 Objectives
- Integrate Tavily with new search abstraction
- Maintain backward compatibility
- Ensure all existing functionality works
- Update tests

## 📝 Subtasks
- [ ] Refactor existing Tavily code to use new abstraction
- [ ] Create `TavilySearchProvider` class
- [ ] Ensure backward compatibility
- [ ] Update existing tests
- [ ] Verify all endpoints still work

## ✅ Acceptance Criteria
- [ ] Tavily integrated with new abstraction
- [ ] Backward compatibility maintained
- [ ] All existing tests pass
- [ ] No regression in functionality

## 📊 Details
- **Priority**: Medium
- **Estimated Time**: 1 day
- **Phase**: 1 - Foundation
- **Dependencies**: Task 1.2

## 🔗 Related Files
- `app/core/search/tavily_search.py`
- `tests/test_tavily_search.py`
""",
        "labels": ["refactor", "phase-1", "medium", "tavily"],
        "milestone": "Phase 1: Foundation"
    },
    
    {
        "title": "🧠 [Phase 2.1] Implement Hallucination Detection",
        "body": """## 📋 Task Description
Implement Exa.ai's hallucination detection methodology for claim validation.

## 🎯 Objectives
- Study Exa.ai hallucination detection approach
- Implement HallucinationDetector class
- Create claim validation logic
- Integrate with DSPy framework

## 📝 Subtasks
- [ ] Study Exa.ai hallucination detection methodology
- [ ] Implement `HallucinationDetector` class
- [ ] Create claim validation logic
- [ ] Add confidence scoring for hallucination detection
- [ ] Integrate with DSPy framework
- [ ] Create key fact extraction logic
- [ ] Implement evidence consistency analysis

## ✅ Acceptance Criteria
- [ ] Hallucination detection working
- [ ] Confidence scoring implemented
- [ ] DSPy integration complete
- [ ] Validation logic functional
- [ ] Accuracy >90% on test dataset

## 📊 Details
- **Priority**: Critical
- **Estimated Time**: 3 days
- **Phase**: 2 - Core Integration
- **Dependencies**: Task 1.3

## 🔗 Related Files
- `app/core/search/hallucination_detector.py`
- `tests/test_hallucination_detection.py`
""",
        "labels": ["enhancement", "phase-2", "critical", "ai-ml", "hallucination"],
        "milestone": "Phase 2: Core Integration"
    },
    
    {
        "title": "🔀 [Phase 2.2] Create Dual Search Orchestrator",
        "body": """## 📋 Task Description
Create orchestrator to manage dual search across Exa.ai and Tavily providers.

## 🎯 Objectives
- Implement parallel search execution
- Create result aggregation logic
- Add intelligent search routing
- Implement fallback mechanisms

## 📝 Subtasks
- [ ] Create `DualSearchOrchestrator` class
- [ ] Implement parallel search execution
- [ ] Add result aggregation logic
- [ ] Create intelligent search routing
- [ ] Add fallback mechanisms
- [ ] Implement search strategy selection
- [ ] Add performance monitoring

## ✅ Acceptance Criteria
- [ ] Dual search orchestrator working
- [ ] Parallel execution implemented
- [ ] Result aggregation functional
- [ ] Fallback mechanisms in place
- [ ] Response time <5 seconds

## 📊 Details
- **Priority**: High
- **Estimated Time**: 2 days
- **Phase**: 2 - Core Integration
- **Dependencies**: Task 1.3, Task 1.4

## 🔗 Related Files
- `app/core/search/dual_search.py`
- `tests/test_dual_search.py`
""",
        "labels": ["enhancement", "phase-2", "high", "orchestration"],
        "milestone": "Phase 2: Core Integration"
    },
    
    {
        "title": "🚀 [Phase 3.1] Enhance Fact-Checking Service",
        "body": """## 📋 Task Description
Enhance existing fact-checking service with dual search and hallucination detection.

## 🎯 Objectives
- Integrate dual search into fact-checking
- Add cross-verification logic
- Enhance confidence scoring
- Update API response models

## 📝 Subtasks
- [ ] Update `FactCheckingService` with dual search
- [ ] Implement cross-verification logic
- [ ] Enhance confidence scoring algorithms
- [ ] Add result comparison and ranking
- [ ] Update API response models
- [ ] Add enhanced fact-checking endpoint

## ✅ Acceptance Criteria
- [ ] Fact-checking service enhanced
- [ ] Cross-verification working
- [ ] Improved confidence scoring
- [ ] API responses updated
- [ ] Accuracy improvement >10%

## 📊 Details
- **Priority**: High
- **Estimated Time**: 2 days
- **Phase**: 3 - Enhancement
- **Dependencies**: Task 2.1, Task 2.2

## 🔗 Related Files
- `app/services/enhanced_fact_checking_service.py`
- `app/api/v1/endpoints/enhanced_fact_checking.py`
""",
        "labels": ["enhancement", "phase-3", "high", "fact-checking"],
        "milestone": "Phase 3: Enhancement"
    },
    
    {
        "title": "🌐 [Phase 3.2] Enhance API Endpoints",
        "body": """## 📋 Task Description
Add new API endpoints and enhance existing ones with dual search capabilities.

## 🎯 Objectives
- Add hallucination detection endpoint
- Update existing fact-check endpoints
- Add search provider selection
- Update API documentation

## 📝 Subtasks
- [ ] Add new `/api/v1/hallucination-check` endpoint
- [ ] Update existing fact-check endpoints
- [ ] Add search provider selection options
- [ ] Implement result comparison endpoints
- [ ] Update OpenAPI documentation
- [ ] Add API versioning support

## ✅ Acceptance Criteria
- [ ] New API endpoints working
- [ ] Existing endpoints enhanced
- [ ] Provider selection implemented
- [ ] Documentation updated
- [ ] All endpoints tested

## 📊 Details
- **Priority**: Medium
- **Estimated Time**: 2 days
- **Phase**: 3 - Enhancement
- **Dependencies**: Task 3.1

## 🔗 Related Files
- `app/api/v1/endpoints/hallucination.py`
- `docs/API_DOCUMENTATION.md`
""",
        "labels": ["enhancement", "phase-3", "medium", "api"],
        "milestone": "Phase 3: Enhancement"
    },
    
    {
        "title": "⚡ [Phase 3.3] Performance Optimization",
        "body": """## 📋 Task Description
Optimize performance for dual search operations and caching strategies.

## 🎯 Objectives
- Optimize parallel search execution
- Implement advanced caching
- Add request deduplication
- Add performance monitoring

## 📝 Subtasks
- [ ] Optimize parallel search execution
- [ ] Implement advanced caching strategies
- [ ] Add request deduplication
- [ ] Optimize database queries
- [ ] Add performance monitoring
- [ ] Implement connection pooling
- [ ] Add response compression

## ✅ Acceptance Criteria
- [ ] Response times <5 seconds
- [ ] Caching optimized
- [ ] Performance monitoring in place
- [ ] Database queries optimized
- [ ] Cache hit rate >80%

## 📊 Details
- **Priority**: Medium
- **Estimated Time**: 1 day
- **Phase**: 3 - Enhancement
- **Dependencies**: Task 3.1

## 🔗 Related Files
- `app/core/cache.py`
- `app/monitoring/performance.py`
""",
        "labels": ["optimization", "phase-3", "medium", "performance"],
        "milestone": "Phase 3: Enhancement"
    },
    
    {
        "title": "🧪 [Phase 4.1] Comprehensive Testing Suite",
        "body": """## 📋 Task Description
Create comprehensive testing suite for all new Exa.ai integration components.

## 🎯 Objectives
- Write unit tests for all components
- Create integration tests
- Add performance tests
- Validate accuracy improvements

## 📝 Subtasks
- [ ] Write unit tests for all new components
- [ ] Create integration tests for dual search
- [ ] Add performance tests
- [ ] Create accuracy tests with known datasets
- [ ] Add API endpoint tests
- [ ] Create load testing scenarios
- [ ] Add regression tests

## ✅ Acceptance Criteria
- [ ] >95% test coverage for new code
- [ ] All integration tests pass
- [ ] Performance tests meet targets
- [ ] Accuracy tests validate improvements
- [ ] Load tests pass

## 📊 Details
- **Priority**: Critical
- **Estimated Time**: 2 days
- **Phase**: 4 - Testing & Deployment
- **Dependencies**: All previous tasks

## 🔗 Related Files
- `tests/test_exa_integration.py`
- `tests/test_performance.py`
""",
        "labels": ["testing", "phase-4", "critical", "quality-assurance"],
        "milestone": "Phase 4: Testing & Deployment"
    },
    
    {
        "title": "📚 [Phase 4.2] Documentation & Deployment Preparation",
        "body": """## 📋 Task Description
Complete documentation and prepare for production deployment.

## 🎯 Objectives
- Update all documentation
- Create deployment scripts
- Set up monitoring dashboards
- Prepare production configuration

## 📝 Subtasks
- [ ] Update API documentation
- [ ] Create integration guides
- [ ] Add configuration documentation
- [ ] Update deployment scripts
- [ ] Create monitoring dashboards
- [ ] Prepare production environment variables
- [ ] Create rollback procedures

## ✅ Acceptance Criteria
- [ ] Documentation complete and accurate
- [ ] Deployment scripts updated
- [ ] Monitoring dashboards functional
- [ ] Integration guides available
- [ ] Production configuration ready

## 📊 Details
- **Priority**: High
- **Estimated Time**: 1.5 days
- **Phase**: 4 - Testing & Deployment
- **Dependencies**: Task 4.1

## 🔗 Related Files
- `docs/EXA_INTEGRATION_GUIDE.md`
- `deployment/exa-integration/`
""",
        "labels": ["documentation", "phase-4", "high", "deployment"],
        "milestone": "Phase 4: Testing & Deployment"
    },
    
    {
        "title": "🚀 [Phase 4.3] Production Deployment",
        "body": """## 📋 Task Description
Deploy Exa.ai integration to production environment with monitoring.

## 🎯 Objectives
- Deploy to staging environment
- Validate functionality
- Deploy to production
- Monitor deployment success

## 📝 Subtasks
- [ ] Deploy to staging environment
- [ ] Run staging tests
- [ ] Deploy to production
- [ ] Monitor production deployment
- [ ] Validate functionality in production
- [ ] Set up alerting
- [ ] Create deployment report

## ✅ Acceptance Criteria
- [ ] Staging deployment successful
- [ ] Production deployment successful
- [ ] All functionality working in production
- [ ] Monitoring shows healthy metrics
- [ ] No performance regression

## 📊 Details
- **Priority**: Critical
- **Estimated Time**: 0.5 days
- **Phase**: 4 - Testing & Deployment
- **Dependencies**: Task 4.2

## 🔗 Related Files
- `deployment/production/`
- `monitoring/dashboards/`
""",
        "labels": ["deployment", "phase-4", "critical", "production"],
        "milestone": "Phase 4: Testing & Deployment"
    }
]

def generate_github_issues_json():
    """Generate JSON file for GitHub issues import"""
    return json.dumps(GITHUB_ISSUES, indent=2)

def generate_github_cli_commands():
    """Generate GitHub CLI commands to create issues"""
    commands = []
    for issue in GITHUB_ISSUES:
        labels = ",".join(issue["labels"])
        command = f'''gh issue create \\
  --title "{issue['title']}" \\
  --body "{issue['body'].replace('"', '\\"')}" \\
  --label "{labels}"'''
        commands.append(command)
    
    return "\n\n".join(commands)

if __name__ == "__main__":
    print("🎯 Exa.ai Integration GitHub Issues")
    print("=" * 50)
    print(f"Total Issues: {len(GITHUB_ISSUES)}")
    print("\nIssue Titles:")
    for i, issue in enumerate(GITHUB_ISSUES, 1):
        print(f"{i:2d}. {issue['title']}")
    
    print("\n📋 To create these issues in GitHub:")
    print("1. Save the JSON output to a file")
    print("2. Use GitHub CLI or GitHub API to import")
    print("3. Or copy the CLI commands below")
    
    print("\n" + "="*50)
    print("JSON OUTPUT:")
    print(generate_github_issues_json())
