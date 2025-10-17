#!/usr/bin/env python3
"""
Simple test for interview slot creation
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "password123"


def login_user(email, password):
    """Login and get authentication token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login/", json={"email": email, "password": password}
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None


def test_slot_creation(token):
    """Test creating a simple interview slot"""
    print("Testing simple slot creation...")

    headers = {"Authorization": f"Token {token}"}

    # Create slot for tomorrow
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    data = {
        "slot_type": "fixed",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_minutes": 60,
        "ai_interview_type": "technical",
        "ai_configuration": {
            "difficulty_level": "intermediate",
            "question_count": 10,
            "time_limit": 60,
        },
        "company": 2,  # Using existing company ID
        "max_candidates": 1,
        "notes": "Test interview slot",
    }

    print(f"Request data: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/interviews/slots/", json=data, headers=headers
        )
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response text: {response.text[:500]}...")

        if response.status_code == 201:
            result = response.json()
            print(f"✅ Slot created successfully: {result.get('id')}")
            return result
        else:
            print(f"❌ Slot creation failed")
            return None
    except Exception as e:
        print(f"❌ Slot creation error: {e}")
        return None


def main():
    print("🚀 Starting simple slot creation test")

    # Login
    token = login_user(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not token:
        print("❌ Failed to login")
        return

    print("✅ Login successful")

    # Test slot creation
    result = test_slot_creation(token)
    if result:
        print("✅ Test passed!")
    else:
        print("❌ Test failed!")


if __name__ == "__main__":
    main()
