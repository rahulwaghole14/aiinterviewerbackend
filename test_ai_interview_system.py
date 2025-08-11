#!/usr/bin/env python3
"""
Test script for AI Interview Slot Management System
Tests the new AI interview functionality without human interviewers
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

def test_ai_interview_slot_creation():
    """Test creating AI interview slots"""
    print("\n🧪 Testing AI Interview Slot Creation...")
    
    token = get_admin_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Token {token}"}
    
    # Get or create a company
    company_data = {
        "name": "AI Tech Corp",
        "email": "ai@techcorp.com",
        "password": "company123"
    }
    
    response = requests.post(f"{BASE_URL}/api/companies/", json=company_data, headers=headers)
    if response.status_code == 201:
        company_id = response.json()['id']
        print(f"✅ Company created: {company_id}")
    elif response.status_code == 400 and "email already exists" in response.text:
        # Company already exists, get it
        response = requests.get(f"{BASE_URL}/api/companies/", headers=headers)
        if response.status_code == 200:
            companies = response.json()
            for company in companies:
                if company['email'] == "ai@techcorp.com":
                    company_id = company['id']
                    print(f"✅ Company found: {company_id}")
                    break
            else:
                print("❌ Company not found in list")
                return False
        else:
            print(f"❌ Failed to get companies: {response.status_code}")
            return False
    else:
        print(f"❌ Company creation failed: {response.status_code} - {response.text}")
        return False
    
    # Create AI interview slot
    slot_data = {
        "slot_type": "fixed",
        "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
        "duration_minutes": 60,
        "ai_interview_type": "technical",
        "ai_configuration": {
            "difficulty": "medium",
            "topics": ["algorithms", "data_structures"],
            "duration": 45
        },
        "company": company_id,
        "max_candidates": 1,
        "notes": "AI Technical Interview Slot"
    }
    
    response = requests.post(f"{BASE_URL}/api/interviews/slots/", json=slot_data, headers=headers)
    if response.status_code == 201:
        slot_id = response.json()['id']
        print(f"✅ AI Interview Slot created: {slot_id}")
        print(f"   AI Type: {response.json()['ai_interview_type']}")
        print(f"   Configuration: {response.json()['ai_configuration']}")
        return True
    else:
        print(f"❌ AI Interview Slot creation failed: {response.status_code} - {response.text}")
        return False

def test_ai_interview_configuration():
    """Test AI interview configuration creation"""
    print("\n🧪 Testing AI Interview Configuration...")
    
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
    
    # Create AI interview configuration
    config_data = {
        "company": company_id,
        "interview_type": "technical",
        "day_of_week": 1,  # Monday
        "start_time": "09:00:00",
        "end_time": "17:00:00",
        "slot_duration": 60,
        "break_duration": 15,
        "ai_settings": {
            "difficulty_levels": ["easy", "medium", "hard"],
            "question_types": ["coding", "system_design", "algorithms"],
            "auto_grading": True
        },
        "valid_from": datetime.now().date().isoformat()
    }
    
    response = requests.post(f"{BASE_URL}/api/interviews/configurations/", json=config_data, headers=headers)
    if response.status_code == 201:
        config_response = response.json()
        config_id = config_response['id']
        print(f"✅ AI Interview Configuration created: {config_id}")
        print(f"   Interview Type: {config_response['interview_type']}")
        print(f"   AI Settings: {config_response['ai_settings']}")
        return True
    else:
        print(f"❌ AI Interview Configuration creation failed: {response.status_code} - {response.text}")
        return False

def test_recurring_ai_slots():
    """Test creating recurring AI interview slots"""
    print("\n🧪 Testing Recurring AI Interview Slots...")
    
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
    
    # Create recurring AI slots
    recurring_data = {
        "company_id": company_id,
        "ai_interview_type": "behavioral",
        "start_date": datetime.now().date().isoformat(),
        "end_date": (datetime.now() + timedelta(days=7)).date().isoformat(),
        "start_time": "10:00:00",
        "end_time": "16:00:00",
        "days_of_week": [1, 2, 3, 4, 5],  # Monday to Friday
        "slot_duration": 45,
        "break_duration": 15,
        "max_candidates_per_slot": 1,
        "ai_configuration": {
            "question_style": "behavioral",
            "evaluation_criteria": ["communication", "problem_solving", "teamwork"]
        },
        "notes": "Recurring Behavioral AI Interviews"
    }
    
    response = requests.post(f"{BASE_URL}/api/interviews/slots/create_recurring/", json=recurring_data, headers=headers)
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Recurring AI Slots created: {result['message']}")
        print(f"   Slots created: {len(result['slots'])}")
        return True
    else:
        print(f"❌ Recurring AI Slots creation failed: {response.status_code} - {response.text}")
        return False

def test_ai_slot_search():
    """Test searching for AI interview slots"""
    print("\n🧪 Testing AI Interview Slot Search...")
    
    token = get_admin_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Token {token}"}
    
    # Search for available AI slots
    search_data = {
        "start_date": datetime.now().date().isoformat(),
        "end_date": (datetime.now() + timedelta(days=7)).date().isoformat(),
        "ai_interview_type": "technical",
        "duration_minutes": 60
    }
    
    response = requests.post(f"{BASE_URL}/api/interviews/slots/search_available/", json=search_data, headers=headers)
    if response.status_code == 200:
        slots = response.json()
        print(f"✅ AI Slot Search successful: Found {len(slots)} slots")
        for slot in slots[:3]:  # Show first 3 slots
            print(f"   - {slot['ai_interview_type']} slot at {slot['start_time']}")
        return True
    else:
        print(f"❌ AI Slot Search failed: {response.status_code} - {response.text}")
        return False

def test_ai_interview_scheduling():
    """Test scheduling an AI interview"""
    print("\n🧪 Testing AI Interview Scheduling...")
    
    token = get_admin_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Token {token}"}
    
    # Create a candidate first (using bulk create endpoint to avoid file upload)
    candidate_data = {
        "domain": "Technology",
        "role": "Software Engineer",
        "candidates": [{
            "full_name": "AI Test Candidate",
            "email": "ai.candidate@test.com",
            "phone": "+1234567890",
            "poc_email": "poc@test.com"
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
    
    # Get available slots
    response = requests.get(f"{BASE_URL}/api/interviews/available-slots/?start_date={datetime.now().date().isoformat()}", headers=headers)
    if response.status_code == 200:
        slots = response.json()
        if slots:
            slot_id = slots[0]['id']
            
            # Book the interview
            booking_data = {
                "interview_id": interview_id,
                "slot_id": slot_id,
                "booking_notes": "AI Interview Booking"
            }
            
            response = requests.post(f"{BASE_URL}/api/interviews/schedules/book_interview/", json=booking_data, headers=headers)
            if response.status_code == 201:
                schedule_id = response.json()['id']
                print(f"✅ AI Interview scheduled: {schedule_id}")
                print(f"   AI Type: {response.json()['ai_interview_type']}")
                return True
            else:
                print(f"❌ Interview booking failed: {response.status_code} - {response.text}")
                return False
        else:
            print("❌ No available slots found")
            return False
    else:
        print(f"❌ Failed to get available slots: {response.status_code}")
        return False

def main():
    """Run all AI interview system tests"""
    print("🤖 AI Interview Slot Management System Test")
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
        test_ai_interview_slot_creation,
        test_ai_interview_configuration,
        test_recurring_ai_slots,
        test_ai_slot_search,
        test_ai_interview_scheduling
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
        print("🎉 All AI Interview System tests passed!")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
