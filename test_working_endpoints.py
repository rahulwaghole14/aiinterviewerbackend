#!/usr/bin/env python3
"""
Focused API Testing Script for AI Interviewer Platform
Tests working endpoints and identifies specific issues
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_CREDENTIALS = {
    "company": {
        "email": "company_test@example.com",
        "password": "password123"
    },
    "admin": {
        "email": "admin@rslsolution.com",
        "password": "admin123"
    }
}

def test_endpoint(session, method, endpoint, data=None, description=""):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = session.get(f"{API_BASE}{endpoint}")
        elif method == "POST":
            response = session.post(f"{API_BASE}{endpoint}", json=data)
        elif method == "PATCH":
            response = session.patch(f"{API_BASE}{endpoint}", json=data)
        
        status_icon = "✅" if 200 <= response.status_code < 300 else "❌"
        print(f"{status_icon} {method} {endpoint} - {response.status_code}")
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text[:100]}...")
        
        return response.status_code < 300, response
        
    except Exception as e:
        print(f"❌ {method} {endpoint} - Exception: {str(e)}")
        return False, None

def main():
    print("🚀 Testing AI Interviewer API Endpoints")
    print("=" * 50)
    
    session = requests.Session()
    
    # Test 1: Login
    print("\n🔐 Testing Login...")
    login_data = TEST_CREDENTIALS["company"]
    response = session.post(
        f"{API_BASE}/auth/login/",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        user_id = data.get("user", {}).get("id")
        print(f"✅ Login successful! User ID: {user_id}")
        
        # Set auth header
        session.headers.update({"Authorization": f"Token {token}"})
        
        # Test 2: User Profile (using authapp)
        print("\n👤 Testing User Profile...")
        test_endpoint(session, "GET", "/auth/profile/", description="Get user profile")
        
        # Test 3: Companies
        print("\n🏢 Testing Companies...")
        test_endpoint(session, "GET", "/companies/", description="Get companies list")
        test_endpoint(session, "GET", "/companies/profile/", description="Get company profile")
        
        # Test 4: Jobs
        print("\n💼 Testing Jobs...")
        test_endpoint(session, "GET", "/jobs/", description="Get jobs list")
        test_endpoint(session, "GET", "/jobs/domains/", description="Get domains")
        test_endpoint(session, "GET", "/jobs/domains/active/", description="Get active domains")
        
        # Test 5: Candidates
        print("\n👤 Testing Candidates...")
        test_endpoint(session, "GET", "/candidates/", description="Get candidates list")
        
        # Test 6: Resumes
        print("\n📄 Testing Resumes...")
        test_endpoint(session, "GET", "/resumes/", description="Get resumes list")
        
        # Test 7: Interviews
        print("\n📅 Testing Interviews...")
        test_endpoint(session, "GET", "/interviews/", description="Get interviews list")
        
        # Test 8: Notifications
        print("\n🔔 Testing Notifications...")
        test_endpoint(session, "GET", "/notifications/", description="Get notifications")
        
        # Test 9: Dashboard
        print("\n📊 Testing Dashboard...")
        test_endpoint(session, "GET", "/dashboard/analytics/", description="Get dashboard analytics")
        test_endpoint(session, "GET", "/dashboard/recent-activities/", description="Get recent activities")
        
        # Test 10: Logout
        print("\n🔐 Testing Logout...")
        test_endpoint(session, "POST", "/auth/logout/", description="Logout user")
        
    else:
        print(f"❌ Login failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error: {error_data}")
        except:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    main() 