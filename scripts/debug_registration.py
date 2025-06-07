#!/usr/bin/env python3
"""
Debug registration endpoint with detailed logging
"""

import requests
import json

def test_endpoints():
    """Test various endpoints to see what's working."""
    
    base_url = "http://localhost:8000"
    
    # Test basic health
    print("=== Testing Basic Health ===")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health Status: {response.status_code}")
        if response.status_code == 200:
            print("[OK] Health endpoint working")
        else:
            print("[FAIL] Health endpoint failed")
    except Exception as e:
        print(f"[ERROR] Health endpoint error: {e}")
    
    # Test API health
    print("\n=== Testing API Health ===")
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=10)
        print(f"API Health Status: {response.status_code}")
        if response.status_code in [200, 307]:  # 307 is redirect
            print("[OK] API health endpoint working")
        else:
            print("[FAIL] API health endpoint failed")
    except Exception as e:
        print(f"[ERROR] API health endpoint error: {e}")
    
    # Test auth endpoint existence
    print("\n=== Testing Auth Endpoint Existence ===")
    try:
        # Try a GET request to see if the endpoint exists
        response = requests.get(f"{base_url}/api/v1/auth/register", timeout=10)
        print(f"Auth GET Status: {response.status_code}")
        if response.status_code == 405:  # Method not allowed is good - endpoint exists
            print("[OK] Auth endpoint exists (Method Not Allowed for GET)")
        elif response.status_code == 404:
            print("[FAIL] Auth endpoint not found")
        else:
            print(f"[INFO] Auth endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Auth endpoint error: {e}")
    
    # Test registration with minimal data
    print("\n=== Testing Registration ===")
    register_data = {
        "email": "debug@example.com",
        "password": "TestPassword123!",
        "first_name": "Debug",
        "last_name": "User"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/register",
            json=register_data,
            timeout=30
        )
        
        print(f"Registration Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"Response JSON: {json.dumps(response_json, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Registration error: {e}")

if __name__ == "__main__":
    test_endpoints()
