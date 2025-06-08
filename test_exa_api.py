#!/usr/bin/env python3
"""
Test Exa.ai API endpoints.
"""

import asyncio
import os
import sys
import time
import json
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.exa_fact_checking_service import ExaFactCheckingService
from app.core.search.models import SearchType


async def test_exa_service_initialization():
    """Test Exa.ai service initialization."""
    print("🔧 Testing Exa.ai Service Initialization...")
    
    try:
        service = ExaFactCheckingService()
        await service.initialize()
        
        print("  ✅ Service initialized successfully")
        print(f"  📊 Exa provider available: {service.exa_provider is not None}")
        print(f"  📊 Tavily provider available: {service.tavily_provider is not None}")
        print(f"  📊 Dual orchestrator available: {service.dual_orchestrator is not None}")
        print(f"  📊 Hallucination detector available: {service.hallucination_detector is not None}")
        
        return service
        
    except Exception as e:
        print(f"  ❌ Service initialization failed: {e}")
        return None


async def test_exa_search_only():
    """Test Exa.ai search only functionality."""
    print("🔍 Testing Exa.ai Search Only...")
    
    try:
        service = ExaFactCheckingService()
        await service.initialize()
        
        query = "renewable energy solar power"
        print(f"  📋 Searching for: '{query}'")
        
        start_time = time.time()
        results = await service.search_with_exa_only(
            query=query,
            search_type=SearchType.NEURAL,
            max_results=3
        )
        duration = time.time() - start_time
        
        print(f"  ✅ Search completed in {duration:.2f}s")
        print(f"  📊 Found {len(results)} results")
        
        for i, result in enumerate(results[:2], 1):  # Show first 2
            print(f"    {i}. {result['title'][:50]}...")
            print(f"       Score: {result['score']:.3f}")
            print(f"       Source: {result['source']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Exa search test failed: {e}")
        return False


async def test_hallucination_check_only():
    """Test hallucination detection only."""
    print("🧠 Testing Hallucination Check Only...")
    
    try:
        service = ExaFactCheckingService()
        await service.initialize()
        
        claim = "Water boils at 100 degrees Celsius at sea level."
        print(f"  📋 Testing claim: '{claim}'")
        
        start_time = time.time()
        result = await service.check_hallucination_only(claim)
        duration = time.time() - start_time
        
        print(f"  ✅ Analysis completed in {duration:.2f}s")
        print(f"  📊 Results:")
        print(f"    Is Hallucination: {result.is_hallucination}")
        print(f"    Confidence Score: {result.confidence_score:.3f}")
        print(f"    Risk Level: {result.risk_level}")
        print(f"    Evidence Sources: {len(result.evidence)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Hallucination check failed: {e}")
        return False


async def test_full_fact_check():
    """Test full fact-checking with Exa.ai."""
    print("🎯 Testing Full Fact-Check with Exa.ai...")
    
    try:
        service = ExaFactCheckingService()
        await service.initialize()
        
        claim = "The Great Wall of China is visible from space."
        print(f"  📋 Fact-checking claim: '{claim}'")
        
        start_time = time.time()
        result = await service.fact_check_with_exa(
            claim=claim,
            search_strategy="parallel",
            enable_hallucination_detection=True
        )
        duration = time.time() - start_time
        
        print(f"  ✅ Fact-check completed in {duration:.2f}s")
        print(f"  📊 Results:")
        print(f"    Verdict: {result.verdict}")
        print(f"    Confidence: {result.confidence:.3f}")
        print(f"    Accuracy Score: {result.accuracy_score:.3f}")
        print(f"    Sources Used: {result.sources_used}")
        print(f"    Is Reliable: {result.is_reliable}")
        
        print(f"  🧠 Hallucination Analysis:")
        print(f"    Is Hallucination: {result.hallucination_analysis.is_hallucination}")
        print(f"    Confidence: {result.hallucination_analysis.confidence_score:.3f}")
        
        print(f"  🔍 Search Results:")
        print(f"    Total Results: {result.search_results.total_results}")
        print(f"    Exa Results: {len(result.search_results.exa_results)}")
        print(f"    Tavily Results: {len(result.search_results.tavily_results)}")
        print(f"    Success Rate: {result.search_results.success_rate:.1%}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Full fact-check failed: {e}")
        return False


async def test_service_stats():
    """Test service statistics."""
    print("📊 Testing Service Statistics...")
    
    try:
        service = ExaFactCheckingService()
        await service.initialize()
        
        stats = await service.get_service_stats()
        
        print("  📈 Service Stats:")
        print(f"    Fact Checks Performed: {stats['fact_checks_performed']}")
        print(f"    Successful Fact Checks: {stats['successful_fact_checks']}")
        print(f"    Success Rate: {stats['success_rate']:.1%}")
        print(f"    Average Processing Time: {stats['average_processing_time']:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Service stats test failed: {e}")
        return False


async def test_different_search_strategies():
    """Test different search strategies."""
    print("🔄 Testing Different Search Strategies...")
    
    try:
        service = ExaFactCheckingService()
        await service.initialize()
        
        claim = "Python is a programming language."
        strategies = ["parallel", "sequential", "intelligent"]
        
        for strategy in strategies:
            print(f"  🔍 Testing {strategy} strategy...")
            
            start_time = time.time()
            result = await service.fact_check_with_exa(
                claim=claim,
                search_strategy=strategy,
                enable_hallucination_detection=False  # Faster for testing
            )
            duration = time.time() - start_time
            
            print(f"    ✅ {strategy}: {result.verdict} (confidence: {result.confidence:.3f}) in {duration:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Search strategies test failed: {e}")
        return False


async def main():
    """Run all API tests."""
    print("🚀 Starting Exa.ai API Tests")
    print("=" * 50)
    
    # Set environment variable
    os.environ["EXA_API_KEY"] = "76ec2188-0e1e-4704-baba-2255da82fb9d"
    
    tests = [
        ("Service Initialization", test_exa_service_initialization),
        ("Exa Search Only", test_exa_search_only),
        ("Hallucination Check Only", test_hallucination_check_only),
        ("Service Statistics", test_service_stats),
        ("Different Search Strategies", test_different_search_strategies),
        ("Full Fact-Check", test_full_fact_check),
    ]
    
    results = []
    total_start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            if test_name == "Service Initialization":
                # Special handling for initialization test
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
    print("📊 API TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall Results: {passed}/{total} tests passed")
    print(f"⏱️ Total Time: {total_duration:.2f} seconds")
    
    if passed == total:
        print("🎊 ALL API TESTS PASSED! Exa.ai service is working correctly.")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n🎯 API test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 API test failed!")
        sys.exit(1)
