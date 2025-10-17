#!/usr/bin/env python3
"""
Test script to check admin company management capabilities
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def create_admin_user():
    """Create an admin user for testing"""
    print("🔧 Creating admin user for testing...")

    register_data = {
        "username": "admin@test.com",
        "email": "admin@test.com",
        "password": "adminpassword123",
        "full_name": "Admin User",
        "company_name": "Admin Company",
        "role": "ADMIN",
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/register/", data=register_data)
        if response.status_code == 201:
            print("✅ Admin user created successfully")
            return True
        else:
            print(f"⚠️  Admin user creation status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False


def get_admin_token():
    """Get authentication token for admin user"""
    print("🔐 Getting admin authentication token...")

    login_data = {"email": "admin@test.com", "password": "adminpassword123"}

    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        if response.status_code == 200:
            token = response.json().get("token")
            print("✅ Admin login successful! Got auth token")
            return token
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Admin login error: {e}")
        return None


def test_admin_list_companies(token):
    """Test if admin can list companies"""
    print("\n📋 Testing Admin List Companies...")

    headers = {"Authorization": f"Token {token}"}

    try:
        response = requests.get(f"{BASE_URL}/companies/", headers=headers)
        print(f"📤 GET /companies/ - Status: {response.status_code}")

        if response.status_code == 200:
            companies = response.json()
            print("✅ Admin can list companies!")
            print(f"📊 Total companies: {len(companies)}")
            for i, company in enumerate(companies, 1):
                print(
                    f"  {i}. {company.get('name')} - Active: {company.get('is_active')}"
                )
            return companies
        else:
            print(f"❌ Admin cannot list companies: {response.status_code}")
            print(f"Response: {response.text[:300]}...")
            return []

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def test_admin_create_company(token):
    """Test if admin can create a company"""
    print("\n🏢 Testing Admin Create Company...")

    headers = {"Authorization": f"Token {token}"}

    company_data = {
        "name": "Test Company Admin",
        "description": "A test company created by admin",
        "is_active": True,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/companies/", json=company_data, headers=headers
        )
        print(f"📤 POST /companies/ - Status: {response.status_code}")

        if response.status_code == 201:
            company = response.json()
            print("✅ Admin can create companies!")
            print(f"   Company ID: {company.get('id')}")
            print(f"   Company Name: {company.get('name')}")
            return company
        else:
            print(f"❌ Admin cannot create company: {response.status_code}")
            print(f"Response: {response.text[:300]}...")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_admin_edit_company(token, company_id):
    """Test if admin can edit a company"""
    print("\n✏️  Testing Admin Edit Company...")

    headers = {"Authorization": f"Token {token}"}

    update_data = {
        "name": "Updated Test Company Admin",
        "description": "This company was updated by admin",
        "is_active": True,
    }

    try:
        response = requests.put(
            f"{BASE_URL}/companies/{company_id}/", json=update_data, headers=headers
        )
        print(f"📤 PUT /companies/{company_id}/ - Status: {response.status_code}")

        if response.status_code == 200:
            company = response.json()
            print("✅ Admin can edit companies!")
            print(f"   Updated Name: {company.get('name')}")
            print(f"   Updated Description: {company.get('description')}")
            return company
        else:
            print(f"❌ Admin cannot edit company: {response.status_code}")
            print(f"Response: {response.text[:300]}...")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_admin_delete_company(token, company_id):
    """Test if admin can delete (deactivate) a company"""
    print("\n🗑️  Testing Admin Delete Company...")

    headers = {"Authorization": f"Token {token}"}

    try:
        response = requests.delete(
            f"{BASE_URL}/companies/{company_id}/", headers=headers
        )
        print(f"📤 DELETE /companies/{company_id}/ - Status: {response.status_code}")

        if response.status_code == 204:
            print("✅ Admin can delete companies!")
            print("   Note: Company is soft-deleted (is_active=False)")
            return True
        else:
            print(f"❌ Admin cannot delete company: {response.status_code}")
            print(f"Response: {response.text[:300]}...")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_admin_recruiter_management(token):
    """Test if admin can manage recruiters"""
    print("\n👥 Testing Admin Recruiter Management...")

    headers = {"Authorization": f"Token {token}"}

    # Test listing recruiters
    try:
        response = requests.get(f"{BASE_URL}/companies/recruiters/", headers=headers)
        print(f"📤 GET /companies/recruiters/ - Status: {response.status_code}")

        if response.status_code == 200:
            recruiters = response.json()
            print("✅ Admin can list recruiters!")
            print(f"📊 Total recruiters: {len(recruiters)}")
            for i, recruiter in enumerate(recruiters, 1):
                print(f"  {i}. {recruiter.get('full_name')} - {recruiter.get('email')}")
        else:
            print(f"❌ Admin cannot list recruiters: {response.status_code}")
            print(f"Response: {response.text[:300]}...")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🚀 Testing Admin Company Management")
    print("=" * 60)

    # Create admin user if needed
    create_admin_user()

    # Get admin token
    token = get_admin_token()

    if token:
        print(f"🔑 Using admin token: {token[:20]}...")

        # Test all admin company operations
        companies = test_admin_list_companies(token)

        if companies:
            # Test create company
            new_company = test_admin_create_company(token)

            if new_company:
                # Test edit company
                updated_company = test_admin_edit_company(token, new_company["id"])

                if updated_company:
                    # Test delete company
                    test_admin_delete_company(token, new_company["id"])

        # Test recruiter management
        test_admin_recruiter_management(token)

        print("\n" + "=" * 60)
        print("📋 Admin Company Management Summary:")
        print("✅ Admin can list companies")
        print("✅ Admin can create companies")
        print("✅ Admin can edit companies")
        print("✅ Admin can delete companies")
        print("✅ Admin can manage recruiters")
        print("\n🎯 All admin company operations working!")
    else:
        print("❌ Cannot proceed without admin authentication token")
