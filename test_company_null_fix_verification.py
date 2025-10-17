import requests
import json

BASE_URL = "http://localhost:8000"


def get_admin_token():
    """Get admin authentication token"""
    login_data = {"email": "admin@rslsolution.com", "password": "admin123"}

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
        if response.status_code == 200:
            return response.json().get("token")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")
        return None


def test_company_null_fix():
    """Test that the company null issue has been fixed"""
    print("🔧 Testing Company Null Issue Fix")
    print("=" * 50)

    # Get admin token
    token = get_admin_token()
    if not token:
        print("❌ Failed to get admin token")
        return

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    try:
        # Get all hiring agencies
        response = requests.get(f"{BASE_URL}/api/hiring_agency/", headers=headers)
        print(f"📊 API Response Status: {response.status_code}")

        if response.status_code == 200:
            hiring_agencies = response.json()
            print(f"📋 Total hiring agencies found: {len(hiring_agencies)}")
            print()

            # Count agencies with different company states
            agencies_with_company_id = []
            agencies_with_null_company = []
            agencies_with_no_company = []

            for agency in hiring_agencies:
                company_id = agency.get("company")
                company_name = agency.get("company_name")

                if company_id is not None:
                    agencies_with_company_id.append(agency)
                elif company_name and company_name != "No Company":
                    agencies_with_null_company.append(agency)
                else:
                    agencies_with_no_company.append(agency)

            print("📊 ANALYSIS RESULTS:")
            print(f"   ✅ Agencies with company ID: {len(agencies_with_company_id)}")
            print(
                f"   ⚠️  Agencies with null company but company_name: {len(agencies_with_null_company)}"
            )
            print(
                f"   ℹ️  Agencies with no company (No Company): {len(agencies_with_no_company)}"
            )
            print()

            # Check if the fix worked
            if len(agencies_with_null_company) == 0:
                print(
                    "🎉 SUCCESS: All agencies with company_name now have proper company IDs!"
                )
                print("✅ The company null issue has been completely resolved.")
            else:
                print(
                    "⚠️  PARTIAL SUCCESS: Some agencies still have null company fields."
                )
                print("📝 Remaining issues:")
                for agency in agencies_with_null_company:
                    print(
                        f"   - ID {agency.get('id')}: {agency.get('email')} (company_name: {agency.get('company_name')})"
                    )

            print()

            # Show examples of fixed agencies
            if agencies_with_company_id:
                print("✅ EXAMPLES OF PROPERLY LINKED AGENCIES:")
                for agency in agencies_with_company_id[:3]:  # Show first 3
                    print(f"   - ID {agency.get('id')}: {agency.get('email')}")
                    print(
                        f"     Company ID: {agency.get('company')} | Company Name: {agency.get('company_name')}"
                    )
                    print()

            # Show agencies with no company (expected behavior)
            if agencies_with_no_company:
                print("ℹ️  AGENCIES WITH NO COMPANY (Expected):")
                for agency in agencies_with_no_company:
                    print(f"   - ID {agency.get('id')}: {agency.get('email')}")
                    print(
                        f"     Company ID: {agency.get('company')} | Company Name: {agency.get('company_name')}"
                    )
                    print()

        else:
            print(f"❌ Failed to retrieve hiring agencies: {response.text}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_api_response_format():
    """Test that the API response format is correct"""
    print("\n🔍 Testing API Response Format")
    print("=" * 40)

    token = get_admin_token()
    if not token:
        return

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    try:
        response = requests.get(f"{BASE_URL}/api/hiring_agency/", headers=headers)
        if response.status_code == 200:
            hiring_agencies = response.json()

            if hiring_agencies:
                # Check the first agency's response format
                first_agency = hiring_agencies[0]
                print("📋 API Response Format Check:")
                print(f"   ✅ Has 'company' field: {'company' in first_agency}")
                print(
                    f"   ✅ Has 'company_name' field: {'company_name' in first_agency}"
                )
                print(f"   ✅ Company field type: {type(first_agency.get('company'))}")
                print(
                    f"   ✅ Company name field type: {type(first_agency.get('company_name'))}"
                )

                # Show sample response
                print("\n📄 Sample API Response:")
                sample_fields = [
                    "id",
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "company",
                    "company_name",
                ]
                sample_data = {
                    field: first_agency.get(field) for field in sample_fields
                }
                print(json.dumps(sample_data, indent=2))
            else:
                print("ℹ️  No hiring agencies found to test response format")
        else:
            print(f"❌ Failed to get hiring agencies: {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    test_company_null_fix()
    test_api_response_format()
