#!/usr/bin/env python3
"""
Test registration endpoint specifically
"""

import requests
import json

def test_registration():
    """Test user registration with detailed error reporting."""
    
    register_data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    print("Testing user registration...")
    print(f"Data: {json.dumps(register_data, indent=2)}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/register",
            json=register_data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"Response JSON: {json.dumps(response_json, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_registration()
