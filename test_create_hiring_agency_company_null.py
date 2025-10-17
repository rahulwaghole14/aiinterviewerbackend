import requests
import json
import time

BASE_URL = "http://localhost:8000"


def get_admin_token():
    """Get admin authentication token"""
    print("🔐 Attempting to get admin token...")
    login_data = {"email": "admin@rslsolution.com", "password": "admin123"}

    try:
        print(f"📡 Making request to {BASE_URL}/api/auth/login/")
        response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response text: {response.text}")

        if response.status_code == 200:
            token = response.json().get("token")
            print(
                f"✅ Token received: {token[:10]}..."
                if token
                else "❌ No token in response"
            )
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")
        return None


def create_hiring_agency_with_company():
    """Create a hiring agency with a company name to test the fix"""
    print("🏢 Testing Company Null Issue with New Hiring Agency Creation")
    print("=" * 60)

    # Get admin token
    token = get_admin_token()
    if not token:
        print("❌ Failed to get admin token")
        return None

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    # Create a unique email for testing
    timestamp = int(time.time())
    test_email = f"test_agency_{timestamp}@example.com"

    # Test data for hiring agency creation
    hiring_agency_data = {
        "first_name": "Test",
        "last_name": "Agency",
        "email": test_email,
        "password": "test123",
        "phone_number": "+1234567890",
        "role": "Hiring Agency",
        "input_company_name": "Test Company",  # This should be resolved to company ID
        "linkedin_url": "https://linkedin.com/in/testagency",
    }

    print(f"📝 Creating hiring agency with email: {test_email}")
    print(f"🏢 Company name: {hiring_agency_data['input_company_name']}")
    print(f"📡 Making request to {BASE_URL}/api/hiring_agency/add_user/")
    print()

    try:
        # Create the hiring agency
        response = requests.post(
            f"{BASE_URL}/api/hiring_agency/add_user/",
            json=hiring_agency_data,
            headers=headers,
        )

        print(f"📊 Creation Response Status: {response.status_code}")
        print(f"📄 Response text: {response.text}")

        if response.status_code == 201:
            created_agency = response.json()
            print("✅ Hiring agency created successfully!")
            print(f"   ID: {created_agency.get('id')}")
            print(f"   Email: {created_agency.get('email')}")
            print(f"   Company (FK): {created_agency.get('company')}")
            print(f"   Company Name: {created_agency.get('company_name')}")
            print()

            # Check if company field is properly set
            if created_agency.get("company") is not None:
                print("🎉 SUCCESS: Company field is properly set!")
                print(f"   Company ID: {created_agency.get('company')}")
                print(f"   Company Name: {created_agency.get('company_name')}")
            else:
                print("⚠️  ISSUE: Company field is null!")
                print("   This indicates the fix might not be working for new records.")

            return created_agency

        else:
            print(f"❌ Failed to create hiring agency: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def verify_created_agency_in_list(agency_id):
    """Verify the created agency appears correctly in the list API"""
    print("\n🔍 Verifying Created Agency in List API")
    print("=" * 45)

    token = get_admin_token()
    if not token:
        print("❌ Failed to get admin token")
        return

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    try:
        print(f"📡 Making request to {BASE_URL}/api/hiring_agency/")
        # Get all hiring agencies
        response = requests.get(f"{BASE_URL}/api/hiring_agency/", headers=headers)
        print(f"📊 List Response Status: {response.status_code}")

        if response.status_code == 200:
            hiring_agencies = response.json()
            print(f"📋 Found {len(hiring_agencies)} hiring agencies")

            # Find the created agency
            created_agency = None
            for agency in hiring_agencies:
                if agency.get("id") == agency_id:
                    created_agency = agency
                    break

            if created_agency:
                print("✅ Found created agency in list API!")
                print(f"   ID: {created_agency.get('id')}")
                print(f"   Email: {created_agency.get('email')}")
                print(f"   Company (FK): {created_agency.get('company')}")
                print(f"   Company Name: {created_agency.get('company_name')}")
                print()

                # Check if company field is properly set
                if created_agency.get("company") is not None:
                    print("🎉 SUCCESS: Company field is properly resolved in list API!")
                    print("✅ The fix is working correctly for new records.")
                else:
                    print("⚠️  ISSUE: Company field is still null in list API!")
                    print("   This indicates the fix might not be working properly.")
            else:
                print("❌ Created agency not found in list API")
        else:
            print(f"❌ Failed to get hiring agencies: {response.text}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_company_resolution():
    """Test if the company resolution logic is working"""
    print("\n🔧 Testing Company Resolution Logic")
    print("=" * 40)

    token = get_admin_token()
    if not token:
        print("❌ Failed to get admin token")
        return

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    try:
        print(f"📡 Making request to {BASE_URL}/api/companies/")
        # First, check what companies exist
        companies_response = requests.get(f"{BASE_URL}/api/companies/", headers=headers)
        print(f"📊 Companies Response Status: {companies_response.status_code}")

        if companies_response.status_code == 200:
            companies = companies_response.json()
            print(f"📋 Found {len(companies)} companies")
            test_company = None

            # Find "Test Company"
            for company in companies:
                if company.get("name") == "Test Company":
                    test_company = company
                    break

            if test_company:
                print(f"✅ Found 'Test Company' with ID: {test_company.get('id')}")
                print(
                    f"   This should be the company ID returned for new hiring agencies."
                )
            else:
                print("⚠️  'Test Company' not found in companies list")
                print("   This might explain why company field is null.")
        else:
            print(f"❌ Failed to get companies: {companies_response.text}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


def cleanup_test_agency(agency_id):
    """Clean up the test agency"""
    print(f"\n🧹 Cleaning up test agency (ID: {agency_id})")
    print("=" * 40)

    token = get_admin_token()
    if not token:
        print("❌ Failed to get admin token")
        return

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    try:
        response = requests.delete(
            f"{BASE_URL}/api/hiring_agency/{agency_id}/", headers=headers
        )

        if response.status_code == 204:
            print("✅ Test agency deleted successfully")
        else:
            print(f"⚠️  Failed to delete test agency: {response.status_code}")

    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting test...")
    print(f"🌐 Base URL: {BASE_URL}")
    print()

    # Test company resolution logic first
    test_company_resolution()

    # Create a new hiring agency
    created_agency = create_hiring_agency_with_company()

    if created_agency:
        agency_id = created_agency.get("id")

        # Verify the created agency in the list API
        verify_created_agency_in_list(agency_id)

        # Clean up the test agency
        cleanup_test_agency(agency_id)

    print("\n�� Test completed!")
