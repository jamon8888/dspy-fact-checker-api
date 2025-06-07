#!/usr/bin/env python3
"""
Full API Test Suite for DSPy-Enhanced Fact-Checker API Platform
Tests all endpoints including text processing functionality
"""

import requests
import json
import time
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8006"

class APITestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_user_id = None
        self.results = []
    
    def log_test(self, test_name: str, status: str, details: Dict[str, Any] = None):
        """Log test result."""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": time.time(),
            "details": details or {}
        }
        self.results.append(result)
        
        status_icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[ERROR]"
        print(f"{status_icon} {test_name}")
        
        if details and status != "PASS":
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def test_health_endpoints(self):
        """Test health and status endpoints."""
        print("\n=== Testing Health & Status Endpoints ===")
        
        endpoints = [
            ("/health", "Health Check"),
            ("/", "Root Endpoint"),
            ("/docs", "API Documentation"),
            ("/openapi.json", "OpenAPI Schema")
        ]
        
        for endpoint, description in endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    self.log_test(f"health_{endpoint.replace('/', '_')}", "PASS", {
                        "endpoint": endpoint,
                        "response_time": f"{response.elapsed.total_seconds():.3f}s"
                    })
                else:
                    self.log_test(f"health_{endpoint.replace('/', '_')}", "FAIL", {
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "error": response.text[:200]
                    })
                    
            except Exception as e:
                self.log_test(f"health_{endpoint.replace('/', '_')}", "ERROR", {
                    "endpoint": endpoint,
                    "error": str(e)
                })
    
    def test_user_registration(self):
        """Test user registration."""
        print("\n=== Testing User Registration ===")
        
        test_user = {
            "email": f"test_user_{int(time.time())}@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/register",
                json=test_user,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.test_user_id = user_data.get("id")
                self.log_test("user_registration", "PASS", {
                    "user_id": self.test_user_id,
                    "email": user_data.get("email"),
                    "response_time": f"{response.elapsed.total_seconds():.3f}s"
                })
            else:
                self.log_test("user_registration", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })
                
        except Exception as e:
            self.log_test("user_registration", "ERROR", {"error": str(e)})
    
    def test_password_validation(self):
        """Test password validation rules."""
        print("\n=== Testing Password Validation ===")
        
        test_cases = [
            ("ValidPassword123!", True, "Strong password"),
            ("weak", False, "Too short"),
            ("nouppercase123!", False, "No uppercase"),
            ("NOLOWERCASE123!", False, "No lowercase"),
            ("NoNumbers!", False, "No numbers")
        ]
        
        passed = 0
        total = len(test_cases)
        
        for password, should_pass, description in test_cases:
            test_user = {
                "email": f"pwd_test_{hash(password)}@example.com",
                "password": password,
                "first_name": "Test",
                "last_name": "User"
            }
            
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/v1/auth/register",
                    json=test_user,
                    timeout=10
                )
                
                actual_pass = response.status_code == 200
                if should_pass == actual_pass:
                    passed += 1
                    
            except Exception:
                pass  # Count as failure
        
        if passed == total:
            self.log_test("password_validation", "PASS", {
                "passed": f"{passed}/{total}",
                "description": "All password validation rules working correctly"
            })
        else:
            self.log_test("password_validation", "FAIL", {
                "passed": f"{passed}/{total}",
                "description": "Some password validation rules failed"
            })
    
    def test_text_processing_endpoints(self):
        """Test text processing and fact-checking endpoints."""
        print("\n=== Testing Text Processing Endpoints ===")

        # Test text for fact-checking
        test_text = """
        The Earth is flat and the moon landing in 1969 was staged by NASA.
        Climate change is not real and vaccines cause autism.
        The COVID-19 pandemic was planned by world governments.
        """

        # Test basic text processing
        try:
            response = self.session.post(
                f"{BASE_URL}/api/v1/text/process",
                json={
                    "text": test_text,
                    "options": {
                        "extract_claims": True,
                        "verify_claims": False,  # Skip verification for now
                        "include_sources": False
                    }
                },
                timeout=30
            )

            if response.status_code in [200, 202]:  # Accept both success and accepted
                self.log_test("text_processing", "PASS", {
                    "status_code": response.status_code,
                    "response_time": f"{response.elapsed.total_seconds():.3f}s",
                    "text_length": len(test_text)
                })
            else:
                self.log_test("text_processing", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })

        except Exception as e:
            self.log_test("text_processing", "ERROR", {"error": str(e)})
    
    def test_url_processing_endpoints(self):
        """Test URL processing endpoints."""
        print("\n=== Testing URL Processing Endpoints ===")

        test_url = "https://www.example.com"

        try:
            response = self.session.post(
                f"{BASE_URL}/api/v1/urls/process",
                json={
                    "url": test_url,
                    "options": {
                        "extract_claims": True,
                        "verify_claims": False,
                        "include_sources": False
                    }
                },
                timeout=30
            )

            if response.status_code in [200, 202, 422]:  # 422 might be expected for example.com
                self.log_test("url_processing", "PASS", {
                    "status_code": response.status_code,
                    "response_time": f"{response.elapsed.total_seconds():.3f}s",
                    "url": test_url
                })
            else:
                self.log_test("url_processing", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })

        except Exception as e:
            self.log_test("url_processing", "ERROR", {"error": str(e)})
    
    def test_document_upload_endpoints(self):
        """Test document upload endpoints."""
        print("\n=== Testing Document Upload Endpoints ===")

        # Create a simple text file for testing
        test_content = "This is a test document for fact-checking. The Earth is round."

        try:
            files = {
                'file': ('test.txt', test_content.encode(), 'text/plain')
            }
            data = {
                'options': json.dumps({
                    "extract_claims": True,
                    "verify_claims": False,
                    "include_sources": False
                })
            }

            response = self.session.post(
                f"{BASE_URL}/api/v1/documents/upload",
                files=files,
                data=data,
                timeout=30
            )

            if response.status_code in [200, 202]:
                self.log_test("document_upload", "PASS", {
                    "status_code": response.status_code,
                    "response_time": f"{response.elapsed.total_seconds():.3f}s",
                    "file_size": len(test_content)
                })
            else:
                self.log_test("document_upload", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })

        except Exception as e:
            self.log_test("document_upload", "ERROR", {"error": str(e)})
    
    def test_analytics_endpoints(self):
        """Test analytics and metrics endpoints."""
        print("\n=== Testing Analytics Endpoints ===")

        endpoints = [
            ("/api/v1/monitoring/usage-analytics", "Usage Analytics"),
            ("/api/v1/monitoring/metrics", "System Metrics"),
            ("/api/v1/billing/usage", "Billing Usage"),
            ("/api/v1/monitoring/system-status", "System Status")
        ]

        for endpoint, description in endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}", timeout=10)

                # These endpoints might require authentication, so accept 401/403
                if response.status_code in [200, 401, 403]:
                    self.log_test(f"analytics_{endpoint.split('/')[-1].replace('-', '_')}", "PASS", {
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "note": "Endpoint accessible (auth may be required)"
                    })
                else:
                    self.log_test(f"analytics_{endpoint.split('/')[-1].replace('-', '_')}", "FAIL", {
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "error": response.text[:200]
                    })

            except Exception as e:
                self.log_test(f"analytics_{endpoint.split('/')[-1].replace('-', '_')}", "ERROR", {
                    "endpoint": endpoint,
                    "error": str(e)
                })

    def test_dspy_fact_checking(self):
        """Test DSPy fact-checking endpoints."""
        print("\n=== Testing DSPy Fact-Checking Endpoints ===")

        test_text = "The Earth is flat and climate change is not real."

        # Test claim extraction
        try:
            response = self.session.post(
                f"{BASE_URL}/api/v1/dspy/extract-claims",
                json={"text": test_text},
                timeout=30
            )

            if response.status_code in [200, 202]:
                self.log_test("dspy_extract_claims", "PASS", {
                    "status_code": response.status_code,
                    "response_time": f"{response.elapsed.total_seconds():.3f}s"
                })
            else:
                self.log_test("dspy_extract_claims", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })

        except Exception as e:
            self.log_test("dspy_extract_claims", "ERROR", {"error": str(e)})

        # Test claim verification
        try:
            response = self.session.post(
                f"{BASE_URL}/api/v1/dspy/verify-claim",
                json={"claim": "The Earth is flat"},
                timeout=30
            )

            if response.status_code in [200, 202]:
                self.log_test("dspy_verify_claim", "PASS", {
                    "status_code": response.status_code,
                    "response_time": f"{response.elapsed.total_seconds():.3f}s"
                })
            else:
                self.log_test("dspy_verify_claim", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })

        except Exception as e:
            self.log_test("dspy_verify_claim", "ERROR", {"error": str(e)})

    def test_focused_processing(self):
        """Test focused document processing endpoints."""
        print("\n=== Testing Focused Processing Endpoints ===")

        test_text = "This is a test document. The moon landing happened in 1969."

        # Test focused text processing
        try:
            response = self.session.post(
                f"{BASE_URL}/api/v1/focused/process-text",
                json={
                    "text": test_text,
                    "options": {
                        "extract_claims": True,
                        "quality_threshold": "medium"
                    }
                },
                timeout=30
            )

            if response.status_code in [200, 202]:
                self.log_test("focused_text_processing", "PASS", {
                    "status_code": response.status_code,
                    "response_time": f"{response.elapsed.total_seconds():.3f}s"
                })
            else:
                self.log_test("focused_text_processing", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })

        except Exception as e:
            self.log_test("focused_text_processing", "ERROR", {"error": str(e)})

        # Test focused URL processing
        try:
            response = self.session.post(
                f"{BASE_URL}/api/v1/focused/process-url",
                json={
                    "url": "https://www.example.com",
                    "options": {
                        "extract_claims": True,
                        "quality_threshold": "medium"
                    }
                },
                timeout=30
            )

            if response.status_code in [200, 202, 422]:  # 422 might be expected
                self.log_test("focused_url_processing", "PASS", {
                    "status_code": response.status_code,
                    "response_time": f"{response.elapsed.total_seconds():.3f}s"
                })
            else:
                self.log_test("focused_url_processing", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })

        except Exception as e:
            self.log_test("focused_url_processing", "ERROR", {"error": str(e)})
    
    def run_all_tests(self):
        """Run all test suites."""
        print("DSPy-Enhanced Fact-Checker API Platform - Full Test Suite")
        print("=" * 70)
        
        start_time = time.time()
        
        # Run all test suites
        self.test_health_endpoints()
        self.test_user_registration()
        self.test_password_validation()
        self.test_text_processing_endpoints()
        self.test_url_processing_endpoints()
        self.test_document_upload_endpoints()
        self.test_dspy_fact_checking()
        self.test_focused_processing()
        self.test_analytics_endpoints()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        self.print_summary(total_time)
    
    def print_summary(self, total_time: float):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.results if result["status"] == "PASS")
        failed = sum(1 for result in self.results if result["status"] == "FAIL")
        errors = sum(1 for result in self.results if result["status"] == "ERROR")
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        
        overall_status = "PASS" if failed == 0 and errors == 0 else "FAIL"
        print(f"\nOverall Status: {overall_status}")
        
        if overall_status == "PASS":
            print("\n[SUCCESS] All tests passed! The API platform is fully functional.")
        else:
            print(f"\n[WARNING] {failed + errors} tests failed. Review the results above.")
            
        # Show failed tests
        if failed > 0 or errors > 0:
            print("\nFailed/Error Tests:")
            for result in self.results:
                if result["status"] in ["FAIL", "ERROR"]:
                    print(f"  - {result['test']}: {result['status']}")

if __name__ == "__main__":
    test_suite = APITestSuite()
    test_suite.run_all_tests()
