#!/usr/bin/env python3
"""
Simple test script to check existing users and test permissions
"""

import requests
import json
import io

BASE_URL = "http://localhost:8000"


def get_user_token(email, password):
    """Get authentication token for a user"""
    login_data = {"email": email, "password": password}

    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        if response.status_code == 200:
            token = response.json().get("token")
            return token
        else:
            print(f"❌ Login failed for {email}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Login error for {email}: {e}")
        return None


def test_user_permissions(token, user_type):
    """Test permissions for a user"""
    print(f"\n🔍 Testing {user_type} Permissions...")

    headers = {"Authorization": f"Token {token}"}

    # Test resume upload
    mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Resume) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"

    files = {
        "file": ("test_resume.pdf", io.BytesIO(mock_pdf_content), "application/pdf")
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/resumes/", files=files, headers=headers
        )
        print(f"📤 POST /api/resumes/ - Status: {response.status_code}")

        if response.status_code == 201:
            print(f"✅ {user_type} can upload resumes!")
        elif response.status_code == 403:
            print(f"❌ {user_type} blocked from uploading resumes (403 Forbidden)")
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test interview scheduling
    try:
        response = requests.get(f"{BASE_URL}/api/interviews/", headers=headers)
        print(f"📤 GET /api/interviews/ - Status: {response.status_code}")

        if response.status_code == 200:
            interviews = response.json()
            print(f"✅ {user_type} can list interviews ({len(interviews)} found)")
        else:
            print(f"❌ {user_type} cannot list interviews: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🚀 Simple Permission Test")
    print("=" * 50)

    # Test with some common email patterns
    test_emails = [
        ("admin@test.com", "adminpass123", "ADMIN"),
        ("admin@example.com", "adminpass123", "ADMIN"),
        ("test@test.com", "testpass123", "TEST"),
        ("user@test.com", "userpass123", "USER"),
    ]

    for email, password, user_type in test_emails:
        token = get_user_token(email, password)
        if token:
            test_user_permissions(token, user_type)
        else:
            print(f"❌ Could not get token for {email}")

    print("\n" + "=" * 50)
    print("📋 Test Complete")
