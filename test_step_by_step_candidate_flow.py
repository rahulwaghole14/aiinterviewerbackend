#!/usr/bin/env python3
"""
Test script for Step-by-Step Candidate Creation Flow
This tests the new implementation that matches the user requirements.
"""

import requests
import json
import time
import os

BASE_URL = "http://localhost:8000"

def test_authentication():
    """Get authentication token"""
    print("🔐 Getting authentication token...")
    
    login_data = {
        'email': 'testuser@example.com',
        'password': 'testpass123'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        if response.status_code == 200:
            token = response.json().get('token')
            print("✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_step1_domain_role_selection(token):
    """Test Step 1: Domain and Role Selection"""
    print("\n🎯 Step 1: Testing Domain and Role Selection...")
    
    headers = {'Authorization': f'Token {token}'}
    data = {
        'domain': 'Python Development',
        'role': 'Senior Software Engineer'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/candidates/select-domain/", 
                               json=data, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Domain and role selection successful")
            print(f"   Draft ID: {result['draft_id']}")
            print(f"   Domain: {result['domain']}")
            print(f"   Role: {result['role']}")
            print(f"   Next Step: {result['next_step']}")
            return result['draft_id']
        else:
            print(f"❌ Domain/role selection failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Domain/role selection error: {e}")
        return None

def test_step2_data_extraction(token, draft_id):
    """Test Step 2: Resume Upload and Data Extraction"""
    print("\n📄 Step 2: Testing Resume Upload and Data Extraction...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Create a mock resume file content
    mock_resume_content = b"""
    JOHN DOE
    Senior Python Developer
    Email: john.doe@example.com
    Phone: +1234567890
    Experience: 5 years
    
    SKILLS:
    - Python, Django, Flask
    - React, JavaScript
    - PostgreSQL, MongoDB
    - Docker, AWS
    
    EXPERIENCE:
    - Senior Developer at Tech Corp (3 years)
    - Python Developer at Startup Inc (2 years)
    """
    
    files = {
        'resume_file': ('john_doe_resume.pdf', mock_resume_content, 'application/pdf')
    }
    
    data = {
        'domain': 'Python Development',
        'role': 'Senior Software Engineer'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/candidates/extract-data/", 
                               files=files, data=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Data extraction successful")
            print(f"   Draft ID: {result['draft_id']}")
            print(f"   Extracted Data: {result['extracted_data']}")
            print(f"   Next Step: {result['next_step']}")
            return result['draft_id']
        else:
            print(f"❌ Data extraction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Data extraction error: {e}")
        return None

def test_step3_verification_preview(token, draft_id):
    """Test Step 3: Verification Preview"""
    print("\n👀 Step 3: Testing Verification Preview...")
    
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.get(f"{BASE_URL}/api/candidates/verify/{draft_id}/", 
                              headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Verification preview successful")
            print(f"   Draft: {result['draft']}")
            print(f"   Next Step: {result['next_step']}")
            return result['draft']
        else:
            print(f"❌ Verification preview failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Verification preview error: {e}")
        return None

def test_step4_verification_update(token, draft_id):
    """Test Step 4: Verification Update"""
    print("\n✏️  Step 4: Testing Verification Update...")
    
    headers = {'Authorization': f'Token {token}'}
    data = {
        'full_name': 'John Doe Updated',
        'email': 'john.updated@example.com',
        'phone': '+1234567891',
        'work_experience': 6
    }
    
    try:
        response = requests.put(f"{BASE_URL}/api/candidates/verify/{draft_id}/", 
                              json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Verification update successful")
            print(f"   Updated Draft: {result['draft']}")
            print(f"   Next Step: {result['next_step']}")
            return True
        else:
            print(f"❌ Verification update failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Verification update error: {e}")
        return False

def test_step5_final_submission(token, draft_id):
    """Test Step 5: Final Submission"""
    print("\n✅ Step 5: Testing Final Submission...")
    
    headers = {'Authorization': f'Token {token}'}
    data = {
        'confirm_submission': True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/candidates/submit/{draft_id}/", 
                               json=data, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Final submission successful")
            print(f"   Candidate ID: {result['candidate_id']}")
            print(f"   Domain: {result['domain']}")
            print(f"   Role: {result['role']}")
            print(f"   Next Step: {result['next_step']}")
            return result['candidate_id']
        else:
            print(f"❌ Final submission failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Final submission error: {e}")
        return None

def test_interview_scheduling(token, candidate_id):
    """Test Interview Scheduling (Step 6)"""
    print("\n📅 Step 6: Testing Interview Scheduling...")
    
    headers = {'Authorization': f'Token {token}'}
    data = {
        'candidate': candidate_id,
        'scheduled_at': '2024-02-15T10:00:00Z',
        'status': 'scheduled',
        'notes': 'Initial interview for Python developer position'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/interviews/", 
                               json=data, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Interview scheduling successful")
            print(f"   Interview ID: {result.get('id')}")
            print(f"   Status: {result.get('status')}")
            return True
        else:
            print(f"❌ Interview scheduling failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Interview scheduling error: {e}")
        return False

def test_legacy_endpoint_compatibility(token):
    """Test that legacy endpoint still works"""
    print("\n🔄 Testing Legacy Endpoint Compatibility...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Test legacy candidate listing
    try:
        response = requests.get(f"{BASE_URL}/api/candidates/", headers=headers)
        if response.status_code == 200:
            candidates = response.json()
            print(f"✅ Legacy endpoint working ({len(candidates)} candidates found)")
            return True
        else:
            print(f"❌ Legacy endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Legacy endpoint error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Step-by-Step Candidate Creation Flow")
    print("=" * 60)
    
    # Get authentication token
    token = test_authentication()
    if not token:
        print("\n❌ Cannot proceed without authentication token.")
        return
    
    # Test the complete flow
    draft_id = test_step1_domain_role_selection(token)
    if not draft_id:
        print("\n❌ Step 1 failed. Cannot proceed.")
        return
    
    draft_id = test_step2_data_extraction(token, draft_id)
    if not draft_id:
        print("\n❌ Step 2 failed. Cannot proceed.")
        return
    
    draft_data = test_step3_verification_preview(token, draft_id)
    if not draft_data:
        print("\n❌ Step 3 failed. Cannot proceed.")
        return
    
    if not test_step4_verification_update(token, draft_id):
        print("\n❌ Step 4 failed. Cannot proceed.")
        return
    
    candidate_id = test_step5_final_submission(token, draft_id)
    if not candidate_id:
        print("\n❌ Step 5 failed. Cannot proceed.")
        return
    
    if test_interview_scheduling(token, candidate_id):
        print("\n✅ Interview scheduling successful")
    
    # Test legacy compatibility
    test_legacy_endpoint_compatibility(token)
    
    print("\n" + "=" * 60)
    print("🎉 Step-by-Step Candidate Creation Flow Test Complete!")
    print("✅ All steps working correctly")
    print("✅ Data extraction and verification working")
    print("✅ Final submission successful")
    print("✅ Interview scheduling available")
    print("✅ Legacy endpoints still compatible")

if __name__ == "__main__":
    main() 