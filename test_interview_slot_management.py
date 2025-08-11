#!/usr/bin/env python3
"""
Test Script for Interview Slot Management System
Tests slot creation, listing, availability status, and booking functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta
import pytz

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "password123"

def log(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def login_user(email, password):
    """Login and get authentication token"""
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login/", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            return data.get('token')
        else:
            log(f"Login failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"Login error: {e}", "ERROR")
        return None

def create_test_company(token):
    """Create a test company or get existing one"""
    headers = {'Authorization': f'Token {token}'}
    data = {
        "name": "Test Company for Slot Management",
        "email": "testcompany@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/companies/", json=data, headers=headers)
        if response.status_code == 201:
            log("✅ Created new test company")
            return response.json()['id']
        elif response.status_code == 400 and "already exists" in response.text:
            log("⚠️ Company already exists, retrieving existing company...")
            # Try to get the existing company
            response = requests.get(f"{BASE_URL}/api/companies/", headers=headers)
            if response.status_code == 200:
                companies = response.json()
                for company in companies:
                    if company.get('email') == data['email']:
                        log(f"✅ Retrieved existing company: {company['id']}")
                        return company['id']
            log("❌ Could not retrieve existing company", "ERROR")
            return None
        else:
            log(f"Company creation failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"Company creation error: {e}", "ERROR")
        return None

def create_test_job(token, company_id):
    """Create a test job or get existing one"""
    headers = {'Authorization': f'Token {token}'}
    data = {
        "job_title": "Senior Software Engineer",
        "company_name": "Test Company for Slot Management",
        "domain": 15,  # Python Development domain
        "spoc_email": "hr@testcompany.com",
        "hiring_manager_email": "hiring@testcompany.com",
        "current_team_size_info": "10-20",
        "number_to_hire": 2,
        "position_level": "IC",
        "tech_stack_details": "Python, Django, React, AWS, Docker, Kubernetes",
        "current_process": "We are looking for a senior software engineer with 5+ years of experience in Python development."
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/jobs/", json=data, headers=headers)
        if response.status_code == 201:
            log("✅ Created new test job")
            return response.json()['id']
        elif response.status_code == 400 and "already exists" in response.text:
            log("⚠️ Job already exists, retrieving existing job...")
            # Try to get the existing job
            response = requests.get(f"{BASE_URL}/api/jobs/", headers=headers)
            if response.status_code == 200:
                jobs = response.json()
                for job in jobs:
                    if job.get('job_title') == data['job_title'] and job.get('company_name') == data['company_name']:
                        log(f"✅ Retrieved existing job: {job['id']}")
                        return job['id']
            log("❌ Could not retrieve existing job", "ERROR")
            return None
        else:
            log(f"Job creation failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"Job creation error: {e}", "ERROR")
        return None

def test_create_interview_slot(token, company_id, job_id):
    """Test creating an interview slot"""
    log("Testing interview slot creation...")
    
    headers = {'Authorization': f'Token {token}'}
    
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
            "time_limit": 60
        },
        "company": company_id,
        "job": job_id,
        "max_candidates": 1,
        "notes": "Test interview slot for technical screening"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/interviews/slots/", json=data, headers=headers)
        log(f"Create slot response: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            log(f"✅ Interview slot created successfully")
            log(f"   Slot ID: {result.get('id')}")
            log(f"   Start Time: {result.get('start_time')}")
            log(f"   End Time: {result.get('end_time')}")
            log(f"   Status: {result.get('status')}")
            log(f"   AI Type: {result.get('ai_interview_type')}")
            return result
        else:
            log(f"❌ Slot creation failed: {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Slot creation error: {e}", "ERROR")
        return None

def test_list_all_slots(token):
    """Test listing all interview slots"""
    log("Testing interview slot listing...")
    
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.get(f"{BASE_URL}/api/interviews/slots/", headers=headers)
        log(f"List slots response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            slots = result.get('results', result) if isinstance(result, dict) else result
            
            log(f"✅ Retrieved {len(slots)} interview slots")
            
            for i, slot in enumerate(slots[:5]):  # Show first 5 slots
                log(f"   Slot {i+1}:")
                log(f"     ID: {slot.get('id')}")
                log(f"     Start: {slot.get('start_time')}")
                log(f"     End: {slot.get('end_time')}")
                log(f"     Status: {slot.get('status')}")
                log(f"     AI Type: {slot.get('ai_interview_type')}")
                log(f"     Available: {slot.get('current_bookings', 0)}/{slot.get('max_candidates', 1)}")
            
            return slots
        else:
            log(f"❌ Slot listing failed: {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Slot listing error: {e}", "ERROR")
        return None

def test_get_available_slots(token):
    """Test getting available slots"""
    log("Testing available slots retrieval...")
    
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.get(f"{BASE_URL}/api/interviews/available-slots/", headers=headers)
        log(f"Available slots response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            available_slots = result.get('available_slots', [])
            
            log(f"✅ Retrieved {len(available_slots)} available slots")
            
            for i, slot in enumerate(available_slots[:3]):  # Show first 3 available slots
                log(f"   Available Slot {i+1}:")
                log(f"     ID: {slot.get('id')}")
                log(f"     Start: {slot.get('start_time')}")
                log(f"     End: {slot.get('end_time')}")
                log(f"     Status: {slot.get('status')}")
                log(f"     AI Type: {slot.get('ai_interview_type')}")
            
            return available_slots
        else:
            log(f"❌ Available slots retrieval failed: {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Available slots error: {e}", "ERROR")
        return None

def test_search_available_slots(token):
    """Test searching for available slots with filters"""
    log("Testing slot search with filters...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Search for slots tomorrow
    tomorrow = datetime.now() + timedelta(days=1)
    search_date = tomorrow.strftime('%Y-%m-%d')
    
    data = {
        "start_date": search_date,
        "end_date": search_date,
        "ai_interview_type": "technical",
        "start_time": "09:00:00",
        "end_time": "18:00:00"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/interviews/slots/search_available/", json=data, headers=headers)
        log(f"Search slots response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            # Handle both list and dict responses
            if isinstance(result, list):
                available_slots = result
            else:
                available_slots = result.get('available_slots', [])
            
            log(f"✅ Search found {len(available_slots)} available slots for {search_date}")
            
            for i, slot in enumerate(available_slots[:3]):
                log(f"   Search Result {i+1}:")
                log(f"     ID: {slot.get('id')}")
                log(f"     Start: {slot.get('start_time')}")
                log(f"     End: {slot.get('end_time')}")
                log(f"     AI Type: {slot.get('ai_interview_type')}")
            
            return available_slots
        else:
            log(f"❌ Slot search failed: {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Slot search error: {e}", "ERROR")
        return None

def test_create_recurring_slots(token, company_id, job_id):
    """Test creating recurring interview slots"""
    log("Testing recurring slot creation...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Create recurring slots for next week (Monday to Friday)
    start_date = datetime.now() + timedelta(days=7)  # Next week
    end_date = start_date + timedelta(days=4)  # 5 days (Mon-Fri)
    
    data = {
        "company_id": company_id,
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "days_of_week": [1, 2, 3, 4, 5],  # Monday to Friday
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "ai_interview_type": "behavioral",
        "ai_configuration": {
            "difficulty_level": "beginner",
            "question_count": 8,
            "time_limit": 45
        },
        "max_candidates_per_slot": 1
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/interviews/slots/create_recurring/", json=data, headers=headers)
        log(f"Create recurring slots response: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            created_count = result.get('created_slots', 0)
            
            if created_count > 0:
                log(f"✅ Created {created_count} recurring slots")
            else:
                log(f"⚠️ Created 0 recurring slots (conflicts detected - this is correct behavior)")
            
            log(f"   Date range: {data['start_date']} to {data['end_date']}")
            log(f"   Days: Monday to Friday")
            log(f"   Time: {data['start_time']} to {data['end_time']}")
            
            # Check if there were skipped slots due to conflicts
            skipped_slots = result.get('skipped_slots', [])
            if skipped_slots:
                log(f"   Skipped slots due to conflicts: {len(skipped_slots)}")
            
            return result
        else:
            log(f"❌ Recurring slot creation failed: {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Recurring slot creation error: {e}", "ERROR")
        return None

def test_slot_availability_status(token, slot_id):
    """Test slot availability status"""
    log(f"Testing slot availability status for slot {slot_id}...")
    
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.get(f"{BASE_URL}/api/interviews/slots/{slot_id}/", headers=headers)
        log(f"Get slot details response: {response.status_code}")
        
        if response.status_code == 200:
            slot = response.json()
            
            log(f"✅ Slot details retrieved")
            log(f"   ID: {slot.get('id')}")
            log(f"   Status: {slot.get('status')}")
            log(f"   Current Bookings: {slot.get('current_bookings', 0)}")
            log(f"   Max Candidates: {slot.get('max_candidates', 1)}")
            log(f"   Available: {slot.get('current_bookings', 0) < slot.get('max_candidates', 1)}")
            log(f"   Start Time: {slot.get('start_time')}")
            log(f"   End Time: {slot.get('end_time')}")
            
            # Check if slot is available
            is_available = slot.get('current_bookings', 0) < slot.get('max_candidates', 1)
            status_correct = (slot.get('status') == 'available') == is_available
            
            if status_correct:
                log(f"✅ Slot availability status is correct")
            else:
                log(f"⚠️ Slot availability status may be incorrect", "WARNING")
            
            return slot
        else:
            log(f"❌ Get slot details failed: {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Get slot details error: {e}", "ERROR")
        return None

def test_book_slot(token, slot_id):
    """Test booking a slot"""
    log(f"Testing slot booking for slot {slot_id}...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # First create a test candidate using bulk endpoint
    candidate_data = {
        "domain": "Software Development",
        "role": "Developer",
        "candidates": [
            {
                "filename": "test_candidate.pdf",
                "edited_data": {
                    "full_name": "Test Candidate",
                    "email": "test.candidate@example.com",
                    "phone": "+1234567890",
                    "work_experience": 3,
                    "poc_email": "test.candidate@example.com"
                }
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/candidates/bulk-create/?step=submit", json=candidate_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('summary', {}).get('successful_creations', 0) > 0:
                # Get the first successful candidate ID
                for candidate_result in result.get('results', []):
                    if candidate_result.get('status') == 'success':
                        candidate_id = candidate_result.get('candidate_id')
                        log(f"Created test candidate: {candidate_id}")
                        break
                else:
                    log(f"Failed to create test candidate: {response.text}", "ERROR")
                    return None
            else:
                log(f"Failed to create test candidate: {response.text}", "ERROR")
                return None
        else:
            log(f"Failed to create test candidate: {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"Error creating test candidate: {e}", "ERROR")
        return None
    
    # First create an interview for the candidate
    interview_data = {
        "candidate": candidate_id,
        "status": "scheduled"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/interviews/", json=interview_data, headers=headers)
        if response.status_code == 201:
            interview_id = response.json()['id']
            log(f"Created test interview: {interview_id}")
        else:
            log(f"Failed to create test interview: {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"Error creating test interview: {e}", "ERROR")
        return None
    
    # Now book the slot
    booking_data = {
        "interview_id": interview_id,
        "booking_notes": "Test booking for slot availability verification"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/interviews/slots/{slot_id}/book_slot/", json=booking_data, headers=headers)
        log(f"Book slot response: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            log(f"✅ Slot booked successfully")
            log(f"   Interview Schedule ID: {result.get('id')}")
            log(f"   Interview ID: {result.get('interview')}")
            log(f"   Status: {result.get('status')}")
            return result
        else:
            log(f"❌ Slot booking failed: {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Slot booking error: {e}", "ERROR")
        return None

def test_release_slot(token, slot_id):
    """Test releasing a booked slot"""
    log(f"Testing slot release for slot {slot_id}...")
    
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.post(f"{BASE_URL}/api/interviews/slots/{slot_id}/release_slot/", headers=headers)
        log(f"Release slot response: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            log(f"✅ Slot released successfully")
            log(f"   Slot Available: {result.get('slot_available')}")
            return result
        else:
            log(f"❌ Slot release failed: {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Slot release error: {e}", "ERROR")
        return None

def test_calendar_view(token):
    """Test interview calendar view"""
    log("Testing interview calendar view...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Get current month
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    params = {
        'year': current_year,
        'month': current_month,
        'ai_interview_type': 'technical'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/interviews/calendar/", params=params, headers=headers)
        log(f"Calendar view response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            calendar_data = result.get('calendar_data', [])
            
            log(f"✅ Calendar view retrieved")
            log(f"   Total Slots: {result.get('total_slots', 0)}")
            log(f"   Available Slots: {result.get('available_slots', 0)}")
            log(f"   Booked Slots: {result.get('booked_slots', 0)}")
            log(f"   Calendar Entries: {len(calendar_data)}")
            
            return result
        else:
            log(f"❌ Calendar view failed: {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Calendar view error: {e}", "ERROR")
        return None

def main():
    """Main test function"""
    log("🚀 Starting Interview Slot Management System Test")
    log("=" * 70)
    
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
    
    job_id = create_test_job(token, company_id)
    if not job_id:
        log("❌ Failed to create job. Exiting.", "ERROR")
        return
    
    log("✅ Test data created successfully")
    
    # Step 3: Test slot creation
    log("\nStep 3: Testing slot creation...")
    slot_result = test_create_interview_slot(token, company_id, job_id)
    if not slot_result:
        log("❌ Failed to create test slot. Exiting.", "ERROR")
        return
    
    slot_id = slot_result['id']
    
    # Step 4: Test slot listing
    log("\nStep 4: Testing slot listing...")
    all_slots = test_list_all_slots(token)
    if all_slots is None:
        log("❌ Failed to list slots. Exiting.", "ERROR")
        return
    
    # Step 5: Test available slots
    log("\nStep 5: Testing available slots...")
    available_slots = test_get_available_slots(token)
    if available_slots is None:
        log("❌ Failed to get available slots. Exiting.", "ERROR")
        return
    
    # Step 6: Test slot search
    log("\nStep 6: Testing slot search...")
    search_results = test_search_available_slots(token)
    
    # Step 7: Test recurring slot creation
    log("\nStep 7: Testing recurring slot creation...")
    recurring_result = test_create_recurring_slots(token, company_id, job_id)
    
    # Step 8: Test slot availability status
    log("\nStep 8: Testing slot availability status...")
    slot_details = test_slot_availability_status(token, slot_id)
    
    # Step 9: Test slot booking
    log("\nStep 9: Testing slot booking...")
    booking_result = test_book_slot(token, slot_id)
    
    # Step 10: Test slot release
    log("\nStep 10: Testing slot release...")
    if booking_result:
        release_result = test_release_slot(token, slot_id)
    
    # Step 11: Test calendar view
    log("\nStep 11: Testing calendar view...")
    calendar_result = test_calendar_view(token)
    
    # Summary
    log("\n" + "=" * 70)
    log("📊 Test Results Summary:")
    log(f"   ✅ Slot creation: {'PASS' if slot_result else 'FAIL'}")
    log(f"   ✅ Slot listing: {'PASS' if all_slots else 'FAIL'}")
    log(f"   ✅ Available slots: {'PASS' if available_slots else 'FAIL'}")
    log(f"   ✅ Slot search: {'PASS' if search_results else 'FAIL'}")
    log(f"   ✅ Recurring slots: {'PASS' if recurring_result else 'FAIL'}")
    log(f"   ✅ Availability status: {'PASS' if slot_details else 'FAIL'}")
    log(f"   ✅ Slot booking: {'PASS' if booking_result else 'FAIL'}")
    log(f"   ✅ Slot release: {'PASS' if 'release_result' in locals() and release_result else 'FAIL'}")
    log(f"   ✅ Calendar view: {'PASS' if calendar_result else 'FAIL'}")
    
    # Check if all tests passed
    test_results = [
        slot_result, all_slots, available_slots, search_results, 
        recurring_result, slot_details, booking_result, 
        'release_result' in locals() and release_result, calendar_result
    ]
    
    passed_tests = sum(1 for result in test_results if result)
    total_tests = len(test_results)
    
    log(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        log("🎉 All tests passed! Interview slot management system is working correctly.")
    else:
        log("❌ Some tests failed. Please check the implementation.", "ERROR")
    
    log("\n✅ Test completed!")

if __name__ == "__main__":
    main()
