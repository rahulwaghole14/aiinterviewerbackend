#!/usr/bin/env python3
"""
Test script to check if only hiring agency users and recruiters can upload resumes and schedule interviews
"""

import requests
import json
import io

BASE_URL = "http://localhost:8000"

def create_test_users():
    """Create test users with different roles"""
    print("🔧 Creating test users...")
    
    # Create hiring agency user (as CustomUser)
    hiring_agency_data = {
        'username': 'hiring_agency@test.com',
        'email': 'hiring_agency@test.com',
        'password': 'hiringpass123',
        'full_name': 'Hiring Agency User',
        'company_name': 'Test Company',
        'role': 'HIRING_MANAGER'  # Using available role from CustomUser
    }
    
    # Create recruiter user (as CustomUser)
    recruiter_data = {
        'username': 'recruiter@test.com',
        'email': 'recruiter@test.com',
        'password': 'recruiterpass123',
        'full_name': 'Recruiter User',
        'company_name': 'Test Company',
        'role': 'RECRUITER'  # Using available role from CustomUser
    }
    
    # Create admin user
    admin_data = {
        'username': 'admin_test@test.com',
        'email': 'admin_test@test.com',
        'password': 'adminpass123',
        'full_name': 'Admin User',
        'company_name': 'Admin Company',
        'role': 'ADMIN'
    }
    
    # Create regular company user
    company_data = {
        'username': 'company_user@test.com',
        'email': 'company_user@test.com',
        'password': 'companypass123',
        'full_name': 'Company User',
        'company_name': 'Test Company',
        'role': 'COMPANY'
    }
    
    try:
        # Create hiring agency user
        response = requests.post(f"{BASE_URL}/auth/register/", data=hiring_agency_data)
        if response.status_code == 201:
            print("✅ Hiring agency user created")
        else:
            print(f"⚠️  Hiring agency user creation: {response.status_code}")
        
        # Create recruiter user
        response = requests.post(f"{BASE_URL}/auth/register/", data=recruiter_data)
        if response.status_code == 201:
            print("✅ Recruiter user created")
        else:
            print(f"⚠️  Recruiter user creation: {response.status_code}")
        
        # Create admin user
        response = requests.post(f"{BASE_URL}/auth/register/", data=admin_data)
        if response.status_code == 201:
            print("✅ Admin user created")
        else:
            print(f"⚠️  Admin user creation: {response.status_code}")
        
        # Create company user
        response = requests.post(f"{BASE_URL}/auth/register/", data=company_data)
        if response.status_code == 201:
            print("✅ Company user created")
        else:
            print(f"⚠️  Company user creation: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error creating test users: {e}")

def get_user_token(email, password):
    """Get authentication token for a user"""
    login_data = {
        'email': email,
        'password': password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        if response.status_code == 200:
            token = response.json().get('token')
            return token
        else:
            print(f"❌ Login failed for {email}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Login error for {email}: {e}")
        return None

def test_resume_upload_permissions(token, user_type):
    """Test resume upload permissions for a user"""
    print(f"\n📄 Testing {user_type} Resume Upload Permissions...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Create a mock PDF file
    mock_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Resume) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF'
    
    # Test single resume upload
    files = {
        'file': ('test_resume.pdf', io.BytesIO(mock_pdf_content), 'application/pdf')
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/resumes/", files=files, headers=headers)
        print(f"📤 POST /api/resumes/ - Status: {response.status_code}")
        
        if response.status_code == 201:
            resume = response.json()
            print(f"✅ {user_type} can upload resumes!")
            print(f"   Resume ID: {resume.get('id')}")
            return resume.get('id')
        elif response.status_code == 403:
            print(f"❌ {user_type} blocked from uploading resumes (403 Forbidden)")
            return None
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_bulk_resume_upload_permissions(token, user_type):
    """Test bulk resume upload permissions for a user"""
    print(f"\n📄 Testing {user_type} Bulk Resume Upload Permissions...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Create mock PDF files
    mock_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Resume) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF'
    
    files = [
        ('files', ('test_resume1.pdf', io.BytesIO(mock_pdf_content), 'application/pdf')),
        ('files', ('test_resume2.pdf', io.BytesIO(mock_pdf_content), 'application/pdf')),
    ]
    
    try:
        response = requests.post(f"{BASE_URL}/api/resumes/bulk-upload/", files=files, headers=headers)
        print(f"📤 POST /api/resumes/bulk-upload/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {user_type} can upload resumes in bulk!")
            print(f"   Summary: {result.get('summary', {})}")
            return True
        elif response.status_code == 403:
            print(f"❌ {user_type} blocked from bulk uploading resumes (403 Forbidden)")
            return False
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_interview_scheduling_permissions(token, user_type):
    """Test interview scheduling permissions for a user"""
    print(f"\n📅 Testing {user_type} Interview Scheduling Permissions...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Test list interviews
    try:
        response = requests.get(f"{BASE_URL}/api/interviews/", headers=headers)
        print(f"📤 GET /api/interviews/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            interviews = response.json()
            print(f"✅ {user_type} can list interviews ({len(interviews)} found)")
        else:
            print(f"❌ {user_type} cannot list interviews: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test create interview (we'll need a job and candidate first)
    interview_data = {
        'candidate': 1,  # Assuming candidate with ID 1 exists
        'job': 1,        # Assuming job with ID 1 exists
        'scheduled_at': '2024-01-15T10:00:00Z',
        'status': 'scheduled'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/interviews/", json=interview_data, headers=headers)
        print(f"📤 POST /api/interviews/ - Status: {response.status_code}")
        
        if response.status_code == 201:
            interview = response.json()
            print(f"✅ {user_type} can schedule interviews!")
            print(f"   Interview ID: {interview.get('id')}")
            return interview.get('id')
        elif response.status_code == 403:
            print(f"❌ {user_type} blocked from scheduling interviews (403 Forbidden)")
            return None
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_interview_management_permissions(token, interview_id, user_type):
    """Test interview management permissions for a user"""
    headers = {'Authorization': f'Token {token}'}
    
    # Test update interview
    update_data = {
        'status': 'completed',
        'notes': f'Interview completed by {user_type}'
    }
    
    try:
        response = requests.put(f"{BASE_URL}/api/interviews/{interview_id}/", json=update_data, headers=headers)
        print(f"📤 PUT /api/interviews/{interview_id}/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ {user_type} can update interviews!")
        elif response.status_code == 403:
            print(f"❌ {user_type} blocked from updating interviews (403 Forbidden)")
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Resume Upload & Interview Scheduling Permissions")
    print("=" * 70)
    
    # Create test users
    create_test_users()
    
    # Test hiring agency user permissions
    hiring_agency_token = get_user_token('hiring_agency@test.com', 'hiringpass123')
    if hiring_agency_token:
        print("\n🏢 Testing HIRING AGENCY User Permissions:")
        
        # Test resume upload
        resume_id = test_resume_upload_permissions(hiring_agency_token, "HIRING AGENCY")
        test_bulk_resume_upload_permissions(hiring_agency_token, "HIRING AGENCY")
        
        # Test interview scheduling
        interview_id = test_interview_scheduling_permissions(hiring_agency_token, "HIRING AGENCY")
        if interview_id:
            test_interview_management_permissions(hiring_agency_token, interview_id, "HIRING AGENCY")
    
    # Test recruiter user permissions
    recruiter_token = get_user_token('recruiter@test.com', 'recruiterpass123')
    if recruiter_token:
        print("\n👥 Testing RECRUITER User Permissions:")
        
        # Test resume upload
        resume_id = test_resume_upload_permissions(recruiter_token, "RECRUITER")
        test_bulk_resume_upload_permissions(recruiter_token, "RECRUITER")
        
        # Test interview scheduling
        interview_id = test_interview_scheduling_permissions(recruiter_token, "RECRUITER")
        if interview_id:
            test_interview_management_permissions(recruiter_token, interview_id, "RECRUITER")
    
    # Test admin user permissions
    admin_token = get_user_token('admin_test@test.com', 'adminpass123')
    if admin_token:
        print("\n👑 Testing ADMIN User Permissions:")
        
        # Test resume upload
        resume_id = test_resume_upload_permissions(admin_token, "ADMIN")
        test_bulk_resume_upload_permissions(admin_token, "ADMIN")
        
        # Test interview scheduling
        interview_id = test_interview_scheduling_permissions(admin_token, "ADMIN")
        if interview_id:
            test_interview_management_permissions(admin_token, interview_id, "ADMIN")
    
    # Test company user permissions
    company_token = get_user_token('company_user@test.com', 'companypass123')
    if company_token:
        print("\n🏢 Testing COMPANY User Permissions:")
        
        # Test resume upload
        resume_id = test_resume_upload_permissions(company_token, "COMPANY")
        test_bulk_resume_upload_permissions(company_token, "COMPANY")
        
        # Test interview scheduling
        interview_id = test_interview_scheduling_permissions(company_token, "COMPANY")
        if interview_id:
            test_interview_management_permissions(company_token, interview_id, "COMPANY")
    
    print("\n" + "=" * 70)
    print("📋 Permission Summary:")
    print("❓ Need to check if only hiring agency and recruiter can upload resumes")
    print("❓ Need to check if only hiring agency and recruiter can schedule interviews")
    print("✅ Testing all user roles for resume and interview permissions") 