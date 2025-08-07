#!/usr/bin/env python3
"""
Simple test to check if company registration creates Company model entries
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_company_registration():
    """Test if company registration creates Company model entries"""
    print("🔍 Testing Company Registration Fix")
    print("=" * 50)
    
    # Test data
    test_company = {
        'email': 'test_company_fix@example.com',
        'password': 'password123',
        'full_name': 'Test Company Fix User',
        'company_name': 'Test Company Fix',
        'role': 'COMPANY'
    }
    
    print(f"📝 Registering company: {test_company['company_name']}")
    
    try:
        # Register the company
        response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=test_company,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Registration Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Registration successful!")
            print(f"   - User ID: {data['user']['id']}")
            print(f"   - Company: {data['user']['company_name']}")
            
            # Now check if the company appears in the companies API
            print(f"\n🔍 Checking if company appears in /api/companies/")
            
            # Create admin user to access companies API
            admin_data = {
                'email': 'admin_check@example.com',
                'password': 'adminpass123',
                'full_name': 'Admin Check User',
                'company_name': 'Admin Company',
                'role': 'ADMIN'
            }
            
            admin_response = requests.post(
                f"{BASE_URL}/api/auth/register/",
                json=admin_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if admin_response.status_code == 201:
                admin_token = admin_response.json()['token']
                
                # Get all companies
                companies_response = requests.get(
                    f"{BASE_URL}/api/companies/",
                    headers={'Authorization': f'Token {admin_token}'}
                )
                
                print(f"   Companies API Status: {companies_response.status_code}")
                
                if companies_response.status_code == 200:
                    companies = companies_response.json()
                    company_names = [comp.get('name') for comp in companies]
                    
                    print(f"   📊 Total companies: {len(companies)}")
                    print(f"   🔍 Looking for: {test_company['company_name']}")
                    
                    if test_company['company_name'] in company_names:
                        print(f"   ✅ SUCCESS: Company found in API!")
                        return True
                    else:
                        print(f"   ❌ FAILED: Company not found in API")
                        print(f"   Available companies: {company_names}")
                        return False
                else:
                    print(f"   ❌ Failed to get companies: {companies_response.text}")
                    return False
            else:
                print(f"   ❌ Failed to create admin user: {admin_response.text}")
                return False
        else:
            print(f"   ❌ Registration failed: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection Error: Make sure the server is running on {BASE_URL}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    import time
    time.sleep(3)  # Wait for server to start
    success = test_company_registration()
    
    if success:
        print("\n🎉 SUCCESS: Company registration fix is working!")
    else:
        print("\n❌ FAILED: Company registration fix is not working!")
