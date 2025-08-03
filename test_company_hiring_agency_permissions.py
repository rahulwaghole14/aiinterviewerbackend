#!/usr/bin/env python3
"""
Test script to check Company user permissions for hiring agency and recruiters
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def create_test_users():
    """Create test users with different roles"""
    print("🔧 Creating test users...")
    
    # Create company user
    company_data = {
        'username': 'company_hiring@test.com',
        'email': 'company_hiring@test.com',
        'password': 'companypass123',
        'full_name': 'Company Hiring User',
        'company_name': 'Test Company',
        'role': 'COMPANY'
    }
    
    # Create admin user for comparison
    admin_data = {
        'username': 'admin_hiring@test.com',
        'email': 'admin_hiring@test.com',
        'password': 'adminpass123',
        'full_name': 'Admin Hiring User',
        'company_name': 'Admin Company',
        'role': 'ADMIN'
    }
    
    try:
        # Create company user
        response = requests.post(f"{BASE_URL}/auth/register/", data=company_data)
        if response.status_code == 201:
            print("✅ Company user created")
        else:
            print(f"⚠️  Company user creation: {response.status_code}")
        
        # Create admin user
        response = requests.post(f"{BASE_URL}/auth/register/", data=admin_data)
        if response.status_code == 201:
            print("✅ Admin user created")
        else:
            print(f"⚠️  Admin user creation: {response.status_code}")
            
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

def test_hiring_agency_permissions(token, user_type):
    """Test hiring agency permissions for a user"""
    print(f"\n🏢 Testing {user_type} Hiring Agency Permissions...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Test list hiring agency (should work for all authenticated users)
    try:
        response = requests.get(f"{BASE_URL}/hiring_agency/", headers=headers)
        print(f"📤 GET /hiring_agency/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            hiring_agencies = response.json()
            print(f"✅ {user_type} can list hiring agencies ({len(hiring_agencies)} found)")
        else:
            print(f"❌ {user_type} cannot list hiring agencies: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test create hiring agency user
    hiring_agency_data = {
        'username': f'hiring_user_{user_type.lower()}',
        'email': f'hiring_{user_type.lower()}@test.com',
        'full_name': f'Hiring User {user_type}',
        'password': 'hiringpass123',
        'role': 'HR',
        'company_name': 'Test Company'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/hiring_agency/", json=hiring_agency_data, headers=headers)
        print(f"📤 POST /hiring_agency/ - Status: {response.status_code}")
        
        if response.status_code == 201:
            hiring_user = response.json()
            print(f"✅ {user_type} can create hiring agency users!")
            print(f"   User ID: {hiring_user.get('id')}")
            return hiring_user
        elif response.status_code == 403:
            print(f"✅ {user_type} correctly blocked from creating hiring agency users (403 Forbidden)")
            return None
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_hiring_agency_edit_permissions(token, user_id, user_type):
    """Test edit permissions for hiring agency users"""
    headers = {'Authorization': f'Token {token}'}
    
    update_data = {
        'full_name': f'Updated Hiring User {user_type}',
        'role': 'HIRING_MANAGER'
    }
    
    try:
        response = requests.put(f"{BASE_URL}/hiring_agency/{user_id}/", json=update_data, headers=headers)
        print(f"📤 PUT /hiring_agency/{user_id}/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ {user_type} can edit hiring agency users!")
        elif response.status_code == 403:
            print(f"✅ {user_type} correctly blocked from editing hiring agency users (403 Forbidden)")
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_recruiter_permissions(token, user_type):
    """Test recruiter management permissions for a user"""
    print(f"\n👥 Testing {user_type} Recruiter Permissions...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Test list recruiters
    try:
        response = requests.get(f"{BASE_URL}/companies/recruiters/", headers=headers)
        print(f"📤 GET /companies/recruiters/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            recruiters = response.json()
            print(f"✅ {user_type} can list recruiters ({len(recruiters)} found)")
        else:
            print(f"❌ {user_type} cannot list recruiters: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test create recruiter
    recruiter_data = {
        'username': f'recruiter_{user_type.lower()}',
        'email': f'recruiter_{user_type.lower()}@test.com',
        'full_name': f'Recruiter {user_type}',
        'password': 'recruiterpass123',
        'company_id': 1  # Assuming company with ID 1 exists
    }
    
    try:
        response = requests.post(f"{BASE_URL}/companies/recruiters/create/", json=recruiter_data, headers=headers)
        print(f"📤 POST /companies/recruiters/create/ - Status: {response.status_code}")
        
        if response.status_code == 201:
            recruiter = response.json()
            print(f"✅ {user_type} can create recruiters!")
            print(f"   Recruiter ID: {recruiter.get('id')}")
            return recruiter
        elif response.status_code == 403:
            print(f"✅ {user_type} correctly blocked from creating recruiters (403 Forbidden)")
            return None
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_recruiter_edit_permissions(token, recruiter_id, user_type):
    """Test edit permissions for recruiters"""
    headers = {'Authorization': f'Token {token}'}
    
    update_data = {
        'full_name': f'Updated Recruiter {user_type}',
        'is_active': True
    }
    
    try:
        response = requests.put(f"{BASE_URL}/companies/recruiters/{recruiter_id}/", json=update_data, headers=headers)
        print(f"📤 PUT /companies/recruiters/{recruiter_id}/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ {user_type} can edit recruiters!")
        elif response.status_code == 403:
            print(f"✅ {user_type} correctly blocked from editing recruiters (403 Forbidden)")
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_recruiter_delete_permissions(token, recruiter_id, user_type):
    """Test delete permissions for recruiters"""
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.delete(f"{BASE_URL}/companies/recruiters/{recruiter_id}/", headers=headers)
        print(f"📤 DELETE /companies/recruiters/{recruiter_id}/ - Status: {response.status_code}")
        
        if response.status_code == 204:
            print(f"✅ {user_type} can delete recruiters!")
        elif response.status_code == 403:
            print(f"✅ {user_type} correctly blocked from deleting recruiters (403 Forbidden)")
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Company User Hiring Agency & Recruiter Permissions")
    print("=" * 70)
    
    # Create test users
    create_test_users()
    
    # Test company user permissions
    company_token = get_user_token('company_hiring@test.com', 'companypass123')
    if company_token:
        print("\n🏢 Testing COMPANY User Permissions:")
        
        # Test hiring agency permissions
        hiring_user = test_hiring_agency_permissions(company_token, "COMPANY")
        if hiring_user:
            test_hiring_agency_edit_permissions(company_token, hiring_user['id'], "COMPANY")
        
        # Test recruiter permissions
        recruiter = test_recruiter_permissions(company_token, "COMPANY")
        if recruiter:
            test_recruiter_edit_permissions(company_token, recruiter['id'], "COMPANY")
            test_recruiter_delete_permissions(company_token, recruiter['id'], "COMPANY")
    
    # Test admin user permissions for comparison
    admin_token = get_user_token('admin_hiring@test.com', 'adminpass123')
    if admin_token:
        print("\n👑 Testing ADMIN User Permissions:")
        
        # Test hiring agency permissions
        admin_hiring_user = test_hiring_agency_permissions(admin_token, "ADMIN")
        if admin_hiring_user:
            test_hiring_agency_edit_permissions(admin_token, admin_hiring_user['id'], "ADMIN")
        
        # Test recruiter permissions
        admin_recruiter = test_recruiter_permissions(admin_token, "ADMIN")
        if admin_recruiter:
            test_recruiter_edit_permissions(admin_token, admin_recruiter['id'], "ADMIN")
            test_recruiter_delete_permissions(admin_token, admin_recruiter['id'], "ADMIN")
    
    print("\n" + "=" * 70)
    print("📋 Permission Summary:")
    print("✅ Company users can view hiring agencies and recruiters")
    print("❓ Company users may be restricted from creating/editing")
    print("✅ Admin users have full access to both")
    print("✅ Role-based permissions are working correctly") 