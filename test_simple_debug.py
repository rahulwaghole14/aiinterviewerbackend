#!/usr/bin/env python3
"""
Simple debug script to test specific issues
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


def test_recurring_slots_simple(token):
    """Test recurring slot creation with minimal data"""
    print("\n=== Testing Recurring Slot Creation (Simple) ===")

    headers = {"Authorization": f"Token {token}"}

    # Get a company ID
    try:
        response = requests.get(f"{BASE_URL}/api/companies/", headers=headers)
        if response.status_code == 200:
            companies = response.json()
            if companies:
                company_id = companies[0]["id"]
                print(f"Using company ID: {company_id}")
            else:
                print("No companies found")
                return
        else:
            print(f"Failed to get companies: {response.status_code}")
            return
    except Exception as e:
        print(f"Error getting companies: {e}")
        return

    # Create recurring slots for tomorrow only
    tomorrow = datetime.now() + timedelta(days=1)

    data = {
        "company_id": company_id,
        "start_date": tomorrow.strftime("%Y-%m-%d"),
        "end_date": tomorrow.strftime("%Y-%m-%d"),
        "days_of_week": [1, 2, 3, 4, 5],  # Monday to Friday
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "ai_interview_type": "behavioral",
        "ai_configuration": {
            "difficulty_level": "beginner",
            "question_count": 8,
            "time_limit": 45,
        },
        "max_candidates_per_slot": 1,
    }

    print(f"Request data: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/interviews/slots/create_recurring/",
            json=data,
            headers=headers,
        )
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")

        if response.status_code == 201:
            result = response.json()
            print(f"✅ Created {result.get('created_slots', 0)} recurring slots")
            if result.get("skipped_slots"):
                print(f"Skipped slots: {result['skipped_slots']}")
        else:
            print(f"❌ Failed to create recurring slots")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_interview_creation_simple(token):
    """Test interview creation with minimal data"""
    print("\n=== Testing Interview Creation (Simple) ===")

    headers = {"Authorization": f"Token {token}"}

    # Get an existing candidate
    try:
        response = requests.get(f"{BASE_URL}/api/candidates/", headers=headers)
        if response.status_code == 200:
            candidates = response.json()
            if candidates:
                candidate_id = candidates[0]["id"]
                print(f"Using existing candidate ID: {candidate_id}")
            else:
                print("No candidates found")
                return
        else:
            print(f"Failed to get candidates: {response.status_code}")
            return
    except Exception as e:
        print(f"Error getting candidates: {e}")
        return

    # Create an interview
    interview_data = {"candidate": candidate_id, "status": "scheduled"}

    print(f"Interview data: {json.dumps(interview_data, indent=2)}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/interviews/", json=interview_data, headers=headers
        )
        print(f"Interview creation response: {response.status_code}")
        print(f"Interview creation text: {response.text}")

        if response.status_code == 201:
            result = response.json()
            print(f"✅ Created interview: {result.get('id')}")
            return result.get("id")
        else:
            print(f"❌ Failed to create interview")
            return None
    except Exception as e:
        print(f"❌ Error creating interview: {e}")
        return None


def test_slot_booking_simple(token):
    """Test slot booking with minimal data"""
    print("\n=== Testing Slot Booking (Simple) ===")

    headers = {"Authorization": f"Token {token}"}

    # Get an available slot
    try:
        response = requests.get(f"{BASE_URL}/api/interviews/slots/", headers=headers)
        if response.status_code == 200:
            slots = response.json()
            if isinstance(slots, dict):
                slots = slots.get("results", [])

            available_slot = None
            for slot in slots:
                if slot.get("status") == "available":
                    available_slot = slot
                    break

            if available_slot:
                slot_id = available_slot["id"]
                print(f"Found available slot: {slot_id}")
            else:
                print("No available slots found")
                return
        else:
            print(f"Failed to get slots: {response.status_code}")
            return
    except Exception as e:
        print(f"Error getting slots: {e}")
        return

    # Get an existing interview
    try:
        response = requests.get(f"{BASE_URL}/api/interviews/", headers=headers)
        if response.status_code == 200:
            interviews = response.json()
            if interviews:
                interview_id = interviews[0]["id"]
                print(f"Using existing interview ID: {interview_id}")
            else:
                print("No interviews found")
                return
        else:
            print(f"Failed to get interviews: {response.status_code}")
            return
    except Exception as e:
        print(f"Error getting interviews: {e}")
        return

    # Book the slot
    booking_data = {"interview_id": interview_id, "booking_notes": "Test booking"}

    print(f"Booking data: {json.dumps(booking_data, indent=2)}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/interviews/slots/{slot_id}/book_slot/",
            json=booking_data,
            headers=headers,
        )
        print(f"Slot booking response: {response.status_code}")
        print(f"Slot booking text: {response.text}")

        if response.status_code == 201:
            result = response.json()
            print(f"✅ Booked slot successfully")
            return result
        else:
            print(f"❌ Failed to book slot")
            return None
    except Exception as e:
        print(f"❌ Error booking slot: {e}")
        return None


def main():
    print("🔍 Simple Debug Tests")

    # Login
    token = login_user(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not token:
        print("❌ Failed to login")
        return

    print("✅ Login successful")

    # Test recurring slots
    test_recurring_slots_simple(token)

    # Test interview creation
    test_interview_creation_simple(token)

    # Test slot booking
    test_slot_booking_simple(token)

    print("\n✅ Simple debug tests completed!")


if __name__ == "__main__":
    main()
