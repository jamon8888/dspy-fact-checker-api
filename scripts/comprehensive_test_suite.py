#!/usr/bin/env python3
"""
Comprehensive Test Suite for DSPy-Enhanced Fact-Checker API Platform
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8006"

def test_health_check() -> Dict[str, Any]:
    """Test API health check endpoint."""
    print("\n=== Testing Health Check ===")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        result = {
            "test": "health_check",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds()
        }
        
        if response.status_code == 200:
            health_data = response.json()
            result["components"] = {
                "database": health_data["components"]["database"]["status"],
                "redis": health_data["components"]["redis"]["status"],
                "qdrant": health_data["components"]["qdrant"]["status"],
                "celery": health_data["components"]["celery"]["status"]
            }
        
        print(f"Status: {result['status']} ({result['status_code']})")
        print(f"Response Time: {result['response_time']:.3f}s")
        
        return result
        
    except Exception as e:
        return {
            "test": "health_check",
            "status": "ERROR",
            "error": str(e)
        }

def test_user_registration() -> Dict[str, Any]:
    """Test user registration functionality."""
    print("\n=== Testing User Registration ===")
    
    test_user = {
        "email": f"test_user_{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=test_user,
            timeout=10
        )
        
        result = {
            "test": "user_registration",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds()
        }
        
        if response.status_code == 200:
            user_data = response.json()
            result["user_id"] = user_data.get("id")
            result["email"] = user_data.get("email")
        else:
            result["error"] = response.text
        
        print(f"Status: {result['status']} ({result['status_code']})")
        print(f"Response Time: {result['response_time']:.3f}s")
        
        return result
        
    except Exception as e:
        return {
            "test": "user_registration",
            "status": "ERROR",
            "error": str(e)
        }

def test_password_validation() -> Dict[str, Any]:
    """Test password validation rules."""
    print("\n=== Testing Password Validation ===")
    
    test_cases = [
        ("ValidPassword123!", True, "Valid strong password"),
        ("weak", False, "Too short"),
        ("nouppercase123!", False, "No uppercase"),
        ("NOLOWERCASE123!", False, "No lowercase"),
        ("NoNumbers!", False, "No numbers"),
        ("ValidPassword123", True, "Valid without special chars")
    ]
    
    results = []
    
    for password, should_pass, description in test_cases:
        test_user = {
            "email": f"test_pwd_{hash(password)}@example.com",
            "password": password,
            "first_name": "Test",
            "last_name": "User"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/register",
                json=test_user,
                timeout=10
            )
            
            actual_pass = response.status_code == 200
            test_result = {
                "password": password,
                "description": description,
                "expected": should_pass,
                "actual": actual_pass,
                "status": "PASS" if should_pass == actual_pass else "FAIL",
                "status_code": response.status_code
            }
            
            results.append(test_result)
            print(f"  {description}: {test_result['status']} (expected: {should_pass}, got: {actual_pass})")
            
        except Exception as e:
            results.append({
                "password": password,
                "description": description,
                "status": "ERROR",
                "error": str(e)
            })
    
    overall_status = "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL"
    
    return {
        "test": "password_validation",
        "status": overall_status,
        "results": results
    }

def test_api_documentation() -> Dict[str, Any]:
    """Test API documentation endpoints."""
    print("\n=== Testing API Documentation ===")
    
    endpoints = [
        ("/docs", "Swagger UI"),
        ("/redoc", "ReDoc"),
        ("/openapi.json", "OpenAPI Schema")
    ]
    
    results = []
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            result = {
                "endpoint": endpoint,
                "description": description,
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", "Unknown")
            }
            results.append(result)
            print(f"  {description}: {result['status']} ({result['status_code']})")
            
        except Exception as e:
            results.append({
                "endpoint": endpoint,
                "description": description,
                "status": "ERROR",
                "error": str(e)
            })
    
    overall_status = "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL"
    
    return {
        "test": "api_documentation",
        "status": overall_status,
        "results": results
    }

def run_comprehensive_tests():
    """Run all tests and generate a comprehensive report."""
    print("DSPy-Enhanced Fact-Checker API Platform - Comprehensive Test Suite")
    print("=" * 70)
    
    start_time = time.time()
    
    # Run all tests
    test_results = [
        test_health_check(),
        test_user_registration(),
        test_password_validation(),
        test_api_documentation()
    ]
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Generate summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for result in test_results if result["status"] == "PASS")
    failed = sum(1 for result in test_results if result["status"] == "FAIL")
    errors = sum(1 for result in test_results if result["status"] == "ERROR")

    for result in test_results:
        status_icon = "[PASS]" if result["status"] == "PASS" else "[FAIL]" if result["status"] == "FAIL" else "[ERROR]"
        print(f"{status_icon} {result['test']}: {result['status']}")

    print(f"\nResults: {passed} PASSED, {failed} FAILED, {errors} ERRORS")
    print(f"Total Time: {total_time:.2f} seconds")

    overall_status = "PASS" if failed == 0 and errors == 0 else "FAIL"
    print(f"\nOverall Status: {overall_status}")

    if overall_status == "PASS":
        print("\n[SUCCESS] All tests passed! The API platform is ready for production.")
    else:
        print("\n[WARNING] Some tests failed. Please review the results above.")
    
    return {
        "overall_status": overall_status,
        "summary": {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total_time": total_time
        },
        "results": test_results
    }

if __name__ == "__main__":
    run_comprehensive_tests()
