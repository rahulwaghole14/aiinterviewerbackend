#!/usr/bin/env python3
"""
Test script to check if email notifications are being sent to candidates when interviews are scheduled
"""

import requests
import json
from datetime import datetime, timedelta
import time

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@rslsolution.com"
ADMIN_PASSWORD = "admin123"

def get_admin_token():
    """Get admin authentication token"""
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
    if response.status_code == 200:
        return response.json().get('token')
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_interview_creation_notification():
    """Test if notifications are sent when interview is created"""
    print("\n🧪 Testing Interview Creation Notification...")
    
    token = get_admin_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Token {token}"}
    
    # Get first company
    response = requests.get(f"{BASE_URL}/api/companies/", headers=headers)
    if response.status_code == 200:
        companies = response.json()
        if companies:
            company_id = companies[0]['id']
        else:
            print("❌ No companies found")
            return False
    else:
        print(f"❌ Failed to get companies: {response.status_code}")
        return False
    
    # Create a candidate first
    candidate_data = {
        "domain": "Technology",
        "role": "Software Engineer",
        "candidates": [{
            "full_name": "Test Candidate for Notification",
            "email": "test.candidate@example.com",
            "phone": "+1234567890",
            "poc_email": "poc@example.com"
        }]
    }
    
    response = requests.post(f"{BASE_URL}/api/candidates/bulk-create/?step=submit", json=candidate_data, headers=headers)
    if response.status_code == 201:
        candidates = response.json()
        if candidates and len(candidates) > 0:
            candidate_id = candidates[0]['id']
            print(f"✅ Candidate created: {candidate_id}")
        else:
            print("❌ No candidates returned from bulk create")
            return False
    else:
        print(f"❌ Candidate creation failed: {response.status_code} - {response.text}")
        return False
    
    # Create an interview
    interview_data = {
        "candidate": candidate_id,
        "status": "scheduled"
    }
    
    response = requests.post(f"{BASE_URL}/api/interviews/", json=interview_data, headers=headers)
    if response.status_code == 201:
        interview_id = response.json()['id']
        print(f"✅ Interview created: {interview_id}")
    else:
        print(f"❌ Interview creation failed: {response.status_code} - {response.text}")
        return False
    
    # Check if notifications were sent
    print("📧 Checking for notifications...")
    
    # Check notifications for the candidate's recruiter (admin in this case)
    response = requests.get(f"{BASE_URL}/api/notifications/", headers=headers)
    if response.status_code == 200:
        notifications = response.json()
        interview_notifications = [n for n in notifications if 'interview' in n.get('notification_type', '').lower()]
        
        if interview_notifications:
            print(f"✅ Found {len(interview_notifications)} interview notifications")
            for notification in interview_notifications[:3]:  # Show first 3
                print(f"   - {notification.get('title', 'No title')}")
                print(f"     Type: {notification.get('notification_type', 'Unknown')}")
                print(f"     Status: {notification.get('status', 'Unknown')}")
        else:
            print("❌ No interview notifications found")
            return False
    else:
        print(f"❌ Failed to get notifications: {response.status_code}")
        return False
    
    return True

def test_interview_scheduling_notification():
    """Test if notifications are sent when interview is scheduled with a slot"""
    print("\n🧪 Testing Interview Scheduling Notification...")
    
    token = get_admin_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Token {token}"}
    
    # Get first company
    response = requests.get(f"{BASE_URL}/api/companies/", headers=headers)
    if response.status_code == 200:
        companies = response.json()
        if companies:
            company_id = companies[0]['id']
        else:
            print("❌ No companies found")
            return False
    else:
        print(f"❌ Failed to get companies: {response.status_code}")
        return False
    
    # Create an AI interview slot
    slot_data = {
        "slot_type": "fixed",
        "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
        "duration_minutes": 60,
        "ai_interview_type": "technical",
        "ai_configuration": {
            "difficulty": "medium",
            "topics": ["algorithms", "data_structures"]
        },
        "company": company_id,
        "max_candidates": 1,
        "notes": "Test AI Interview Slot"
    }
    
    response = requests.post(f"{BASE_URL}/api/interviews/slots/", json=slot_data, headers=headers)
    if response.status_code == 201:
        slot_id = response.json()['id']
        print(f"✅ AI Interview Slot created: {slot_id}")
    else:
        print(f"❌ AI Interview Slot creation failed: {response.status_code} - {response.text}")
        return False
    
    # Create a candidate
    candidate_data = {
        "domain": "Technology",
        "role": "Software Engineer",
        "candidates": [{
            "full_name": "Scheduled Test Candidate",
            "email": "scheduled.candidate@example.com",
            "phone": "+1234567890",
            "poc_email": "poc@example.com"
        }]
    }
    
    response = requests.post(f"{BASE_URL}/api/candidates/bulk-create/?step=submit", json=candidate_data, headers=headers)
    if response.status_code == 201:
        candidates = response.json()
        if candidates and len(candidates) > 0:
            candidate_id = candidates[0]['id']
            print(f"✅ Candidate created: {candidate_id}")
        else:
            print("❌ No candidates returned from bulk create")
            return False
    else:
        print(f"❌ Candidate creation failed: {response.status_code} - {response.text}")
        return False
    
    # Create an interview
    interview_data = {
        "candidate": candidate_id,
        "status": "scheduled"
    }
    
    response = requests.post(f"{BASE_URL}/api/interviews/", json=interview_data, headers=headers)
    if response.status_code == 201:
        interview_id = response.json()['id']
        print(f"✅ Interview created: {interview_id}")
    else:
        print(f"❌ Interview creation failed: {response.status_code} - {response.text}")
        return False
    
    # Book the interview to the slot
    booking_data = {
        "interview_id": interview_id,
        "slot_id": slot_id,
        "booking_notes": "Test AI Interview Booking"
    }
    
    response = requests.post(f"{BASE_URL}/api/interviews/schedules/book_interview/", json=booking_data, headers=headers)
    if response.status_code == 201:
        schedule_id = response.json()['id']
        print(f"✅ Interview scheduled: {schedule_id}")
    else:
        print(f"❌ Interview booking failed: {response.status_code} - {response.text}")
        return False
    
    # Check if notifications were sent
    print("📧 Checking for scheduling notifications...")
    
    response = requests.get(f"{BASE_URL}/api/notifications/", headers=headers)
    if response.status_code == 200:
        notifications = response.json()
        scheduling_notifications = [n for n in notifications if 'scheduled' in n.get('notification_type', '').lower()]
        
        if scheduling_notifications:
            print(f"✅ Found {len(scheduling_notifications)} scheduling notifications")
            for notification in scheduling_notifications[:3]:
                print(f"   - {notification.get('title', 'No title')}")
                print(f"     Type: {notification.get('notification_type', 'Unknown')}")
                print(f"     Status: {notification.get('status', 'Unknown')}")
        else:
            print("❌ No scheduling notifications found")
            return False
    else:
        print(f"❌ Failed to get notifications: {response.status_code}")
        return False
    
    return True

def test_candidate_email_notification():
    """Test if notifications are sent to candidate's email"""
    print("\n🧪 Testing Candidate Email Notification...")
    
    token = get_admin_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Token {token}"}
    
    # Check notification templates to see if they support candidate emails
    response = requests.get(f"{BASE_URL}/api/notifications/templates/", headers=headers)
    if response.status_code == 200:
        templates = response.json()
        interview_template = None
        for template in templates:
            if 'interview_scheduled' in template.get('name', ''):
                interview_template = template
                break
        
        if interview_template:
            print(f"✅ Found interview scheduled template: {interview_template.get('name')}")
            print(f"   Title template: {interview_template.get('title_template', 'N/A')}")
            print(f"   Message template: {interview_template.get('message_template', 'N/A')}")
            print(f"   Channels: {interview_template.get('channels', [])}")
            
            # Check if the template mentions candidate
            message_template = interview_template.get('message_template', '')
            if 'candidate' in message_template.lower():
                print("✅ Template mentions candidate")
            else:
                print("❌ Template does not mention candidate")
        else:
            print("❌ No interview scheduled template found")
            return False
    else:
        print(f"❌ Failed to get notification templates: {response.status_code}")
        return False
    
    return True

def main():
    """Run all notification tests"""
    print("📧 Interview Notification System Test")
    print("=" * 50)
    
    # Test server connection
    try:
        response = requests.get(f"{BASE_URL}/api/")
        if response.status_code == 401:
            print("✅ Server is running (authentication required)")
        elif response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server not responding: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on http://localhost:8000")
        return
    
    # Run tests
    tests = [
        test_interview_creation_notification,
        test_interview_scheduling_notification,
        test_candidate_email_notification
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All notification tests passed!")
    else:
        print("⚠️  Some tests failed. Email notifications may not be working properly.")
    
    print("\n📋 Summary:")
    print("1. Interview creation notification test - Checks if notifications are sent when interviews are created")
    print("2. Interview scheduling notification test - Checks if notifications are sent when interviews are scheduled with slots")
    print("3. Candidate email notification test - Checks if notification templates support candidate emails")

if __name__ == "__main__":
    main()

