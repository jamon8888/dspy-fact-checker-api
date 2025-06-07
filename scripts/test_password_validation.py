#!/usr/bin/env python3
"""
Test password validation specifically
"""

import requests
import json

def test_password_validation():
    """Test different password formats to identify validation issues."""
    
    passwords_to_test = [
        ("TestPassword123!", "Strong password with all requirements"),
        ("testpassword123", "No uppercase or special char"),
        ("TESTPASSWORD123", "No lowercase"),
        ("TestPassword", "No numbers or special char"),
        ("Test123", "Too short"),
        ("TestPassword123", "No special char"),
        ("TestPassword!", "No numbers"),
        ("testpassword123!", "No uppercase"),
    ]
    
    for password, description in passwords_to_test:
        print(f"\nTesting: {description}")
        print(f"Password: {password}")
        
        register_data = {
            "email": f"test_{hash(password)}@example.com",
            "password": password,
            "first_name": "Test",
            "last_name": "User"
        }
        
        try:
            response = requests.post(
                "http://localhost:8006/api/v1/auth/register",
                json=register_data,
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 422:  # Validation error
                try:
                    error_data = response.json()
                    print(f"Validation Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Response: {response.text}")
            elif response.status_code == 201:
                print("[SUCCESS] Registration successful!")
                break
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    print(f"Server Error: {error_data.get('message', 'Unknown error')}")
                except:
                    print(f"Server Error: {response.text}")
            else:
                print(f"Unexpected status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    test_password_validation()
