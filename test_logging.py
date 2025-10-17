#!/usr/bin/env python3
"""
Test script to verify logging implementation
"""

import requests
import json
import io
import time

BASE_URL = "http://localhost:8000"


def test_logging():
    """Test various actions to verify logging"""
    print("🧪 Testing Logging Implementation")
    print("=" * 50)

    # Test 1: User Registration
    print("\n📝 Test 1: User Registration")
    registration_data = {
        "username": "test_logger@test.com",
        "email": "test_logger@test.com",
        "password": "testpass123",
        "full_name": "Test Logger User",
        "company_name": "Test Company",
        "role": "HIRING_MANAGER",
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/register/", data=registration_data)
        print(f"Registration Status: {response.status_code}")
        if response.status_code == 201:
            print("✅ Registration successful - should be logged")
        else:
            print(f"❌ Registration failed: {response.text}")
    except Exception as e:
        print(f"❌ Registration error: {e}")

    # Test 2: User Login
    print("\n🔐 Test 2: User Login")
    login_data = {"email": "test_logger@test.com", "password": "testpass123"}

    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        print(f"Login Status: {response.status_code}")
        if response.status_code == 200:
            token = response.json().get("token")
            print("✅ Login successful - should be logged")
        else:
            print(f"❌ Login failed: {response.text}")
            token = None
    except Exception as e:
        print(f"❌ Login error: {e}")
        token = None

    # Test 3: Resume Upload (with permission)
    if token:
        print("\n📄 Test 3: Resume Upload (with permission)")
        headers = {"Authorization": f"Token {token}"}

        # Create a mock PDF file
        mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Resume) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"

        files = {
            "file": ("test_resume.pdf", io.BytesIO(mock_pdf_content), "application/pdf")
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/resumes/", files=files, headers=headers
            )
            print(f"Resume Upload Status: {response.status_code}")
            if response.status_code == 201:
                print("✅ Resume upload successful - should be logged")
            else:
                print(f"❌ Resume upload failed: {response.text}")
        except Exception as e:
            print(f"❌ Resume upload error: {e}")

    # Test 4: Resume Upload (without permission - should be blocked)
    print("\n🚫 Test 4: Resume Upload (without permission)")
    try:
        response = requests.post(f"{BASE_URL}/api/resumes/", files=files)  # No token
        print(f"Unauthorized Upload Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Unauthorized access blocked - should be logged")
        else:
            print(f"❌ Unexpected response: {response.text}")
    except Exception as e:
        print(f"❌ Unauthorized upload error: {e}")

    # Test 5: Interview Listing
    if token:
        print("\n📅 Test 5: Interview Listing")
        try:
            response = requests.get(f"{BASE_URL}/api/interviews/", headers=headers)
            print(f"Interview Listing Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Interview listing successful - should be logged")
            else:
                print(f"❌ Interview listing failed: {response.text}")
        except Exception as e:
            print(f"❌ Interview listing error: {e}")

    # Test 6: Invalid Login Attempt
    print("\n❌ Test 6: Invalid Login Attempt")
    invalid_login_data = {"email": "test_logger@test.com", "password": "wrongpassword"}

    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=invalid_login_data)
        print(f"Invalid Login Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Invalid login blocked - should be logged")
        else:
            print(f"❌ Unexpected response: {response.text}")
    except Exception as e:
        print(f"❌ Invalid login error: {e}")

    print("\n" + "=" * 50)
    print("📋 Logging Test Complete")
    print("Check the following log files:")
    print("- logs/ai_interviewer.log (main application logs)")
    print("- logs/security.log (security events)")
    print("\nExpected logged events:")
    print("✅ User registration")
    print("✅ User login")
    print("✅ Resume upload")
    print("✅ Permission denied (unauthorized access)")
    print("✅ Interview listing")
    print("✅ Invalid login attempt")
    print("✅ API request/response logging")


if __name__ == "__main__":
    test_logging()
