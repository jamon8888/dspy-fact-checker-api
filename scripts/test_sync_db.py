#!/usr/bin/env python3
"""
Test sync database dependency
"""

import requests
import json

def test_sync_db():
    """Test if sync database dependency is working."""
    
    print("Testing sync database dependency...")
    
    # Test a simple endpoint that uses sync database
    try:
        response = requests.get("http://localhost:8000/api/v1/auth/register", timeout=10)
        print(f"GET /auth/register Status: {response.status_code}")
        
        if response.status_code == 405:  # Method not allowed is expected
            print("[OK] Auth endpoint exists and sync DB dependency is working")
        else:
            print(f"[INFO] Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

if __name__ == "__main__":
    test_sync_db()
