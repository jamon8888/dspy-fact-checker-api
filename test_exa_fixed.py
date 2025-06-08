#!/usr/bin/env python3
"""
Fixed test for Exa.ai integration with proper environment loading.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Set environment variables before importing anything
os.environ["EXA_API_KEY"] = "76ec2188-0e1e-4704-baba-2255da82fb9d"
os.environ["TAVILY_API_KEY"] = "test_key"  # Placeholder for testing
os.environ["ENVIRONMENT"] = "production"

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.exa_fact_checking_service import ExaFactCheckingService
from app.core.search.models import SearchType


async def test_service_with_api_key():
    """Test service with proper API key configuration."""
    print("🔧 Testing Service with API Key...")
    
    try:
        service = ExaFactCheckingService()
        
        # Manually set the API keys for testing
        service.settings.EXA_API_KEY = "76ec2188-0e1e-4704-baba-2255da82fb9d"
        service.settings.TAVILY_API_KEY = "test_key"
        
        await service.initialize()
        
        print("  ✅ Service initialized with API keys")
        print(f"  📊 Exa provider available: {service.exa_provider is not None}")
        print(f"  📊 Tavily provider available: {service.tavily_provider is not None}")
        print(f"  📊 Dual orchestrator available: {service.dual_orchestrator is not None}")
        print(f"  📊 Hallucination detector available: {service.hallucination_detector is not None}")
        
        return service
        
    except Exception as e:
        print(f"  ❌ Service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_exa_search_direct():
    """Test Exa.ai search directly."""
    print("🔍 Testing Direct Exa.ai Search...")
    
    try:
        from app.core.search.exa_search import ExaSearchProvider
        from app.core.search.models import SearchQuery, SearchType
        
        provider = ExaSearchProvider("76ec2188-0e1e-4704-baba-2255da82fb9d")
        
        query = SearchQuery(
            query="machine learning algorithms",
            search_type=SearchType.NEURAL,
            max_results=2
        )
        
        start_time = time.time()
        results = await provider.search(query)
        duration = time.time() - start_time
        
        print(f"  ✅ Direct search completed in {duration:.2f}s")
        print(f"  📊 Found {len(results)} results")
        
        for i, result in enumerate(results, 1):
            print(f"    {i}. {result.title[:50]}...")
            print(f"       Score: {result.score:.3f}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Direct search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_hallucination_direct():
    """Test hallucination detection directly."""
    print("🧠 Testing Direct Hallucination Detection...")
    
    try:
        from app.core.search.exa_search import ExaSearchProvider
        from app.core.search.hallucination_detector import HallucinationDetector
        
        provider = ExaSearchProvider("76ec2188-0e1e-4704-baba-2255da82fb9d")
        detector = HallucinationDetector(provider, confidence_threshold=0.7)
        
        claim = "The speed of light is approximately 300,000 kilometers per second."
        
        start_time = time.time()
        result = await detector.detect_hallucination(claim)
        duration = time.time() - start_time
        
        print(f"  ✅ Hallucination detection completed in {duration:.2f}s")
        print(f"  📊 Results:")
        print(f"    Is Hallucination: {result.is_hallucination}")
        print(f"    Confidence Score: {result.confidence_score:.3f}")
        print(f"    Key Facts: {len(result.key_facts)}")
        print(f"    Evidence: {len(result.evidence)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Hallucination detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_service_fact_check():
    """Test service fact-checking with proper setup."""
    print("🎯 Testing Service Fact-Check...")
    
    try:
        service = ExaFactCheckingService()
        
        # Manually configure for testing
        service.settings.EXA_API_KEY = "76ec2188-0e1e-4704-baba-2255da82fb9d"
        service.settings.TAVILY_API_KEY = "test_key"
        service.settings.HALLUCINATION_DETECTION_ENABLED = True
        
        await service.initialize()
        
        if not service.exa_provider:
            print("  ❌ Exa provider not initialized")
            return False
        
        claim = "Photosynthesis converts sunlight into chemical energy."
        
        start_time = time.time()
        result = await service.fact_check_with_exa(
            claim=claim,
            search_strategy="intelligent",
            enable_hallucination_detection=True
        )
        duration = time.time() - start_time
        
        print(f"  ✅ Fact-check completed in {duration:.2f}s")
        print(f"  📊 Results:")
        print(f"    Verdict: {result.verdict}")
        print(f"    Confidence: {result.confidence:.3f}")
        print(f"    Sources: {result.sources_used}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Service fact-check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run comprehensive tests."""
    print("🚀 Starting Comprehensive Exa.ai Tests")
    print("=" * 50)
    
    tests = [
        ("Service with API Key", test_service_with_api_key),
        ("Direct Exa Search", test_exa_search_direct),
        ("Direct Hallucination Detection", test_hallucination_direct),
        ("Service Fact-Check", test_service_fact_check),
    ]
    
    results = []
    total_start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            if test_name == "Service with API Key":
                service = await test_func()
                success = service is not None
            else:
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
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall Results: {passed}/{total} tests passed")
    print(f"⏱️ Total Time: {total_duration:.2f} seconds")
    
    if passed == total:
        print("🎊 ALL TESTS PASSED! Exa.ai integration is fully functional.")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n🎯 Comprehensive test completed successfully!")
        print("🚀 Exa.ai integration is ready for production!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)
