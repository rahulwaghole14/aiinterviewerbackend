import requests
import json

BASE_URL = "http://localhost:8000"

def get_admin_token():
    """Get admin authentication token"""
    login_data = {
        "email": "admin@rslsolution.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
        if response.status_code == 200:
            return response.json().get('token')
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")
        return None

def test_hiring_agencies_company_field():
    """Test the Get All Hiring Agencies API to check company field values"""
    print("🔍 Investigating Company Field Null Issue in Hiring Agencies API")
    print("=" * 70)
    
    # Get admin token
    token = get_admin_token()
    if not token:
        print("❌ Failed to get admin token")
        return
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get all hiring agencies
        response = requests.get(f"{BASE_URL}/api/hiring_agency/", headers=headers)
        print(f"📊 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            hiring_agencies = response.json()
            print(f"📋 Total hiring agencies found: {len(hiring_agencies)}")
            print()
            
            # Analyze each hiring agency
            for i, agency in enumerate(hiring_agencies, 1):
                print(f"🏢 Hiring Agency {i}:")
                print(f"   ID: {agency.get('id')}")
                print(f"   Email: {agency.get('email')}")
                print(f"   Name: {agency.get('first_name')} {agency.get('last_name')}")
                print(f"   Role: {agency.get('role')}")
                print(f"   Company (FK): {agency.get('company')}")
                print(f"   Company Name (text): {agency.get('company_name')}")
                print(f"   Created By: {agency.get('created_by')}")
                print()
                
                # Check if company is null but company_name exists
                if agency.get('company') is None and agency.get('company_name'):
                    print(f"   ⚠️  ISSUE DETECTED: company FK is null but company_name exists!")
                    print(f"   📝 This suggests the ForeignKey relationship wasn't properly set during migration or creation.")
                    print()
                elif agency.get('company') is None and not agency.get('company_name'):
                    print(f"   ℹ️  No company assigned (both FK and text field are empty)")
                    print()
                else:
                    print(f"   ✅ Company relationship properly set")
                    print()
            
            # Summary
            print("📊 SUMMARY:")
            agencies_with_null_company = [a for a in hiring_agencies if a.get('company') is None]
            agencies_with_company = [a for a in hiring_agencies if a.get('company') is not None]
            
            print(f"   Total agencies: {len(hiring_agencies)}")
            print(f"   Agencies with null company FK: {len(agencies_with_null_company)}")
            print(f"   Agencies with company FK: {len(agencies_with_company)}")
            
            if agencies_with_null_company:
                print(f"   ⚠️  {len(agencies_with_null_company)} agencies have null company field!")
                
        else:
            print(f"❌ Failed to retrieve hiring agencies: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_company_data():
    """Test the companies API to see what companies exist"""
    print("\n🏢 Checking Available Companies")
    print("=" * 40)
    
    token = get_admin_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/companies/", headers=headers)
        if response.status_code == 200:
            companies = response.json()
            print(f"📋 Total companies in database: {len(companies)}")
            
            for company in companies:
                print(f"   ID: {company.get('id')} | Name: {company.get('name')} | Email: {company.get('email')}")
        else:
            print(f"❌ Failed to get companies: {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_hiring_agencies_company_field()
    test_company_data()
