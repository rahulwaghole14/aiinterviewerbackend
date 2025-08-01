#!/usr/bin/env python3
"""
Test script with real authentication for Bulk Resume Processing
"""

import requests
import json
import os
from pathlib import Path

# API Base URL
BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get authentication token by logging in"""
    print("🔐 Getting authentication token...")
    
    # First, try to register a test user
    register_data = {
        'username': 'testuser@example.com',
        'email': 'testuser@example.com',
        'password': 'testpassword123',
        'full_name': 'Test User',
        'company_name': 'Test Company',
        'role': 'COMPANY'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register/", data=register_data)
        if response.status_code == 201:
            print("✅ User registered successfully")
        else:
            print(f"⚠️  Registration status: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Registration error: {e}")
    
    # Now try to login
    login_data = {
        'email': 'testuser@example.com',
        'password': 'testpassword123'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            if token:
                print("✅ Login successful! Got auth token")
                return token
            else:
                print("❌ No token in response")
                print(f"Response: {data}")
                return None
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_bulk_upload_with_real_auth(token):
    """Test bulk upload with real authentication"""
    print("\n🧪 Testing Bulk Upload with Real Auth...")
    
    headers = {
        'Authorization': f'Token {token}'
    }
    
    # Create mock resume files for testing
    mock_resume_content = b"""
    John Doe
    Software Engineer
    Email: john.doe@example.com
    Phone: +1-555-123-4567
    Experience: 5 years in software development
    Skills: Python, Django, React, AWS
    """
    
    files = [
        ('files', ('john_doe.pdf', mock_resume_content, 'application/pdf')),
        ('files', ('jane_smith.docx', mock_resume_content, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')),
        ('files', ('bob_wilson.pdf', mock_resume_content, 'application/pdf')),
    ]
    
    try:
        response = requests.post(f"{BASE_URL}/api/resumes/bulk-upload/", 
                               files=files, headers=headers)
        print(f"📤 POST /api/resumes/bulk-upload/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Bulk upload successful!")
            print(f"📊 Summary: {result.get('summary', {})}")
            print("\n📋 Results:")
            for i, res in enumerate(result.get('results', []), 1):
                if res.get('success'):
                    print(f"  {i}. ✅ {res.get('filename')} - {res.get('extracted_data', {})}")
                else:
                    print(f"  {i}. ❌ {res.get('filename')} - {res.get('error_message', 'Unknown error')}")
        else:
            print(f"❌ Bulk upload failed: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_single_upload_with_real_auth(token):
    """Test single resume upload with real authentication"""
    print("\n📄 Testing Single Resume Upload...")
    
    headers = {
        'Authorization': f'Token {token}'
    }
    
    mock_resume_content = b"""
    Alice Johnson
    Data Scientist
    Email: alice.johnson@example.com
    Phone: +1-555-987-6543
    Experience: 3 years in data science
    Skills: Python, Machine Learning, SQL, TensorFlow
    """
    
    files = {
        'file': ('alice_johnson.pdf', mock_resume_content, 'application/pdf')
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/resumes/", 
                               files=files, headers=headers)
        print(f"📤 POST /api/resumes/ - Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Single upload successful!")
            print(f"📄 Resume ID: {result.get('id')}")
            print(f"📝 Parsed text length: {len(result.get('parsed_text', ''))} characters")
        else:
            print(f"❌ Single upload failed: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_resume_listing_with_real_auth(token):
    """Test resume listing with real authentication"""
    print("\n📋 Testing Resume Listing...")
    
    headers = {
        'Authorization': f'Token {token}'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/resumes/", headers=headers)
        print(f"📤 GET /api/resumes/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            resumes = response.json()
            print(f"✅ Resume listing successful!")
            print(f"📊 Total resumes: {len(resumes)}")
            for i, resume in enumerate(resumes, 1):
                print(f"  {i}. {resume.get('id')} - {resume.get('file')}")
        else:
            print(f"❌ Resume listing failed: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_jobs_with_real_auth(token):
    """Test jobs endpoints with real authentication"""
    print("\n💼 Testing Jobs Endpoints...")
    
    headers = {
        'Authorization': f'Token {token}'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/jobs/", headers=headers)
        print(f"📤 GET /api/jobs/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            jobs = response.json()
            print(f"✅ Jobs listing successful!")
            print(f"📊 Total jobs: {len(jobs)}")
        else:
            print(f"❌ Jobs listing failed: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 AI Interviewer Platform - Authenticated API Testing")
    print("=" * 60)
    
    # Get authentication token
    token = get_auth_token()
    
    if token:
        print(f"🔑 Using token: {token[:20]}...")
        
        # Test all endpoints with real authentication
        test_bulk_upload_with_real_auth(token)
        test_single_upload_with_real_auth(token)
        test_resume_listing_with_real_auth(token)
        test_jobs_with_real_auth(token)
        
        print("\n" + "=" * 60)
        print("📋 Testing Summary:")
        print("✅ Authentication working")
        print("✅ Bulk resume processing tested")
        print("✅ Single resume upload tested")
        print("✅ Resume listing tested")
        print("✅ Jobs endpoints tested")
        print("\n🎯 All tests completed!")
    else:
        print("❌ Cannot proceed without authentication token") 