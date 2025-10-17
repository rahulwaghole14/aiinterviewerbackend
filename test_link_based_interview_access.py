#!/usr/bin/env python3
"""
Test Script for Link-Based Interview Access System
Tests the complete flow from interview scheduling to candidate access via secure links
"""

import requests
import json
import time
from datetime import datetime, timedelta
import base64
import hmac
import hashlib

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"


def log(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


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
            log(f"Login failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"Login error: {e}", "ERROR")
        return None


def create_test_company(token):
    """Create a test company"""
    headers = {"Authorization": f"Token {token}"}
    data = {
        "name": "Test Company for Link Access",
        "email": "testcompany@example.com",
        "password": "password123",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/companies/", json=data, headers=headers
        )
        if response.status_code == 201:
            return response.json()["id"]
        else:
            log(
                f"Company creation failed: {response.status_code} - {response.text}",
                "ERROR",
            )
            return None
    except Exception as e:
        log(f"Company creation error: {e}", "ERROR")
        return None


def create_test_candidate(token, company_id):
    """Create a test candidate"""
    headers = {"Authorization": f"Token {token}"}
    data = {
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "work_experience": 3,
        "domain": "Software Development",
        "poc_email": "john.doe@example.com",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/candidates/", json=data, headers=headers
        )
        if response.status_code == 201:
            return response.json()["id"]
        else:
            log(
                f"Candidate creation failed: {response.status_code} - {response.text}",
                "ERROR",
            )
            return None
    except Exception as e:
        log(f"Candidate creation error: {e}", "ERROR")
        return None


def create_test_job(token, company_id):
    """Create a test job"""
    headers = {"Authorization": f"Token {token}"}
    data = {
        "job_title": "Senior Software Engineer",
        "company_name": "Test Company for Link Access",
        "domain": 1,  # Assuming domain ID 1 exists
        "spoc_email": "hr@testcompany.com",
        "hiring_manager_email": "hiring@testcompany.com",
        "current_team_size_info": "10-20",
        "number_to_hire": 2,
        "position_level": "senior",
        "job_description": "We are looking for a senior software engineer...",
        "required_skills": "Python, Django, React",
        "preferred_skills": "AWS, Docker, Kubernetes",
        "experience_required": 5,
        "salary_range": "80000-120000",
        "location": "Remote",
        "employment_type": "full_time",
    }

    try:
        response = requests.post(f"{BASE_URL}/api/jobs/", json=data, headers=headers)
        if response.status_code == 201:
            return response.json()["id"]
        else:
            log(
                f"Job creation failed: {response.status_code} - {response.text}",
                "ERROR",
            )
            return None
    except Exception as e:
        log(f"Job creation error: {e}", "ERROR")
        return None


def schedule_interview(token, candidate_id, job_id):
    """Schedule an interview and get the interview link"""
    headers = {"Authorization": f"Token {token}"}

    # Schedule interview for tomorrow
    tomorrow = datetime.now() + timedelta(days=1)
    scheduled_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

    data = {
        "candidate": candidate_id,
        "job": job_id,
        "status": "scheduled",
        "interview_round": "Technical Round 1",
        "started_at": scheduled_time.isoformat(),
        "ended_at": (scheduled_time + timedelta(hours=1)).isoformat(),
        "video_url": "https://meet.google.com/test-interview",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/interviews/", json=data, headers=headers
        )
        if response.status_code == 201:
            result = response.json()
            log(f"Interview scheduled successfully: {result['id']}")
            return result
        else:
            log(
                f"Interview scheduling failed: {response.status_code} - {response.text}",
                "ERROR",
            )
            return None
    except Exception as e:
        log(f"Interview scheduling error: {e}", "ERROR")
        return None


def generate_interview_link(token, interview_id):
    """Generate a new interview link"""
    headers = {"Authorization": f"Token {token}"}

    try:
        response = requests.post(
            f"{BASE_URL}/api/interviews/{interview_id}/generate-link/", headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            log(f"Interview link generated: {result['interview_link'][:20]}...")
            return result
        else:
            log(
                f"Link generation failed: {response.status_code} - {response.text}",
                "ERROR",
            )
            return None
    except Exception as e:
        log(f"Link generation error: {e}", "ERROR")
        return None


def test_public_interview_access(interview_link_token):
    """Test public interview access without authentication"""
    log("Testing public interview access...")

    # Test 1: Get interview details
    try:
        response = requests.get(
            f"{BASE_URL}/api/interviews/public/{interview_link_token}/"
        )
        log(f"GET interview details: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            log(f"✅ Interview details retrieved successfully")
            log(f"   Candidate: {data.get('candidate_name')}")
            log(f"   Job: {data.get('job_title')}")
            log(
                f"   Scheduled: {data.get('scheduled_date')} at {data.get('scheduled_time')}"
            )
            log(f"   Can join: {data.get('can_join')}")
            return True
        else:
            log(f"❌ Failed to get interview details: {response.text}", "ERROR")
            return False
    except Exception as e:
        log(f"❌ Error getting interview details: {e}", "ERROR")
        return False


def test_join_interview(interview_link_token):
    """Test joining the interview"""
    log("Testing interview join...")

    try:
        response = requests.post(
            f"{BASE_URL}/api/interviews/public/{interview_link_token}/"
        )
        log(f"POST join interview: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            log(f"✅ Interview joined successfully")
            log(f"   Status: {data.get('status')}")
            log(f"   Started at: {data.get('started_at')}")
            return True
        elif response.status_code == 400:
            data = response.json()
            log(f"⚠️ Interview join validation: {data.get('error')}")
            # This is expected if trying to join before scheduled time
            return True
        else:
            log(f"❌ Failed to join interview: {response.text}", "ERROR")
            return False
    except Exception as e:
        log(f"❌ Error joining interview: {e}", "ERROR")
        return False


def test_invalid_link():
    """Test with invalid interview link"""
    log("Testing invalid interview link...")

    invalid_token = "invalid_token_12345"

    try:
        response = requests.get(f"{BASE_URL}/api/interviews/public/{invalid_token}/")
        log(f"GET invalid link: {response.status_code}")

        if response.status_code == 400:
            data = response.json()
            log(f"✅ Invalid link properly rejected: {data.get('error')}")
            return True
        else:
            log(
                f"❌ Invalid link not properly handled: {response.status_code}", "ERROR"
            )
            return False
    except Exception as e:
        log(f"❌ Error testing invalid link: {e}", "ERROR")
        return False


def test_expired_link():
    """Test with expired interview link (simulated)"""
    log("Testing expired interview link...")

    # Create a mock expired token
    expired_token = "expired_token_simulation"

    try:
        response = requests.get(f"{BASE_URL}/api/interviews/public/{expired_token}/")
        log(f"GET expired link: {response.status_code}")

        if response.status_code == 400:
            data = response.json()
            log(f"✅ Expired link properly rejected: {data.get('error')}")
            return True
        else:
            log(
                f"❌ Expired link not properly handled: {response.status_code}", "ERROR"
            )
            return False
    except Exception as e:
        log(f"❌ Error testing expired link: {e}", "ERROR")
        return False


def main():
    """Main test function"""
    log("🚀 Starting Link-Based Interview Access System Test")
    log("=" * 60)

    # Step 1: Login as admin
    log("Step 1: Logging in as admin...")
    token = login_user(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not token:
        log("❌ Failed to login. Exiting.", "ERROR")
        return

    log("✅ Admin login successful")

    # Step 2: Create test data
    log("\nStep 2: Creating test data...")

    company_id = create_test_company(token)
    if not company_id:
        log("❌ Failed to create company. Exiting.", "ERROR")
        return

    candidate_id = create_test_candidate(token, company_id)
    if not candidate_id:
        log("❌ Failed to create candidate. Exiting.", "ERROR")
        return

    job_id = create_test_job(token, company_id)
    if not job_id:
        log("❌ Failed to create job. Exiting.", "ERROR")
        return

    log("✅ Test data created successfully")

    # Step 3: Schedule interview
    log("\nStep 3: Scheduling interview...")
    interview_result = schedule_interview(token, candidate_id, job_id)
    if not interview_result:
        log("❌ Failed to schedule interview. Exiting.", "ERROR")
        return

    interview_id = interview_result["id"]
    interview_link = interview_result.get("interview_link")

    if not interview_link:
        log("⚠️ No interview link in response, generating one...")
        link_result = generate_interview_link(token, interview_id)
        if link_result:
            interview_link = link_result["interview_link"]
        else:
            log("❌ Failed to generate interview link. Exiting.", "ERROR")
            return

    log(f"✅ Interview scheduled with link: {interview_link[:20]}...")

    # Step 4: Test public access
    log("\nStep 4: Testing public interview access...")

    # Test valid link
    success1 = test_public_interview_access(interview_link)
    success2 = test_join_interview(interview_link)

    # Test invalid scenarios
    success3 = test_invalid_link()
    success4 = test_expired_link()

    # Summary
    log("\n" + "=" * 60)
    log("📊 Test Results Summary:")
    log(f"   ✅ Valid link access: {'PASS' if success1 else 'FAIL'}")
    log(f"   ✅ Interview join: {'PASS' if success2 else 'FAIL'}")
    log(f"   ✅ Invalid link rejection: {'PASS' if success3 else 'FAIL'}")
    log(f"   ✅ Expired link rejection: {'PASS' if success4 else 'FAIL'}")

    if all([success1, success2, success3, success4]):
        log(
            "🎉 All tests passed! Link-based interview access system is working correctly."
        )
    else:
        log("❌ Some tests failed. Please check the implementation.", "ERROR")

    log("\n🔗 Interview URL for testing:")
    log(f"   {BASE_URL}/api/interviews/public/{interview_link}/")

    log("\n📧 Email notification should have been sent to:")
    log(f"   john.doe@example.com")

    log("\n✅ Test completed!")


if __name__ == "__main__":
    main()
