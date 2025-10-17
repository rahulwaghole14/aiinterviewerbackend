#!/usr/bin/env python3
"""
Test script to verify hiring agency company ForeignKey relationship
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


def test_get_all_hiring_agencies_with_company_relationship(token):
    """Test that hiring agencies now have proper company relationship"""
    print("\n🔧 Testing Hiring Agency Company Relationship")
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

            # Check that company_name field is present and populated
            company_relationship_found = False
            for agency in agencies:
                if "company_name" in agency and agency["company_name"]:
                    company_relationship_found = True
                    print(
                        f"✅ Agency '{agency['email']}' has company: {agency['company_name']}"
                    )
                else:
                    print(f"⚠️ Agency '{agency['email']}' has no company relationship")

            if company_relationship_found:
                print("✅ Company relationship is working in hiring agency API")
                return True
            else:
                print("❌ No hiring agencies have company relationships")
                return False
        else:
            print(f"❌ Failed to fetch hiring agencies: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error during get all hiring agencies: {e}")
        return False


def test_create_hiring_agency_with_company_relationship(token):
    """Test creating a hiring agency and verify company relationship is set"""
    print("\n🔧 Testing Hiring Agency Creation with Company Relationship")
    print("=" * 50)

    try:
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

        # Test data for hiring agency creation
        hiring_agency_data = {
            "email": "testagency_company@example.com",
            "password": "agency123",
            "role": "Hiring Agency",
            "first_name": "Test",
            "last_name": "AgencyCompany",
            "phone_number": "+1234567892",
            "linkedin_url": "https://linkedin.com/in/testagencycompany",
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
            created_agency = response.json()
            if "company_name" in created_agency and created_agency["company_name"]:
                print(
                    f"✅ Hiring agency created successfully with company: {created_agency['company_name']}"
                )
                return created_agency
            else:
                print("⚠️ Hiring agency created but no company relationship found")
                return created_agency
        else:
            print("❌ Hiring agency creation failed")
            return None

    except Exception as e:
        print(f"❌ Error during hiring agency creation: {e}")
        return None


def test_company_data_integrity(token):
    """Test that company data is consistent between company_name and company relationship"""
    print("\n🔧 Testing Company Data Integrity")
    print("=" * 50)

    try:
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

        # Get all companies
        print("📤 Fetching all companies...")
        companies_response = requests.get(f"{BASE_URL}/api/companies/", headers=headers)

        if companies_response.status_code == 200:
            companies = companies_response.json()
            print(f"📥 Found {len(companies)} companies")

            # Get all hiring agencies
            print("📤 Fetching all hiring agencies...")
            agencies_response = requests.get(
                f"{BASE_URL}/api/hiring_agency/", headers=headers
            )

            if agencies_response.status_code == 200:
                agencies = agencies_response.json()
                print(f"📥 Found {len(agencies)} hiring agencies")

                # Check for consistency
                company_names = {company["name"] for company in companies}
                agency_company_names = {
                    agency["company_name"]
                    for agency in agencies
                    if agency.get("company_name")
                }

                print(f"📊 Company names in companies table: {company_names}")
                print(f"📊 Company names in hiring agencies: {agency_company_names}")

                # Check if all agency company names exist in companies table
                missing_companies = agency_company_names - company_names
                if missing_companies:
                    print(f"❌ Missing companies: {missing_companies}")
                    return False
                else:
                    print("✅ All hiring agency companies exist in companies table")
                    return True
            else:
                print(
                    f"❌ Failed to fetch hiring agencies: {agencies_response.status_code}"
                )
                return False
        else:
            print(f"❌ Failed to fetch companies: {companies_response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error during company data integrity check: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Starting Hiring Agency Company Relationship Tests")
    print("=" * 60)

    # Get admin token
    token = get_admin_token()
    if not token:
        print("❌ Cannot proceed without admin token")
        return

    print(f"✅ Admin token obtained: {token[:20]}...")

    # Test 1: Check existing hiring agencies have company relationships
    relationship_working = test_get_all_hiring_agencies_with_company_relationship(token)

    # Test 2: Create new hiring agency and verify company relationship
    created_agency = test_create_hiring_agency_with_company_relationship(token)

    # Test 3: Check data integrity between companies and hiring agencies
    data_integrity = test_company_data_integrity(token)

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    if relationship_working:
        print("✅ Company relationship working in existing hiring agencies: PASSED")
    else:
        print("❌ Company relationship working in existing hiring agencies: FAILED")

    if created_agency:
        print("✅ Company relationship working in new hiring agencies: PASSED")
    else:
        print("❌ Company relationship working in new hiring agencies: FAILED")

    if data_integrity:
        print("✅ Company data integrity: PASSED")
    else:
        print("❌ Company data integrity: FAILED")

    print("\n🎉 Testing completed!")


if __name__ == "__main__":
    main()
