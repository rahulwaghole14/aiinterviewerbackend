#!/usr/bin/env python3
"""
Simple test for bulk upload endpoint
"""

import requests

BASE_URL = "http://localhost:8000"

def test_bulk_endpoint():
    """Test if bulk upload endpoint is accessible"""
    print("🔍 Testing bulk upload endpoint accessibility...")
    
    # Test GET request to see if endpoint exists
    try:
        response = requests.get(f"{BASE_URL}/api/resumes/bulk-upload/")
        print(f"📤 GET /api/resumes/bulk-upload/ - Status: {response.status_code}")
        if response.status_code == 405:
            print("   ✅ Endpoint exists (GET not allowed, POST should work)")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test POST with minimal data
    try:
        headers = {'Authorization': 'Token 17fcaaae25380d72f89d'}
        response = requests.post(f"{BASE_URL}/api/resumes/bulk-upload/", 
                               headers=headers)
        print(f"📤 POST /api/resumes/bulk-upload/ - Status: {response.status_code}")
        print(f"   Response: {response.text[:300]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_bulk_endpoint() 