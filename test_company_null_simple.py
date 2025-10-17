#!/usr/bin/env python3
import requests
import json


def test_company_null_fix():
    """Simple test to verify the company null fix is working"""
    print("🔍 Testing Company Null Fix with Simple Request")
    print("=" * 50)

    BASE_URL = "http://localhost:8000"

    # Test data
    login_data = {"email": "admin@rslsolution.com", "password": "admin123"}

    try:
        # Step 1: Login
        print("1. Logging in...")
        response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return

        token = response.json().get("token")
        headers = {"Authorization": f"Token {token}"}
        print("✅ Login successful")

        # Step 2: Get hiring agencies
        print("\n2. Getting hiring agencies...")
        response = requests.get(f"{BASE_URL}/api/hiring_agency/", headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to get hiring agencies: {response.status_code}")
            return

        agencies = response.json()
        print(f"✅ Found {len(agencies)} hiring agencies")

        # Step 3: Analyze company fields
        print("\n3. Analyzing company fields...")
        null_count = 0
        valid_count = 0

        for agency in agencies:
            company_id = agency.get("company")
            company_name = agency.get("company_name")

            if company_id is not None:
                valid_count += 1
                print(
                    f"   ✅ ID {agency.get('id')}: company={company_id}, name='{company_name}'"
                )
            elif company_name and company_name != "No Company":
                null_count += 1
                print(
                    f"   ⚠️  ID {agency.get('id')}: company=null, name='{company_name}' (ISSUE)"
                )
            else:
                print(
                    f"   ℹ️  ID {agency.get('id')}: company=null, name='{company_name}' (expected)"
                )

        # Step 4: Summary
        print(f"\n📊 SUMMARY:")
        print(f"   Total agencies: {len(agencies)}")
        print(f"   Valid company IDs: {valid_count}")
        print(f"   Null company issues: {null_count}")

        if null_count == 0:
            print("🎉 SUCCESS: No company null issues found!")
            print("✅ The fix is working correctly.")
        else:
            print(f"⚠️  Found {null_count} agencies with company null issues.")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_company_null_fix()
