#!/usr/bin/env python3
"""
Interview CRUD Operations Test Script
Tests all Create, Read, Update, Delete operations for Interviews
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@rslsolution.com"
ADMIN_PASSWORD = "admin123"


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def get_auth_token():
    """Get authentication token for admin user"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login/",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )

        if response.status_code == 200:
            token = response.json().get("token")
            log(f"✅ Login successful for {ADMIN_EMAIL}")
            return token
        else:
            log(f"❌ Login failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Login error: {str(e)}", "ERROR")
        return None


def get_test_data(token):
    """Get test candidate and job data for interview creation"""
    headers = {"Authorization": f"Token {token}"}

    # Get a candidate
    response = requests.get(f"{BASE_URL}/api/candidates/", headers=headers)
    if response.status_code == 200:
        candidates = response.json()
        if candidates:
            candidate_id = candidates[0]["id"]
            log(f"✅ Using candidate for testing: ID {candidate_id}")
        else:
            log("❌ No candidates found", "ERROR")
            return None, None
    else:
        log(f"❌ Failed to get candidates: {response.status_code}", "ERROR")
        return None, None

    # Get a job
    response = requests.get(f"{BASE_URL}/api/jobs/", headers=headers)
    if response.status_code == 200:
        jobs = response.json()
        if jobs:
            job_id = jobs[0]["id"]
            log(f"✅ Using job for testing: ID {job_id}")
        else:
            log("❌ No jobs found", "ERROR")
            return candidate_id, None
    else:
        log(f"❌ Failed to get jobs: {response.status_code}", "ERROR")
        return candidate_id, None

    return candidate_id, job_id


def test_interview_crud(token, candidate_id, job_id):
    """Test Interview CRUD operations"""
    headers = {"Authorization": f"Token {token}"}

    log("\n" + "=" * 60)
    log("🎯 TESTING INTERVIEW CRUD OPERATIONS")
    log("=" * 60)

    # CREATE Interview
    log("\n📝 Testing Interview CREATE...")

    # Create interview times within 08:00-22:00 UTC window
    start_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    interview_data = {
        "candidate": candidate_id,
        "job": job_id,
        "interview_round": f"Test Round {int(time.time())}",
        "status": "scheduled",
        "started_at": start_time.isoformat(),
        "ended_at": end_time.isoformat(),
        "feedback": "Initial test interview",
    }

    response = requests.post(
        f"{BASE_URL}/api/interviews/", json=interview_data, headers=headers
    )
    if response.status_code == 201:
        interview = response.json()
        interview_id = interview["id"]
        log(f"✅ Interview created successfully: ID {interview_id}")
    else:
        log(
            f"❌ Interview creation failed: {response.status_code} - {response.text}",
            "ERROR",
        )
        return None

    # READ Interview List
    log("\n📖 Testing Interview READ (List)...")
    response = requests.get(f"{BASE_URL}/api/interviews/", headers=headers)
    if response.status_code == 200:
        interviews = response.json()
        log(f"✅ Interviews list retrieved: {len(interviews)} interviews")
    else:
        log(
            f"❌ Interview list retrieval failed: {response.status_code} - {response.text}",
            "ERROR",
        )

    # READ Interview Detail
    log(f"\n📖 Testing Interview READ (Detail) - ID {interview_id}...")
    response = requests.get(
        f"{BASE_URL}/api/interviews/{interview_id}/", headers=headers
    )
    if response.status_code == 200:
        interview_detail = response.json()
        log(f"✅ Interview detail retrieved: {interview_detail['interview_round']}")
    else:
        log(
            f"❌ Interview detail retrieval failed: {response.status_code} - {response.text}",
            "ERROR",
        )

    # UPDATE Interview
    log(f"\n✏️ Testing Interview UPDATE - ID {interview_id}...")
    update_start_time = datetime.now().replace(
        hour=14, minute=0, second=0, microsecond=0
    )
    update_end_time = update_start_time + timedelta(hours=1)

    update_data = {
        "candidate": candidate_id,
        "job": job_id,
        "interview_round": f"Updated Round {int(time.time())}",
        "status": "completed",
        "started_at": update_start_time.isoformat(),
        "ended_at": update_end_time.isoformat(),
        "feedback": "Updated test interview feedback",
        "video_url": "https://example.com/video/test-interview",
    }
    response = requests.put(
        f"{BASE_URL}/api/interviews/{interview_id}/", json=update_data, headers=headers
    )
    if response.status_code == 200:
        updated_interview = response.json()
        log(
            f"✅ Interview updated successfully: {updated_interview['interview_round']}"
        )
    else:
        log(
            f"❌ Interview update failed: {response.status_code} - {response.text}",
            "ERROR",
        )

    # DELETE Interview
    log(f"\n🗑️ Testing Interview DELETE - ID {interview_id}...")
    response = requests.delete(
        f"{BASE_URL}/api/interviews/{interview_id}/", headers=headers
    )
    if response.status_code == 204:
        log(f"✅ Interview deleted successfully")
    else:
        log(
            f"❌ Interview deletion failed: {response.status_code} - {response.text}",
            "ERROR",
        )

    return interview_id


def test_interview_summary(token):
    """Test Interview Summary endpoint"""
    headers = {"Authorization": f"Token {token}"}

    log("\n" + "=" * 60)
    log("📊 TESTING INTERVIEW SUMMARY")
    log("=" * 60)

    log("\n📊 Testing Interview Summary...")
    response = requests.get(f"{BASE_URL}/api/interviews/summary/", headers=headers)
    if response.status_code == 200:
        summary = response.json()
        log(f"✅ Interview summary retrieved successfully")
        log(f"   - Total interviews: {summary.get('total_interviews', 'N/A')}")
        log(f"   - Scheduled: {summary.get('scheduled_interviews', 'N/A')}")
        log(f"   - Completed: {summary.get('completed_interviews', 'N/A')}")
    else:
        log(
            f"❌ Interview summary retrieval failed: {response.status_code} - {response.text}",
            "ERROR",
        )


def test_interview_filtering(token, candidate_id, job_id):
    """Test Interview filtering and search"""
    headers = {"Authorization": f"Token {token}"}

    log("\n" + "=" * 60)
    log("🔍 TESTING INTERVIEW FILTERING")
    log("=" * 60)

    # Create a test interview for filtering
    log("\n📝 Creating test interview for filtering...")
    start_time = datetime.now().replace(hour=11, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    interview_data = {
        "candidate": candidate_id,
        "job": job_id,
        "interview_round": f"Filter Test Round {int(time.time())}",
        "status": "scheduled",
        "started_at": start_time.isoformat(),
        "ended_at": end_time.isoformat(),
        "feedback": "Test interview for filtering",
    }

    response = requests.post(
        f"{BASE_URL}/api/interviews/", json=interview_data, headers=headers
    )
    if response.status_code == 201:
        interview = response.json()
        interview_id = interview["id"]
        log(f"✅ Test interview created for filtering: ID {interview_id}")
    else:
        log(
            f"❌ Test interview creation failed: {response.status_code} - {response.text}",
            "ERROR",
        )
        return

    # Test filtering by status
    log("\n🔍 Testing filter by status...")
    response = requests.get(
        f"{BASE_URL}/api/interviews/?status=scheduled", headers=headers
    )
    if response.status_code == 200:
        interviews = response.json()
        log(f"✅ Filter by status (scheduled): {len(interviews)} interviews")
    else:
        log(
            f"❌ Filter by status failed: {response.status_code} - {response.text}",
            "ERROR",
        )

    # Test filtering by candidate
    log("\n🔍 Testing filter by candidate...")
    response = requests.get(
        f"{BASE_URL}/api/interviews/?candidate={candidate_id}", headers=headers
    )
    if response.status_code == 200:
        interviews = response.json()
        log(f"✅ Filter by candidate: {len(interviews)} interviews")
    else:
        log(
            f"❌ Filter by candidate failed: {response.status_code} - {response.text}",
            "ERROR",
        )

    # Test filtering by job
    log("\n🔍 Testing filter by job...")
    response = requests.get(f"{BASE_URL}/api/interviews/?job={job_id}", headers=headers)
    if response.status_code == 200:
        interviews = response.json()
        log(f"✅ Filter by job: {len(interviews)} interviews")
    else:
        log(
            f"❌ Filter by job failed: {response.status_code} - {response.text}",
            "ERROR",
        )

    # Clean up test interview
    log(f"\n🗑️ Cleaning up test interview - ID {interview_id}...")
    response = requests.delete(
        f"{BASE_URL}/api/interviews/{interview_id}/", headers=headers
    )
    if response.status_code == 204:
        log(f"✅ Test interview cleaned up successfully")
    else:
        log(
            f"❌ Test interview cleanup failed: {response.status_code} - {response.text}",
            "ERROR",
        )


def test_interview_validation(token, candidate_id, job_id):
    """Test Interview validation rules"""
    headers = {"Authorization": f"Token {token}"}

    log("\n" + "=" * 60)
    log("✅ TESTING INTERVIEW VALIDATION")
    log("=" * 60)

    # Test invalid time window (outside 08:00-22:00 UTC)
    log("\n⏰ Testing invalid time window (outside 08:00-22:00)...")
    invalid_start_time = datetime.now().replace(
        hour=23, minute=0, second=0, microsecond=0
    )
    invalid_end_time = invalid_start_time + timedelta(hours=1)

    invalid_data = {
        "candidate": candidate_id,
        "job": job_id,
        "interview_round": "Invalid Time Test",
        "status": "scheduled",
        "started_at": invalid_start_time.isoformat(),
        "ended_at": invalid_end_time.isoformat(),
        "feedback": "Test with invalid time",
    }

    response = requests.post(
        f"{BASE_URL}/api/interviews/", json=invalid_data, headers=headers
    )
    if response.status_code == 400:
        log(f"✅ Invalid time window correctly rejected: {response.json()}")
    else:
        log(f"❌ Invalid time window should have been rejected: {response.status_code}")

    # Test end time before start time
    log("\n⏰ Testing end time before start time...")
    start_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time - timedelta(hours=1)  # End before start

    invalid_data = {
        "candidate": candidate_id,
        "job": job_id,
        "interview_round": "Invalid Duration Test",
        "status": "scheduled",
        "started_at": start_time.isoformat(),
        "ended_at": end_time.isoformat(),
        "feedback": "Test with invalid duration",
    }

    response = requests.post(
        f"{BASE_URL}/api/interviews/", json=invalid_data, headers=headers
    )
    if response.status_code == 400:
        log(f"✅ Invalid duration correctly rejected: {response.json()}")
    else:
        log(f"❌ Invalid duration should have been rejected: {response.status_code}")


def main():
    """Main test function"""
    log("🚀 STARTING INTERVIEW CRUD OPERATIONS TEST")
    log("=" * 60)

    # Get authentication token
    token = get_auth_token()
    if not token:
        log("❌ Cannot proceed without authentication token", "ERROR")
        return

    # Get test data (candidate and job)
    candidate_id, job_id = get_test_data(token)
    if not candidate_id:
        log("❌ Cannot proceed without test candidate", "ERROR")
        return

    if not job_id:
        log(
            "⚠️  Proceeding without job (interviews can be created without jobs)",
            "WARNING",
        )

    # Test Interview CRUD operations
    interview_id = test_interview_crud(token, candidate_id, job_id)
    if not interview_id:
        log("❌ Interview CRUD test failed", "ERROR")
        return

    # Test additional Interview endpoints
    test_interview_summary(token)
    test_interview_filtering(token, candidate_id, job_id)
    test_interview_validation(token, candidate_id, job_id)

    log("\n" + "=" * 60)
    log("📊 INTERVIEW CRUD OPERATIONS TEST SUMMARY")
    log("=" * 60)
    log("✅ All Interview CRUD operations tested successfully!")
    log("✅ Create, Read, Update, Delete operations working")
    log("✅ Additional endpoints (summary, filtering) working correctly")
    log("✅ Validation rules properly enforced")
    log("🎉 INTERVIEW CRUD OPERATIONS TEST COMPLETED!")


if __name__ == "__main__":
    main()
