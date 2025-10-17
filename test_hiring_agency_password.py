#!/usr/bin/env python3
"""
Test script to verify hiring agency creation with password field
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@rslsolution.com"
ADMIN_PASSWORD = "admin123"


def get_admin_token():
    """Get admin authentication token"""
    try:
        login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}

        response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)

        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error during login: {e}")
        return None


def test_create_hiring_agency_with_password(token):
    """Test creating a hiring agency with password"""
    print("\n🔧 Testing Hiring Agency Creation with Password")
    print("=" * 50)

    try:
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

        # Test data for hiring agency creation
        hiring_agency_data = {
            "email": "testagency@example.com",
            "password": "agency123",
            "role": "Hiring Agency",
            "first_name": "Test",
            "last_name": "Agency",
            "phone_number": "+1234567890",
            "company_name": "Test Company",
            "linkedin_url": "https://linkedin.com/in/testagency",
        }

        print(
            f"📤 Creating hiring agency with data: {json.dumps(hiring_agency_data, indent=2)}"
        )

        response = requests.post(
            f"{BASE_URL}/api/hiring_agency/add_user/",
            json=hiring_agency_data,
            headers=headers,
        )

        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 201:
            print("✅ Hiring agency created successfully with password")
            return response.json()
        else:
            print("❌ Hiring agency creation failed")
            return None

    except Exception as e:
        print(f"❌ Error during hiring agency creation: {e}")
        return None


def test_create_hiring_agency_without_password(token):
    """Test creating a hiring agency without password (backward compatibility)"""
    print("\n🔧 Testing Hiring Agency Creation without Password")
    print("=" * 50)

    try:
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

        # Test data for hiring agency creation without password
        hiring_agency_data = {
            "email": "testagency2@example.com",
            "role": "Hiring Agency",
            "first_name": "Test",
            "last_name": "Agency2",
            "phone_number": "+1234567891",
            "company_name": "Test Company",
            "linkedin_url": "https://linkedin.com/in/testagency2",
        }

        print(
            f"📤 Creating hiring agency with data: {json.dumps(hiring_agency_data, indent=2)}"
        )

        response = requests.post(
            f"{BASE_URL}/api/hiring_agency/add_user/",
            json=hiring_agency_data,
            headers=headers,
        )

        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 201:
            print("✅ Hiring agency created successfully without password")
            return response.json()
        else:
            print("❌ Hiring agency creation failed")
            return None

    except Exception as e:
        print(f"❌ Error during hiring agency creation: {e}")
        return None


def test_get_all_hiring_agencies(token):
    """Test that get all hiring agencies API works and doesn't return password"""
    print("\n🔧 Testing Get All Hiring Agencies API")
    print("=" * 50)

    try:
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

        print("📤 Fetching all hiring agencies...")

        response = requests.get(f"{BASE_URL}/api/hiring_agency/", headers=headers)

        print(f"📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            agencies = response.json()
            print(f"📥 Found {len(agencies)} hiring agencies")

            # Check that password field is not returned in response
            password_found = False
            for agency in agencies:
                if "password" in agency:
                    password_found = True
                    print(f"❌ Agency '{agency['email']}' has password field exposed")
                else:
                    print(
                        f"✅ Agency '{agency['email']}' password field properly hidden"
                    )

            if not password_found:
                print(
                    "✅ Password field is properly hidden in get all hiring agencies API"
                )
                return True
            else:
                print("❌ Password field is exposed in get all hiring agencies API")
                return False
        else:
            print(f"❌ Failed to fetch hiring agencies: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error during get all hiring agencies: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Starting Hiring Agency Password API Tests")
    print("=" * 60)

    # Get admin token
    token = get_admin_token()
    if not token:
        print("❌ Cannot proceed without admin token")
        return

    print(f"✅ Admin token obtained: {token[:20]}...")

    # Test 1: Create hiring agency with password
    created_agency = test_create_hiring_agency_with_password(token)

    # Test 2: Create hiring agency without password (backward compatibility)
    created_agency_simple = test_create_hiring_agency_without_password(token)

    # Test 3: Get all hiring agencies and verify password is not exposed
    password_hidden = test_get_all_hiring_agencies(token)

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    if created_agency:
        print("✅ Hiring agency creation with password: PASSED")
    else:
        print("❌ Hiring agency creation with password: FAILED")

    if created_agency_simple:
        print("✅ Hiring agency creation without password: PASSED")
    else:
        print("❌ Hiring agency creation without password: FAILED")

    if password_hidden:
        print("✅ Password field properly hidden: PASSED")
    else:
        print("❌ Password field properly hidden: FAILED")

    print("\n🎉 Testing completed!")


if __name__ == "__main__":
    main()
