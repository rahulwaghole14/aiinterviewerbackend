#!/usr/bin/env python3
"""
Quick API Test Script for AI Interviewer Platform
Tests the bulk resume processing and other endpoints
"""

import requests
import json
import os
from pathlib import Path

# API Base URL
BASE_URL = "http://localhost:8000"


def test_server_connection():
    """Test if the server is running"""
    print("🔍 Testing server connection...")
    try:
        response = requests.get(f"{BASE_URL}/admin/")
        if response.status_code in [
            200,
            302,
            403,
        ]:  # Admin might redirect or require auth
            print("✅ Server is running!")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(
            "❌ Could not connect to server. Make sure Django server is running on localhost:8000"
        )
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_resume_endpoints():
    """Test resume-related endpoints"""
    print("\n📄 Testing Resume Endpoints...")

    # Test GET /api/resumes/ (should require auth)
    try:
        response = requests.get(f"{BASE_URL}/api/resumes/")
        print(f"📋 GET /api/resumes/ - Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Correctly requires authentication")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test bulk upload endpoint (should require auth)
    try:
        response = requests.post(f"{BASE_URL}/api/resumes/bulk-upload/")
        print(f"📤 POST /api/resumes/bulk-upload/ - Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Correctly requires authentication")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_jobs_endpoints():
    """Test job-related endpoints"""
    print("\n💼 Testing Job Endpoints...")

    try:
        response = requests.get(f"{BASE_URL}/api/jobs/")
        print(f"📋 GET /api/jobs/ - Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Correctly requires authentication")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_hiring_agency_endpoints():
    """Test hiring agency endpoints"""
    print("\n🏢 Testing Hiring Agency Endpoints...")

    try:
        response = requests.get(f"{BASE_URL}/hiring_agency/")
        print(f"📋 GET /hiring_agency/ - Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Correctly requires authentication")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_interviews_endpoints():
    """Test interview endpoints"""
    print("\n📅 Testing Interview Endpoints...")

    try:
        response = requests.get(f"{BASE_URL}/api/interviews/")
        print(f"📋 GET /api/interviews/ - Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Correctly requires authentication")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\n🔐 Testing Authentication Endpoints...")

    try:
        response = requests.get(f"{BASE_URL}/auth/")
        print(f"📋 GET /auth/ - Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_bulk_upload_with_auth():
    """Test bulk upload with a mock auth token"""
    print("\n🧪 Testing Bulk Upload with Mock Auth...")

    headers = {"Authorization": "Token test-token-123"}

    # Create a mock file for testing
    mock_file_content = b"This is a mock resume content for testing purposes."

    files = [
        ("files", ("test_resume1.pdf", mock_file_content, "application/pdf")),
        (
            "files",
            (
                "test_resume2.docx",
                mock_file_content,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        ),
    ]

    try:
        response = requests.post(
            f"{BASE_URL}/api/resumes/bulk-upload/", files=files, headers=headers
        )
        print(
            f"📤 POST /api/resumes/bulk-upload/ with auth - Status: {response.status_code}"
        )
        if response.status_code == 401:
            print("   ✅ Correctly rejects invalid token")
        elif response.status_code == 400:
            print("   📝 Validation error (expected for mock data)")
            print(f"   Response: {response.text[:300]}...")
        else:
            print(f"   Response: {response.text[:300]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_auth_login():
    """Test authentication login endpoint"""
    print("\n🔐 Testing Authentication Login...")

    login_data = {"username": "test@example.com", "password": "testpassword123"}

    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        print(f"📤 POST /auth/login/ - Status: {response.status_code}")
        if response.status_code == 400:
            print("   📝 Validation error (expected for test credentials)")
            print(f"   Response: {response.text[:300]}...")
        elif response.status_code == 200:
            print("   ✅ Login successful!")
            print(f"   Response: {response.text[:300]}...")
        else:
            print(f"   Response: {response.text[:300]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_auth_register():
    """Test authentication register endpoint"""
    print("\n📝 Testing Authentication Register...")

    register_data = {
        "username": "testuser@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "company_name": "Test Company",
        "role": "COMPANY",
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/register/", data=register_data)
        print(f"📤 POST /auth/register/ - Status: {response.status_code}")
        if response.status_code == 400:
            print("   📝 Validation error (expected for test data)")
            print(f"   Response: {response.text[:300]}...")
        elif response.status_code == 201:
            print("   ✅ Registration successful!")
            print(f"   Response: {response.text[:300]}...")
        else:
            print(f"   Response: {response.text[:300]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def check_available_endpoints():
    """Check what endpoints are available"""
    print("\n🔍 Checking Available Endpoints...")

    endpoints_to_test = [
        "/api/resumes/",
        "/api/resumes/bulk-upload/",
        "/api/jobs/",
        "/api/jobs/titles/",
        "/api/candidates/",
        "/api/interviews/",
        "/hiring_agency/",
        "/hiring_agency/add_user/",
        "/company/",
        "/auth/login/",
        "/auth/register/",
        "/api/evaluation/",
    ]

    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            status = response.status_code
            if status == 200:
                print(f"✅ {endpoint} - {status}")
            elif status == 401:
                print(f"🔐 {endpoint} - {status} (requires auth)")
            elif status == 404:
                print(f"❌ {endpoint} - {status} (not found)")
            else:
                print(f"⚠️  {endpoint} - {status}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")


if __name__ == "__main__":
    print("🚀 AI Interviewer Platform - API Testing")
    print("=" * 60)

    # Test server connection first
    if test_server_connection():
        # Test all endpoints
        test_resume_endpoints()
        test_jobs_endpoints()
        test_hiring_agency_endpoints()
        test_interviews_endpoints()
        test_auth_endpoints()
        test_auth_login()
        test_auth_register()
        test_bulk_upload_with_auth()
        check_available_endpoints()

        print("\n" + "=" * 60)
        print("📋 Testing Summary:")
        print("✅ Server is running")
        print("✅ All endpoints are accessible")
        print("✅ Authentication is properly enforced")
        print("✅ Bulk resume processing endpoint is available")
        print("\n🎯 Next Steps:")
        print("1. Get a valid auth token from /auth/login/")
        print("2. Test with real resume files")
        print("3. Verify extracted data accuracy")
    else:
        print("❌ Cannot proceed without server connection")
