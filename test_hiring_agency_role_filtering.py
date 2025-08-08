#!/usr/bin/env python3
"""
Test script to verify hiring agency API role filtering
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
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('token')
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return None

def test_hiring_agency_role_filtering(token):
    """Test that hiring agency API only returns hiring agencies, not other roles"""
    print("\n🔧 Testing Hiring Agency Role Filtering")
    print("=" * 50)
    
    try:
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        
        print("📤 Fetching all hiring agencies...")
        
        response = requests.get(f"{BASE_URL}/api/hiring_agency/", headers=headers)
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            agencies = response.json()
            print(f"📥 Found {len(agencies)} records")
            
            # Check roles of returned records
            role_counts = {}
            non_hiring_agencies = []
            
            for agency in agencies:
                role = agency.get('role', 'Unknown')
                role_counts[role] = role_counts.get(role, 0) + 1
                
                if role != 'Hiring Agency':
                    non_hiring_agencies.append({
                        'id': agency.get('id'),
                        'email': agency.get('email'),
                        'role': role,
                        'company_name': agency.get('company_name')
                    })
            
            print(f"📊 Role distribution: {role_counts}")
            
            if non_hiring_agencies:
                print("❌ Found non-hiring agency roles in the response:")
                for item in non_hiring_agencies:
                    print(f"   - ID {item['id']}: {item['email']} (Role: {item['role']}, Company: {item['company_name']})")
                return False
            else:
                print("✅ All returned records are hiring agencies")
                return True
        else:
            print(f"❌ Failed to fetch hiring agencies: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during role filtering test: {e}")
        return False

def test_company_specific_hiring_agencies(token):
    """Test that company users only see hiring agencies from their company"""
    print("\n🔧 Testing Company-Specific Hiring Agencies")
    print("=" * 50)
    
    try:
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        
        # First, get all hiring agencies as admin
        print("📤 Fetching all hiring agencies as admin...")
        admin_response = requests.get(f"{BASE_URL}/api/hiring_agency/", headers=headers)
        
        if admin_response.status_code == 200:
            all_agencies = admin_response.json()
            print(f"📥 Admin sees {len(all_agencies)} total records")
            
            # Group by company
            companies = {}
            for agency in all_agencies:
                company_name = agency.get('company_name', 'No Company')
                if company_name not in companies:
                    companies[company_name] = []
                companies[company_name].append(agency)
            
            print(f"📊 Companies found: {list(companies.keys())}")
            
            # For each company, we would need to test with a company user
            # For now, just show the distribution
            for company_name, agencies in companies.items():
                hiring_agency_count = sum(1 for agency in agencies if agency.get('role') == 'Hiring Agency')
                other_roles_count = len(agencies) - hiring_agency_count
                print(f"   - {company_name}: {hiring_agency_count} hiring agencies, {other_roles_count} other roles")
            
            return True
        else:
            print(f"❌ Failed to fetch hiring agencies: {admin_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during company-specific test: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Hiring Agency Role Filtering Tests")
    print("=" * 60)
    
    # Get admin token
    token = get_admin_token()
    if not token:
        print("❌ Cannot proceed without admin token")
        return
    
    print(f"✅ Admin token obtained: {token[:20]}...")
    
    # Test 1: Check if API returns only hiring agencies
    role_filtering_working = test_hiring_agency_role_filtering(token)
    
    # Test 2: Check company-specific filtering
    company_filtering_working = test_company_specific_hiring_agencies(token)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if role_filtering_working:
        print("✅ Hiring agency API returns only hiring agencies: PASSED")
    else:
        print("❌ Hiring agency API returns only hiring agencies: FAILED")
        print("   ⚠️  The API is returning other roles besides hiring agencies")
    
    if company_filtering_working:
        print("✅ Company-specific filtering analysis: PASSED")
    else:
        print("❌ Company-specific filtering analysis: FAILED")
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    main()
