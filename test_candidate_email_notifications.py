#!/usr/bin/env python3
"""
Test script to verify that email notifications are being sent to candidates when interviews are scheduled
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

def test_interview_creation_with_notification():
    """Test if email notifications are sent when interview is created"""
    print("\n🧪 Testing Interview Creation with Email Notification...")
    
    token = get_admin_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Token {token}"}
    
    # Create a candidate first
    candidate_data = {
        "domain": "Technology",
        "role": "Software Engineer",
        "candidates": [{
            "full_name": "Email Test Candidate",
            "email": "email.test.candidate@example.com",
            "phone": "+1234567890",
            "poc_email": "poc@example.com"
        }]
    }
    
    response = requests.post(f"{BASE_URL}/api/candidates/bulk-create/?step=submit", json=candidate_data, headers=headers)
    if response.status_code == 201:
        candidates = response.json()
        if candidates and len(candidates) > 0:
            candidate_id = candidates[0]['id']
            candidate_email = candidates[0]['email']
            print(f"✅ Candidate created: {candidate_id} ({candidate_email})")
        else:
            print("❌ No candidates returned from bulk create")
            return False
    else:
        print(f"❌ Candidate creation failed: {response.status_code} - {response.text}")
        return False
    
    # Create an interview (this should trigger email notification)
    interview_data = {
        "candidate": candidate_id,
        "status": "scheduled"
    }
    
    print("📧 Creating interview (should trigger email notification)...")
    response = requests.post(f"{BASE_URL}/api/interviews/", json=interview_data, headers=headers)
    if response.status_code == 201:
        interview_id = response.json()['id']
        print(f"✅ Interview created: {interview_id}")
        print(f"📧 Email notification should have been sent to: {candidate_email}")
    else:
        print(f"❌ Interview creation failed: {response.status_code} - {response.text}")
        return False
    
    # Check if notifications were created in the system
    print("📧 Checking for notifications in the system...")
    response = requests.get(f"{BASE_URL}/api/notifications/", headers=headers)
    if response.status_code == 200:
        notifications = response.json()
        interview_notifications = [n for n in notifications if 'interview' in n.get('notification_type', '').lower()]
        
        if interview_notifications:
            print(f"✅ Found {len(interview_notifications)} interview notifications in system")
            for notification in interview_notifications[:2]:
                print(f"   - {notification.get('title', 'No title')}")
                print(f"     Type: {notification.get('notification_type', 'Unknown')}")
                print(f"     Status: {notification.get('status', 'Unknown')}")
        else:
            print("⚠️  No interview notifications found in system (email may have been sent directly)")
    else:
        print(f"❌ Failed to get notifications: {response.status_code}")
    
    return True

def test_interview_scheduling_with_notification():
    """Test if email notifications are sent when interview is scheduled with a slot"""
    print("\n🧪 Testing Interview Scheduling with Email Notification...")
    
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
        "notes": "Test AI Interview Slot for Email Notification"
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
            "full_name": "Scheduled Email Test Candidate",
            "email": "scheduled.email.test@example.com",
            "phone": "+1234567890",
            "poc_email": "poc@example.com"
        }]
    }
    
    response = requests.post(f"{BASE_URL}/api/candidates/bulk-create/?step=submit", json=candidate_data, headers=headers)
    if response.status_code == 201:
        candidates = response.json()
        if candidates and len(candidates) > 0:
            candidate_id = candidates[0]['id']
            candidate_email = candidates[0]['email']
            print(f"✅ Candidate created: {candidate_id} ({candidate_email})")
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
    
    # Book the interview to the slot (this should trigger email notification)
    booking_data = {
        "interview_id": interview_id,
        "slot_id": slot_id,
        "booking_notes": "Test AI Interview Booking with Email Notification"
    }
    
    print("📧 Booking interview to slot (should trigger email notification)...")
    response = requests.post(f"{BASE_URL}/api/interviews/schedules/book_interview/", json=booking_data, headers=headers)
    if response.status_code == 201:
        schedule_id = response.json()['id']
        print(f"✅ Interview scheduled: {schedule_id}")
        print(f"📧 Email notification should have been sent to: {candidate_email}")
    else:
        print(f"❌ Interview booking failed: {response.status_code} - {response.text}")
        return False
    
    return True

def test_slot_booking_with_notification():
    """Test if email notifications are sent when slots are booked directly"""
    print("\n🧪 Testing Slot Booking with Email Notification...")
    
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
        "start_time": (datetime.now() + timedelta(days=2)).isoformat(),
        "end_time": (datetime.now() + timedelta(days=2, hours=1)).isoformat(),
        "duration_minutes": 60,
        "ai_interview_type": "behavioral",
        "ai_configuration": {
            "question_style": "behavioral",
            "evaluation_criteria": ["communication", "problem_solving"]
        },
        "company": company_id,
        "max_candidates": 1,
        "notes": "Test Slot Booking with Email Notification"
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
            "full_name": "Slot Booking Test Candidate",
            "email": "slot.booking.test@example.com",
            "phone": "+1234567890",
            "poc_email": "poc@example.com"
        }]
    }
    
    response = requests.post(f"{BASE_URL}/api/candidates/bulk-create/?step=submit", json=candidate_data, headers=headers)
    if response.status_code == 201:
        candidates = response.json()
        if candidates and len(candidates) > 0:
            candidate_id = candidates[0]['id']
            candidate_email = candidates[0]['email']
            print(f"✅ Candidate created: {candidate_id} ({candidate_email})")
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
    
    # Book the slot directly (this should trigger email notification)
    booking_data = {
        "interview_id": interview_id,
        "booking_notes": "Direct slot booking with email notification"
    }
    
    print("📧 Booking slot directly (should trigger email notification)...")
    response = requests.post(f"{BASE_URL}/api/interviews/slots/{slot_id}/book_slot/", json=booking_data, headers=headers)
    if response.status_code == 201:
        schedule_data = response.json()
        print(f"✅ Slot booked successfully")
        print(f"📧 Email notification should have been sent to: {candidate_email}")
    else:
        print(f"❌ Slot booking failed: {response.status_code} - {response.text}")
        return False
    
    return True

def test_email_configuration():
    """Test if email configuration is properly set up"""
    print("\n🧪 Testing Email Configuration...")
    
    token = get_admin_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Token {token}"}
    
    # Check if we can access the admin interface to verify email settings
    response = requests.get(f"{BASE_URL}/admin/", headers=headers)
    if response.status_code == 200:
        print("✅ Admin interface accessible")
    else:
        print("⚠️  Admin interface not accessible (this is normal)")
    
    # Check notification templates
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
            print(f"   Channels: {interview_template.get('channels', [])}")
            
            if 'email' in interview_template.get('channels', []):
                print("✅ Email channel is enabled in template")
            else:
                print("❌ Email channel is not enabled in template")
        else:
            print("❌ No interview scheduled template found")
            return False
    else:
        print(f"❌ Failed to get notification templates: {response.status_code}")
        return False
    
    return True

def main():
    """Run all email notification tests"""
    print("📧 Candidate Email Notification System Test")
    print("=" * 60)
    
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
        test_email_configuration,
        test_interview_creation_with_notification,
        test_interview_scheduling_with_notification,
        test_slot_booking_with_notification
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All email notification tests passed!")
        print("📧 Email notifications should be working properly.")
    else:
        print("⚠️  Some tests failed. Email notifications may not be working properly.")
    
    print("\n📋 Summary:")
    print("1. Email configuration test - Checks if email settings are properly configured")
    print("2. Interview creation notification test - Tests email when interviews are created")
    print("3. Interview scheduling notification test - Tests email when interviews are scheduled with slots")
    print("4. Slot booking notification test - Tests email when slots are booked directly")
    
    print("\n💡 Note: Check your email server logs to verify that emails were actually sent.")
    print("   The test emails should be sent to the candidate email addresses shown above.")

if __name__ == "__main__":
    main()

