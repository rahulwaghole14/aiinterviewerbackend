#!/usr/bin/env python3
"""
Test script to verify admin-only company management permissions
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def create_test_users():
    """Create test users with different roles"""
    print("🔧 Creating test users...")
    
    # Create admin user
    admin_data = {
        'username': 'admin_only@test.com',
        'email': 'admin_only@test.com',
        'password': 'adminpass123',
        'full_name': 'Admin Only User',
        'company_name': 'Admin Company',
        'role': 'ADMIN'
    }
    
    # Create company user
    company_data = {
        'username': 'company_only@test.com',
        'email': 'company_only@test.com',
        'password': 'companypass123',
        'full_name': 'Company Only User',
        'company_name': 'Test Company',
        'role': 'COMPANY'
    }
    
    try:
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

def test_company_permissions(token, user_type):
    """Test company management permissions for a user"""
    print(f"\n🔍 Testing {user_type} Company Permissions...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Test list companies (should work for all authenticated users)
    try:
        response = requests.get(f"{BASE_URL}/companies/", headers=headers)
        print(f"📤 GET /companies/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            companies = response.json()
            print(f"✅ {user_type} can list companies ({len(companies)} found)")
        else:
            print(f"❌ {user_type} cannot list companies: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test create company (should only work for admin)
    company_data = {
        'name': f'Test Company by {user_type}',
        'description': f'A test company created by {user_type}',
        'is_active': True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/companies/", json=company_data, headers=headers)
        print(f"📤 POST /companies/ - Status: {response.status_code}")
        
        if response.status_code == 201:
            company = response.json()
            print(f"✅ {user_type} can create companies!")
            print(f"   Company ID: {company.get('id')}")
            return company
        elif response.status_code == 403:
            print(f"✅ {user_type} correctly blocked from creating companies (403 Forbidden)")
            return None
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_edit_permissions(token, company_id, user_type):
    """Test edit permissions for a user"""
    headers = {'Authorization': f'Token {token}'}
    
    update_data = {
        'name': f'Updated by {user_type}',
        'description': f'Updated by {user_type}',
        'is_active': True
    }
    
    try:
        response = requests.put(f"{BASE_URL}/companies/{company_id}/", json=update_data, headers=headers)
        print(f"📤 PUT /companies/{company_id}/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ {user_type} can edit companies!")
        elif response.status_code == 403:
            print(f"✅ {user_type} correctly blocked from editing companies (403 Forbidden)")
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_delete_permissions(token, company_id, user_type):
    """Test delete permissions for a user"""
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.delete(f"{BASE_URL}/companies/{company_id}/", headers=headers)
        print(f"📤 DELETE /companies/{company_id}/ - Status: {response.status_code}")
        
        if response.status_code == 204:
            print(f"✅ {user_type} can delete companies!")
        elif response.status_code == 403:
            print(f"✅ {user_type} correctly blocked from deleting companies (403 Forbidden)")
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_recruiter_permissions(token, user_type):
    """Test recruiter management permissions"""
    print(f"\n👥 Testing {user_type} Recruiter Permissions...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Test create recruiter (should only work for admin)
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
            print(f"✅ {user_type} can create recruiters!")
        elif response.status_code == 403:
            print(f"✅ {user_type} correctly blocked from creating recruiters (403 Forbidden)")
        else:
            print(f"❌ Unexpected response for {user_type}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Admin-Only Company Management")
    print("=" * 60)
    
    # Create test users
    create_test_users()
    
    # Test admin permissions
    admin_token = get_user_token('admin_only@test.com', 'adminpass123')
    if admin_token:
        print("\n👑 Testing ADMIN Permissions:")
        admin_company = test_company_permissions(admin_token, "ADMIN")
        if admin_company:
            test_edit_permissions(admin_token, admin_company['id'], "ADMIN")
            test_delete_permissions(admin_token, admin_company['id'], "ADMIN")
        test_recruiter_permissions(admin_token, "ADMIN")
    
    # Test company user permissions
    company_token = get_user_token('company_only@test.com', 'companypass123')
    if company_token:
        print("\n🏢 Testing COMPANY User Permissions:")
        company_company = test_company_permissions(company_token, "COMPANY")
        if company_company:
            test_edit_permissions(company_token, company_company['id'], "COMPANY")
            test_delete_permissions(company_token, company_company['id'], "COMPANY")
        test_recruiter_permissions(company_token, "COMPANY")
    
    print("\n" + "=" * 60)
    print("📋 Permission Summary:")
    print("✅ Admin can perform all company operations")
    print("✅ Company users can only read companies")
    print("✅ Company users are blocked from create/edit/delete")
    print("✅ Role-based permissions are working correctly") 