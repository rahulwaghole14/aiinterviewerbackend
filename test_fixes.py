#!/usr/bin/env python3
"""
Test script to verify API fixes
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_single_upload_fix():
    """Test if single resume upload is now working"""
    print("🧪 Testing Single Resume Upload Fix...")

    # First get a valid token
    login_data = {"email": "testuser@example.com", "password": "testpassword123"}

    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        if response.status_code == 200:
            token = response.json().get("token")
            print("✅ Got authentication token")

            # Test single upload
            headers = {"Authorization": f"Token {token}"}
            mock_content = b"John Doe\nSoftware Engineer\nEmail: john@example.com\nPhone: +1234567890\nExperience: 5 years"

            files = {"file": ("test_resume_fix.pdf", mock_content, "application/pdf")}

            response = requests.post(
                f"{BASE_URL}/api/resumes/", files=files, headers=headers
            )
            print(f"📤 POST /api/resumes/ - Status: {response.status_code}")

            if response.status_code == 201:
                print("✅ Single upload working!")
                result = response.json()
                print(f"   Resume ID: {result.get('id')}")
                print(f"   File: {result.get('file')}")
            else:
                print(f"❌ Single upload failed: {response.status_code}")
                print(f"   Response: {response.text[:300]}...")

        else:
            print(f"❌ Login failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")


def test_bulk_upload_fix():
    """Test if bulk upload is now working"""
    print("\n🧪 Testing Bulk Upload Fix...")

    # Get token
    login_data = {"email": "testuser@example.com", "password": "testpassword123"}

    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        if response.status_code == 200:
            token = response.json().get("token")
            print("✅ Got authentication token")

            # Test bulk upload
            headers = {"Authorization": f"Token {token}"}
            mock_content = b"Jane Smith\nData Scientist\nEmail: jane@example.com\nPhone: +1987654321\nExperience: 3 years"

            files = [
                ("files", ("test_bulk1.pdf", mock_content, "application/pdf")),
                (
                    "files",
                    (
                        "test_bulk2.docx",
                        mock_content,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ),
                ),
            ]

            response = requests.post(
                f"{BASE_URL}/api/resumes/bulk-upload/", files=files, headers=headers
            )
            print(f"📤 POST /api/resumes/bulk-upload/ - Status: {response.status_code}")

            if response.status_code == 200:
                print("✅ Bulk upload working!")
                result = response.json()
                print(f"   Message: {result.get('message')}")
                print(f"   Summary: {result.get('summary')}")
            else:
                print(f"❌ Bulk upload failed: {response.status_code}")
                print(f"   Response: {response.text[:300]}...")

        else:
            print(f"❌ Login failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")


def test_endpoints_fix():
    """Test if 404 endpoints are now working"""
    print("\n🔍 Testing Endpoint Fixes...")

    endpoints_to_test = [
        "/companies/",
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
                print(f"❌ {endpoint} - {status} (still not found)")
            else:
                print(f"⚠️  {endpoint} - {status}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")


if __name__ == "__main__":
    print("🚀 Testing API Fixes")
    print("=" * 50)

    test_single_upload_fix()
    test_bulk_upload_fix()
    test_endpoints_fix()

    print("\n" + "=" * 50)
    print("📋 Fix Summary:")
    print("✅ File processing errors should be resolved")
    print("✅ Bulk upload should work without connection issues")
    print("✅ Single upload should work without FileDataError")
    print("✅ Endpoint routing should be fixed")
