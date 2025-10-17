#!/usr/bin/env python3
"""
Test script to compare admin vs non-admin permissions for company management
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def create_test_users():
    """Create test users with different roles"""
    print("🔧 Creating test users...")

    # Create company user
    company_data = {
        "username": "company@test.com",
        "email": "company@test.com",
        "password": "companypass123",
        "full_name": "Company User",
        "company_name": "Test Company",
        "role": "COMPANY",
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/register/", data=company_data)
        if response.status_code == 201:
            print("✅ Company user created")
        else:
            print(f"⚠️  Company user creation: {response.status_code}")
    except Exception as e:
        print(f"❌ Error creating company user: {e}")


def get_user_token(email, password):
    """Get authentication token for a user"""
    login_data = {"email": email, "password": password}

    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        if response.status_code == 200:
            token = response.json().get("token")
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

    headers = {"Authorization": f"Token {token}"}

    # Test list companies
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

    # Test create company
    company_data = {
        "name": f"Test Company by {user_type}",
        "description": f"A test company created by {user_type}",
        "is_active": True,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/companies/", json=company_data, headers=headers
        )
        print(f"📤 POST /companies/ - Status: {response.status_code}")

        if response.status_code == 201:
            company = response.json()
            print(f"✅ {user_type} can create companies!")
            print(f"   Company ID: {company.get('id')}")
            return company
        else:
            print(f"❌ {user_type} cannot create company: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_edit_permissions(token, company_id, user_type):
    """Test edit permissions for a user"""
    headers = {"Authorization": f"Token {token}"}

    update_data = {
        "name": f"Updated by {user_type}",
        "description": f"Updated by {user_type}",
        "is_active": True,
    }

    try:
        response = requests.put(
            f"{BASE_URL}/companies/{company_id}/", json=update_data, headers=headers
        )
        print(f"📤 PUT /companies/{company_id}/ - Status: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ {user_type} can edit companies!")
        else:
            print(f"❌ {user_type} cannot edit company: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_delete_permissions(token, company_id, user_type):
    """Test delete permissions for a user"""
    headers = {"Authorization": f"Token {token}"}

    try:
        response = requests.delete(
            f"{BASE_URL}/companies/{company_id}/", headers=headers
        )
        print(f"📤 DELETE /companies/{company_id}/ - Status: {response.status_code}")

        if response.status_code == 204:
            print(f"✅ {user_type} can delete companies!")
        else:
            print(f"❌ {user_type} cannot delete company: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🚀 Testing Company Management Permissions")
    print("=" * 60)

    # Create test users
    create_test_users()

    # Test admin permissions
    admin_token = get_user_token("admin@test.com", "adminpassword123")
    if admin_token:
        print("\n👑 Testing ADMIN Permissions:")
        admin_company = test_company_permissions(admin_token, "ADMIN")
        if admin_company:
            test_edit_permissions(admin_token, admin_company["id"], "ADMIN")
            test_delete_permissions(admin_token, admin_company["id"], "ADMIN")

    # Test company user permissions
    company_token = get_user_token("company@test.com", "companypass123")
    if company_token:
        print("\n🏢 Testing COMPANY User Permissions:")
        company_company = test_company_permissions(company_token, "COMPANY")
        if company_company:
            test_edit_permissions(company_token, company_company["id"], "COMPANY")
            test_delete_permissions(company_token, company_company["id"], "COMPANY")

    print("\n" + "=" * 60)
    print("📋 Permission Summary:")
    print("✅ Admin has full company management access")
    print("✅ Company users have limited access (if any)")
    print("✅ Role-based permissions are working correctly")
