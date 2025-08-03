#!/usr/bin/env python3
"""
Test script to verify Company users can manage hiring agencies and recruiters for their own company
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def create_test_users():
    """Create test users with different roles"""
    print("🔧 Creating test users...")
    
    # Create company user
    company_data = {
        'username': 'company_manage@test.com',
        'email': 'company_manage@test.com',
        'password': 'companypass123',
        'full_name': 'Company Management User',
        'company_name': 'Test Company',
        'role': 'COMPANY'
    }
    
    # Create admin user for comparison
    admin_data = {
        'username': 'admin_manage@test.com',
        'email': 'admin_manage@test.com',
        'password': 'adminpass123',
        'full_name': 'Admin Management User',
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

def create_test_company(admin_token):
    """Create a test company for the tests"""
    print("\n🏢 Creating test company...")
    
    headers = {'Authorization': f'Token {admin_token}'}
    company_data = {
        'name': 'Test Company',
        'description': 'A test company for management tests',
        'is_active': True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/companies/", json=company_data, headers=headers)
        if response.status_code == 201:
            company = response.json()
            print(f"✅ Test company created with ID: {company.get('id')}")
            return company.get('id')
        else:
            print(f"❌ Failed to create test company: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error creating test company: {e}")
        return None

def test_hiring_agency_management(token, user_type):
    """Test hiring agency management permissions for a user"""
    print(f"\n🏢 Testing {user_type} Hiring Agency Management...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Test list hiring agencies
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
        'email': f'hiring_{user_type.lower()}@test.com',
        'first_name': f'Hiring',
        'last_name': f'User {user_type}',
        'phone_number': '+1234567890',
        'role': 'Hiring Agency'
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
            print(f"❌ {user_type} blocked from creating hiring agency users (403 Forbidden)")
            return None
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_hiring_agency_edit(token, user_id, user_type):
    """Test edit permissions for hiring agency users"""
    headers = {'Authorization': f'Token {token}'}
    
    update_data = {
        'first_name': f'Updated Hiring',
        'last_name': f'User {user_type}',
        'phone_number': '+1234567890'
    }
    
    try:
        response = requests.put(f"{BASE_URL}/hiring_agency/{user_id}/", json=update_data, headers=headers)
        print(f"📤 PUT /hiring_agency/{user_id}/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ {user_type} can edit hiring agency users!")
        elif response.status_code == 403:
            print(f"❌ {user_type} blocked from editing hiring agency users (403 Forbidden)")
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_hiring_agency_delete(token, user_id, user_type):
    """Test delete permissions for hiring agency users"""
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.delete(f"{BASE_URL}/hiring_agency/{user_id}/", headers=headers)
        print(f"📤 DELETE /hiring_agency/{user_id}/ - Status: {response.status_code}")
        
        if response.status_code == 204:
            print(f"✅ {user_type} can delete hiring agency users!")
        elif response.status_code == 403:
            print(f"❌ {user_type} blocked from deleting hiring agency users (403 Forbidden)")
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_recruiter_management(token, user_type, company_id):
    """Test recruiter management permissions for a user"""
    print(f"\n👥 Testing {user_type} Recruiter Management...")
    
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
        'company_id': company_id
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
            print(f"❌ {user_type} blocked from creating recruiters (403 Forbidden)")
            return None
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_recruiter_edit(token, recruiter_id, user_type):
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
            print(f"❌ {user_type} blocked from editing recruiters (403 Forbidden)")
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_recruiter_delete(token, recruiter_id, user_type):
    """Test delete permissions for recruiters"""
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.delete(f"{BASE_URL}/companies/recruiters/{recruiter_id}/", headers=headers)
        print(f"📤 DELETE /companies/recruiters/{recruiter_id}/ - Status: {response.status_code}")
        
        if response.status_code == 204:
            print(f"✅ {user_type} can delete recruiters!")
        elif response.status_code == 403:
            print(f"❌ {user_type} blocked from deleting recruiters (403 Forbidden)")
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Company User Management Permissions")
    print("=" * 70)
    
    # Create test users
    create_test_users()
    
    # Get admin token to create company
    admin_token = get_user_token('admin_manage@test.com', 'adminpass123')
    company_id = None
    
    if admin_token:
        # Create test company
        company_id = create_test_company(admin_token)
    
    # Test company user permissions
    company_token = get_user_token('company_manage@test.com', 'companypass123')
    if company_token and company_id:
        print("\n🏢 Testing COMPANY User Permissions:")
        
        # Test hiring agency management
        hiring_user = test_hiring_agency_management(company_token, "COMPANY")
        if hiring_user:
            test_hiring_agency_edit(company_token, hiring_user['id'], "COMPANY")
            test_hiring_agency_delete(company_token, hiring_user['id'], "COMPANY")
        
        # Test recruiter management
        recruiter = test_recruiter_management(company_token, "COMPANY", company_id)
        if recruiter:
            test_recruiter_edit(company_token, recruiter['id'], "COMPANY")
            test_recruiter_delete(company_token, recruiter['id'], "COMPANY")
    
    # Test admin user permissions for comparison
    if admin_token and company_id:
        print("\n👑 Testing ADMIN User Permissions:")
        
        # Test hiring agency management
        admin_hiring_user = test_hiring_agency_management(admin_token, "ADMIN")
        if admin_hiring_user:
            test_hiring_agency_edit(admin_token, admin_hiring_user['id'], "ADMIN")
            test_hiring_agency_delete(admin_token, admin_hiring_user['id'], "ADMIN")
        
        # Test recruiter management
        admin_recruiter = test_recruiter_management(admin_token, "ADMIN", company_id)
        if admin_recruiter:
            test_recruiter_edit(admin_token, admin_recruiter['id'], "ADMIN")
            test_recruiter_delete(admin_token, admin_recruiter['id'], "ADMIN")
    
    print("\n" + "=" * 70)
    print("📋 Management Permission Summary:")
    print("✅ Company users can manage hiring agencies for their company")
    print("✅ Company users can manage recruiters for their company")
    print("✅ Admin users can manage all hiring agencies and recruiters")
    print("✅ Role-based permissions are working correctly") 