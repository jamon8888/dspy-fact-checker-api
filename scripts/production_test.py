#!/usr/bin/env python3
"""
Production API Testing Script

Comprehensive testing script for the fact-checking platform API.
Tests all endpoints, authentication, billing, monitoring, and edge cases.
"""

import asyncio
import aiohttp
import json
import time
import os
import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    success: bool
    response_time: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None


class ProductionAPITester:
    """Comprehensive API testing class."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the API tester."""
        self.base_url = base_url
        self.session = None
        self.auth_token = None
        self.admin_token = None
        self.test_results: List[TestResult] = []
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all production tests."""
        logger.info("🚀 Starting comprehensive production API testing...")
        
        start_time = time.time()
        
        # Test phases
        test_phases = [
            ("Health & Status", self.test_health_endpoints),
            ("Authentication", self.test_authentication),
            ("Core Fact-Checking", self.test_fact_checking),
            ("Document Processing", self.test_document_processing),
            ("URL Processing", self.test_url_processing),
            ("OCR Processing", self.test_ocr_processing),
            ("Billing & Subscriptions", self.test_billing),
            ("Monitoring & Analytics", self.test_monitoring),
            ("Admin Functions", self.test_admin_functions),
            ("Error Handling", self.test_error_handling),
            ("Performance", self.test_performance),
            ("Security", self.test_security)
        ]
        
        phase_results = {}
        
        for phase_name, test_function in test_phases:
            logger.info(f"📋 Testing {phase_name}...")
            try:
                phase_result = await test_function()
                phase_results[phase_name] = phase_result
                logger.info(f"✅ {phase_name} tests completed")
            except Exception as e:
                logger.error(f"❌ {phase_name} tests failed: {e}")
                phase_results[phase_name] = {"error": str(e)}
        
        total_time = time.time() - start_time
        
        # Generate summary report
        summary = self.generate_summary_report(phase_results, total_time)
        
        logger.info("🎉 Production testing completed!")
        return summary
    
    async def test_health_endpoints(self) -> Dict[str, Any]:
        """Test health and status endpoints."""
        tests = [
            ("Basic Health Check", "GET", "/api/v1/health"),
            ("System Status", "GET", "/api/v1/monitoring/system-status"),
            ("Monitoring Health", "GET", "/api/v1/monitoring/health"),
        ]
        
        results = []
        for test_name, method, endpoint in tests:
            result = await self.make_request(test_name, method, endpoint)
            results.append(result)
        
        return {"tests": results, "passed": sum(1 for r in results if r.success)}
    
    async def test_authentication(self) -> Dict[str, Any]:
        """Test authentication system."""
        results = []
        
        # Test user registration
        register_data = {
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        register_result = await self.make_request(
            "User Registration",
            "POST",
            "/api/v1/auth/register",
            json_data=register_data
        )
        results.append(register_result)
        
        if register_result.success:
            # Test user login
            login_data = {
                "email": register_data["email"],
                "password": register_data["password"]
            }
            
            login_result = await self.make_request(
                "User Login",
                "POST",
                "/api/v1/auth/login",
                json_data=login_data
            )
            results.append(login_result)
            
            if login_result.success and login_result.response_data:
                self.auth_token = login_result.response_data.get("access_token")
                
                # Test protected endpoint
                profile_result = await self.make_request(
                    "Get User Profile",
                    "GET",
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                results.append(profile_result)
        
        # Test API key authentication
        api_key_result = await self.make_request(
            "API Key Generation",
            "POST",
            "/api/v1/auth/api-keys",
            headers={"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else None,
            json_data={"name": "Test API Key"}
        )
        results.append(api_key_result)
        
        return {"tests": results, "passed": sum(1 for r in results if r.success)}
    
    async def test_fact_checking(self) -> Dict[str, Any]:
        """Test core fact-checking functionality."""
        if not self.auth_token:
            return {"error": "No authentication token available"}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        results = []
        
        # Test text fact-checking
        text_data = {
            "text": "The Earth is round.",
            "model": "gpt-4"
        }
        
        text_result = await self.make_request(
            "Text Fact-Checking",
            "POST",
            "/api/v1/fact-check/text",
            headers=headers,
            json_data=text_data
        )
        results.append(text_result)
        
        # Test DSPy fact-checking
        dspy_data = {
            "text": "Water boils at 100 degrees Celsius at sea level.",
            "use_optimization": True
        }
        
        dspy_result = await self.make_request(
            "DSPy Fact-Checking",
            "POST",
            "/api/v1/fact-check/dspy",
            headers=headers,
            json_data=dspy_data
        )
        results.append(dspy_result)
        
        return {"tests": results, "passed": sum(1 for r in results if r.success)}
    
    async def test_document_processing(self) -> Dict[str, Any]:
        """Test document processing endpoints."""
        if not self.auth_token:
            return {"error": "No authentication token available"}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        results = []
        
        # Create a test text file
        test_content = "This is a test document for fact-checking. The Earth is round."
        
        # Test document upload (simulated)
        doc_result = await self.make_request(
            "Document Processing",
            "POST",
            "/api/v1/fact-check/documents",
            headers=headers,
            # Note: In real test, would upload actual file
            json_data={"text_content": test_content}
        )
        results.append(doc_result)
        
        return {"tests": results, "passed": sum(1 for r in results if r.success)}
    
    async def test_url_processing(self) -> Dict[str, Any]:
        """Test URL processing endpoints."""
        if not self.auth_token:
            return {"error": "No authentication token available"}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        results = []
        
        # Test URL fact-checking
        url_data = {
            "url": "https://example.com",
            "model": "claude-3"
        }
        
        url_result = await self.make_request(
            "URL Fact-Checking",
            "POST",
            "/api/v1/fact-check/urls",
            headers=headers,
            json_data=url_data
        )
        results.append(url_result)
        
        return {"tests": results, "passed": sum(1 for r in results if r.success)}
    
    async def test_ocr_processing(self) -> Dict[str, Any]:
        """Test OCR processing endpoints."""
        if not self.auth_token:
            return {"error": "No authentication token available"}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        results = []
        
        # Test OCR processing (simulated)
        ocr_result = await self.make_request(
            "OCR Processing",
            "POST",
            "/api/v1/ocr/process",
            headers=headers,
            json_data={"image_data": "base64_encoded_image_data"}
        )
        results.append(ocr_result)
        
        return {"tests": results, "passed": sum(1 for r in results if r.success)}
    
    async def test_billing(self) -> Dict[str, Any]:
        """Test billing and subscription endpoints."""
        if not self.auth_token:
            return {"error": "No authentication token available"}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        results = []
        
        # Test get subscription plans
        plans_result = await self.make_request(
            "Get Subscription Plans",
            "GET",
            "/api/v1/billing/plans",
            headers=headers
        )
        results.append(plans_result)
        
        # Test get current subscription
        subscription_result = await self.make_request(
            "Get Current Subscription",
            "GET",
            "/api/v1/billing/subscription",
            headers=headers
        )
        results.append(subscription_result)
        
        # Test get usage statistics
        usage_result = await self.make_request(
            "Get Usage Statistics",
            "GET",
            "/api/v1/billing/usage",
            headers=headers
        )
        results.append(usage_result)
        
        return {"tests": results, "passed": sum(1 for r in results if r.success)}
    
    async def test_monitoring(self) -> Dict[str, Any]:
        """Test monitoring endpoints."""
        results = []
        
        # Test public monitoring endpoints
        public_tests = [
            ("System Status", "GET", "/api/v1/monitoring/system-status"),
            ("Health Check", "GET", "/api/v1/monitoring/health"),
        ]
        
        for test_name, method, endpoint in public_tests:
            result = await self.make_request(test_name, method, endpoint)
            results.append(result)
        
        return {"tests": results, "passed": sum(1 for r in results if r.success)}
    
    async def test_admin_functions(self) -> Dict[str, Any]:
        """Test admin-only functions."""
        # Note: These tests would require admin authentication
        results = []
        
        # Test admin endpoints (would need admin token)
        admin_tests = [
            ("System Metrics", "GET", "/api/v1/monitoring/metrics"),
            ("Business Dashboard", "GET", "/api/v1/monitoring/business-dashboard"),
            ("Quality Report", "GET", "/api/v1/monitoring/quality-report"),
        ]
        
        for test_name, method, endpoint in admin_tests:
            # These should fail without admin auth (expected behavior)
            result = await self.make_request(test_name, method, endpoint)
            results.append(result)
        
        return {"tests": results, "passed": 0}  # Expected to fail without admin auth
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and edge cases."""
        results = []
        
        # Test invalid endpoints
        invalid_result = await self.make_request(
            "Invalid Endpoint",
            "GET",
            "/api/v1/nonexistent"
        )
        results.append(invalid_result)
        
        # Test malformed requests
        malformed_result = await self.make_request(
            "Malformed Request",
            "POST",
            "/api/v1/fact-check/text",
            json_data={"invalid": "data"}
        )
        results.append(malformed_result)
        
        return {"tests": results, "passed": sum(1 for r in results if not r.success)}  # Expecting failures
    
    async def test_performance(self) -> Dict[str, Any]:
        """Test performance under load."""
        if not self.auth_token:
            return {"error": "No authentication token available"}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Concurrent requests test
        concurrent_requests = 10
        tasks = []
        
        for i in range(concurrent_requests):
            task = self.make_request(
                f"Concurrent Request {i+1}",
                "POST",
                "/api/v1/fact-check/text",
                headers=headers,
                json_data={"text": f"Test claim {i+1}", "model": "gpt-4"}
            )
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        successful_results = [r for r in results if isinstance(r, TestResult) and r.success]
        
        return {
            "tests": results,
            "passed": len(successful_results),
            "total_time": total_time,
            "requests_per_second": len(successful_results) / total_time if total_time > 0 else 0
        }
    
    async def test_security(self) -> Dict[str, Any]:
        """Test security features."""
        results = []
        
        # Test unauthorized access
        unauthorized_result = await self.make_request(
            "Unauthorized Access",
            "GET",
            "/api/v1/auth/me"
        )
        results.append(unauthorized_result)
        
        # Test invalid token
        invalid_token_result = await self.make_request(
            "Invalid Token",
            "GET",
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        results.append(invalid_token_result)
        
        return {"tests": results, "passed": sum(1 for r in results if not r.success)}  # Expecting failures
    
    async def make_request(
        self,
        test_name: str,
        method: str,
        endpoint: str,
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        timeout: int = 30
    ) -> TestResult:
        """Make an HTTP request and return test result."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with self.session.request(
                method,
                url,
                headers=headers,
                json=json_data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response_time = time.time() - start_time
                
                try:
                    response_data = await response.json()
                except:
                    response_data = None
                
                success = 200 <= response.status < 300
                
                result = TestResult(
                    test_name=test_name,
                    success=success,
                    response_time=response_time,
                    status_code=response.status,
                    response_data=response_data
                )
                
                if success:
                    logger.info(f"✅ {test_name}: {response.status} ({response_time:.3f}s)")
                else:
                    logger.warning(f"⚠️  {test_name}: {response.status} ({response_time:.3f}s)")
                
                return result
                
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"❌ {test_name}: {str(e)} ({response_time:.3f}s)")
            
            return TestResult(
                test_name=test_name,
                success=False,
                response_time=response_time,
                error_message=str(e)
            )
    
    def generate_summary_report(self, phase_results: Dict, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive summary report."""
        total_tests = 0
        total_passed = 0
        
        for phase_name, phase_data in phase_results.items():
            if isinstance(phase_data, dict) and "tests" in phase_data:
                total_tests += len(phase_data["tests"])
                total_passed += phase_data.get("passed", 0)
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_time_seconds": total_time,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_tests - total_passed,
            "success_rate_percent": success_rate,
            "phase_results": phase_results,
            "status": "PASS" if success_rate >= 80 else "FAIL",
            "recommendations": self.generate_recommendations(phase_results)
        }
        
        return summary
    
    def generate_recommendations(self, phase_results: Dict) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        for phase_name, phase_data in phase_results.items():
            if isinstance(phase_data, dict):
                if "error" in phase_data:
                    recommendations.append(f"Fix critical error in {phase_name}: {phase_data['error']}")
                elif phase_data.get("passed", 0) == 0:
                    recommendations.append(f"All tests failed in {phase_name} - requires immediate attention")
                elif phase_data.get("passed", 0) < len(phase_data.get("tests", [])) * 0.8:
                    recommendations.append(f"Low success rate in {phase_name} - review failed tests")
        
        if not recommendations:
            recommendations.append("All tests passed successfully - system is ready for production")
        
        return recommendations


async def main():
    """Main testing function."""
    # Check if server is running
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    async with ProductionAPITester(base_url) as tester:
        try:
            # Run all tests
            results = await tester.run_all_tests()
            
            # Save results to file
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            results_file = f"test_results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Print summary
            print("\n" + "="*80)
            print("🎯 PRODUCTION API TEST SUMMARY")
            print("="*80)
            print(f"📊 Total Tests: {results['total_tests']}")
            print(f"✅ Passed: {results['total_passed']}")
            print(f"❌ Failed: {results['total_failed']}")
            print(f"📈 Success Rate: {results['success_rate_percent']:.1f}%")
            print(f"⏱️  Total Time: {results['total_time_seconds']:.2f}s")
            print(f"🎯 Status: {results['status']}")
            print(f"📄 Results saved to: {results_file}")
            
            print("\n📋 RECOMMENDATIONS:")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"{i}. {rec}")
            
            print("="*80)
            
            # Exit with appropriate code
            sys.exit(0 if results['status'] == 'PASS' else 1)
            
        except Exception as e:
            logger.error(f"Testing failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
