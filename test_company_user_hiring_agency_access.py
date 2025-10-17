#!/usr/bin/env python3
"""
Test script to verify company user access to hiring agencies
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


def get_company_user_token(company_email, password):
    """Get company user authentication token"""
    try:
        login_data = {"email": company_email, "password": password}

        response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)

        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        else:
            print(f"❌ Company user login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error during company user login: {e}")
        return None


def test_admin_sees_all_hiring_agencies(token):
    """Test that admin sees all hiring agencies from all companies"""
    print("\n🔧 Testing Admin Access to All Hiring Agencies")
    print("=" * 50)

    try:
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

        print("📤 Admin fetching all hiring agencies...")

        response = requests.get(f"{BASE_URL}/api/hiring_agency/", headers=headers)

        print(f"📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            agencies = response.json()
            print(f"📥 Admin sees {len(agencies)} hiring agencies")

            # Group by company
            companies = {}
            for agency in agencies:
                company_name = agency.get("company_name", "No Company")
                if company_name not in companies:
                    companies[company_name] = []
                companies[company_name].append(agency)

            print("📊 Hiring agencies by company:")
            for company_name, company_agencies in companies.items():
                print(f"   - {company_name}: {len(company_agencies)} hiring agencies")
                for agency in company_agencies:
                    print(
                        f"     * {agency['email']} ({agency['first_name']} {agency['last_name']})"
                    )

            return agencies
        else:
            print(f"❌ Failed to fetch hiring agencies: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Error during admin test: {e}")
        return None


def test_company_user_access(company_email, password, expected_company_name):
    """Test that company user only sees hiring agencies from their company"""
    print(f"\n🔧 Testing Company User Access: {company_email}")
    print("=" * 50)

    try:
        # Get company user token
        token = get_company_user_token(company_email, password)
        if not token:
            print(f"❌ Cannot get token for {company_email}")
            return False

        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

        print(f"📤 Company user fetching hiring agencies...")

        response = requests.get(f"{BASE_URL}/api/hiring_agency/", headers=headers)

        print(f"📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            agencies = response.json()
            print(f"📥 Company user sees {len(agencies)} hiring agencies")

            # Check if all agencies belong to the expected company
            wrong_company_agencies = []
            correct_company_agencies = []

            for agency in agencies:
                agency_company = agency.get("company_name", "No Company")
                if agency_company == expected_company_name:
                    correct_company_agencies.append(agency)
                else:
                    wrong_company_agencies.append(agency)

            print(f"📊 Company filtering results:")
            print(
                f"   - Correct company ({expected_company_name}): {len(correct_company_agencies)} agencies"
            )
            print(f"   - Wrong company: {len(wrong_company_agencies)} agencies")

            if wrong_company_agencies:
                print("❌ Company user can see hiring agencies from other companies:")
                for agency in wrong_company_agencies:
                    print(f"   - {agency['email']} (Company: {agency['company_name']})")
                return False
            else:
                print(
                    "✅ Company user only sees hiring agencies from their own company"
                )
                if correct_company_agencies:
                    print("   Hiring agencies in their company:")
                    for agency in correct_company_agencies:
                        print(
                            f"   - {agency['email']} ({agency['first_name']} {agency['last_name']})"
                        )
                return True
        else:
            print(f"❌ Failed to fetch hiring agencies: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error during company user test: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Starting Company User Hiring Agency Access Tests")
    print("=" * 60)

    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Cannot proceed without admin token")
        return

    print(f"✅ Admin token obtained: {admin_token[:20]}...")

    # Test 1: Admin sees all hiring agencies
    all_agencies = test_admin_sees_all_hiring_agencies(admin_token)

    if not all_agencies:
        print("❌ Cannot proceed without admin access")
        return

    # Test 2: Company users only see their own hiring agencies
    # Note: This would require actual company user credentials
    # For now, we'll just show what we found from admin access

    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    if all_agencies:
        print("✅ Admin can see all hiring agencies: PASSED")

        # Group by company for analysis
        companies = {}
        for agency in all_agencies:
            company_name = agency.get("company_name", "No Company")
            if company_name not in companies:
                companies[company_name] = []
            companies[company_name].append(agency)

        print(f"\n📊 Companies with hiring agencies:")
        for company_name, agencies in companies.items():
            print(f"   - {company_name}: {len(agencies)} hiring agencies")

        print(f"\n⚠️  To test company user access, you would need:")
        print(f"   - Company user credentials for each company")
        print(f"   - Test that each company user only sees their own hiring agencies")

    else:
        print("❌ Admin can see all hiring agencies: FAILED")

    print("\n🎉 Testing completed!")


if __name__ == "__main__":
    main()
