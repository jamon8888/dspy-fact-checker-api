#!/usr/bin/env python3
"""
Real integration test for Exa.ai integration with actual API calls.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.search.exa_search import ExaSearchProvider
from app.core.search.models import SearchQuery, SearchType
from app.core.search.hallucination_detector import HallucinationDetector
from app.core.search.exceptions import SearchProviderError, SearchConfigurationError


async def test_exa_basic_search():
    """Test basic Exa.ai search functionality."""
    print("🔍 Testing Exa.ai Basic Search...")
    
    try:
        # Initialize Exa provider with API key
        api_key = "76ec2188-0e1e-4704-baba-2255da82fb9d"
        provider = ExaSearchProvider(api_key)
        
        # Test neural search
        query = SearchQuery(
            query="artificial intelligence machine learning",
            search_type=SearchType.NEURAL,
            max_results=3
        )
        
        print(f"  📋 Searching for: '{query.query}'")
        start_time = time.time()
        
        results = await provider.search(query)
        
        duration = time.time() - start_time
        print(f"  ✅ Search completed in {duration:.2f}s")
        print(f"  📊 Found {len(results)} results")
        
        for i, result in enumerate(results, 1):
            print(f"    {i}. {result.title[:60]}...")
            print(f"       URL: {result.url}")
            print(f"       Score: {result.score:.3f}")
            print(f"       Source: {result.source}")
            print()
        
        return True
        
    except SearchConfigurationError as e:
        print(f"  ❌ Configuration Error: {e}")
        return False
    except SearchProviderError as e:
        print(f"  ❌ Provider Error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected Error: {e}")
        return False


async def test_exa_health_check():
    """Test Exa.ai provider health check."""
    print("🏥 Testing Exa.ai Health Check...")
    
    try:
        api_key = "76ec2188-0e1e-4704-baba-2255da82fb9d"
        provider = ExaSearchProvider(api_key)
        
        is_healthy = await provider.health_check()
        
        if is_healthy:
            print("  ✅ Exa.ai provider is healthy")
            return True
        else:
            print("  ❌ Exa.ai provider is unhealthy")
            return False
            
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")
        return False


async def test_hallucination_detection():
    """Test hallucination detection functionality."""
    print("🧠 Testing Hallucination Detection...")
    
    try:
        api_key = "76ec2188-0e1e-4704-baba-2255da82fb9d"
        provider = ExaSearchProvider(api_key)
        detector = HallucinationDetector(provider, confidence_threshold=0.7)
        
        # Test with a factual claim
        test_claim = "The Earth orbits around the Sun once every 365.25 days."
        print(f"  📋 Testing claim: '{test_claim}'")
        
        start_time = time.time()
        result = await detector.detect_hallucination(test_claim)
        duration = time.time() - start_time
        
        print(f"  ✅ Analysis completed in {duration:.2f}s")
        print(f"  📊 Results:")
        print(f"    Is Hallucination: {result.is_hallucination}")
        print(f"    Confidence Score: {result.confidence_score:.3f}")
        print(f"    Risk Level: {result.risk_level}")
        print(f"    Key Facts Found: {len(result.key_facts)}")
        print(f"    Evidence Sources: {len(result.evidence)}")
        
        if result.key_facts:
            print(f"  🔍 Key Facts Extracted:")
            for fact in result.key_facts[:3]:  # Show first 3
                print(f"    - {fact}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Hallucination detection failed: {e}")
        return False


async def test_search_capabilities():
    """Test Exa.ai search capabilities."""
    print("⚙️ Testing Search Capabilities...")
    
    try:
        api_key = "76ec2188-0e1e-4704-baba-2255da82fb9d"
        provider = ExaSearchProvider(api_key)
        
        capabilities = await provider.get_search_capabilities()
        
        print("  📊 Exa.ai Capabilities:")
        print(f"    Provider: {capabilities['provider']}")
        print(f"    Search Types: {capabilities['search_types']}")
        print(f"    Supports Autoprompt: {capabilities['supports_autoprompt']}")
        print(f"    Supports Domain Filtering: {capabilities['supports_domain_filtering']}")
        print(f"    Supports Highlights: {capabilities['supports_highlights']}")
        print(f"    Max Results: {capabilities['max_results_per_query']}")
        print(f"    Rate Limit: {capabilities['rate_limit']['calls']}/{capabilities['rate_limit']['period']}s")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Capabilities test failed: {e}")
        return False


async def test_different_search_types():
    """Test different search types."""
    print("🔄 Testing Different Search Types...")
    
    try:
        api_key = "76ec2188-0e1e-4704-baba-2255da82fb9d"
        provider = ExaSearchProvider(api_key)
        
        search_types = [SearchType.NEURAL, SearchType.KEYWORD]
        query_text = "climate change global warming"
        
        for search_type in search_types:
            print(f"  🔍 Testing {search_type.value} search...")
            
            query = SearchQuery(
                query=query_text,
                search_type=search_type,
                max_results=2
            )
            
            start_time = time.time()
            results = await provider.search(query)
            duration = time.time() - start_time
            
            print(f"    ✅ {search_type.value} search: {len(results)} results in {duration:.2f}s")
            
            if results:
                print(f"    📄 Top result: {results[0].title[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Search types test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print("🚀 Starting Exa.ai Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Basic Search", test_exa_basic_search),
        ("Health Check", test_exa_health_check),
        ("Search Capabilities", test_search_capabilities),
        ("Different Search Types", test_different_search_types),
        ("Hallucination Detection", test_hallucination_detection),
    ]
    
    results = []
    total_start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            success = await test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
            results.append((test_name, False))
    
    total_duration = time.time() - total_start_time
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall Results: {passed}/{total} tests passed")
    print(f"⏱️ Total Time: {total_duration:.2f} seconds")
    
    if passed == total:
        print("🎊 ALL TESTS PASSED! Exa.ai integration is working correctly.")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    # Set environment variable for testing
    os.environ["EXA_API_KEY"] = "76ec2188-0e1e-4704-baba-2255da82fb9d"
    
    # Run the tests
    success = asyncio.run(main())
    
    if success:
        print("\n🎯 Integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Integration test failed!")
        sys.exit(1)
