#!/usr/bin/env python3
"""
Test script to verify register company endpoint functionality and 
check if registered companies appear in the all companies API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_register_company_endpoint():
    """Test the register company endpoint functionality"""
    print("🔍 Testing Register Company Endpoint")
    print("=" * 50)
    
    # Test data for company registration
    test_companies = [
        {
            'email': 'test_company1@example.com',
            'password': 'password123',
            'full_name': 'Test Company 1 User',
            'company_name': 'Test Company 1',
            'role': 'COMPANY'
        },
        {
            'email': 'test_company2@example.com',
            'password': 'password123',
            'full_name': 'Test Company 2 User',
            'company_name': 'Test Company 2',
            'role': 'COMPANY'
        }
    ]
    
    registered_companies = []
    
    for i, company_data in enumerate(test_companies, 1):
        print(f"\n📝 Testing Company Registration {i}: {company_data['company_name']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/register/",
                json=company_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"   ✅ Registration successful!")
                print(f"   - User ID: {data['user']['id']}")
                print(f"   - Email: {data['user']['email']}")
                print(f"   - Company: {data['user']['company_name']}")
                print(f"   - Role: {data['user']['role']}")
                print(f"   - Token: {data['token'][:10]}...")
                
                registered_companies.append({
                    'user_data': data['user'],
                    'token': data['token'],
                    'company_name': company_data['company_name']
                })
            else:
                print(f"   ❌ Registration failed: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection Error: Make sure the server is running on {BASE_URL}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    return registered_companies

def test_all_companies_api():
    """Test the all companies API endpoint"""
    print("\n🏢 Testing All Companies API")
    print("=" * 50)
    
    # First, try to get companies without authentication
    print("📤 Testing without authentication...")
    try:
        response = requests.get(f"{BASE_URL}/api/companies/")
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Properly requires authentication")
        else:
            print(f"   ⚠️  Unexpected response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Create an admin user to test with authentication
    print("\n🔧 Creating admin user for testing...")
    admin_data = {
        'email': 'admin_test@example.com',
        'password': 'adminpass123',
        'full_name': 'Admin Test User',
        'company_name': 'Admin Company',
        'role': 'ADMIN'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=admin_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            admin_data = response.json()
            admin_token = admin_data['token']
            print("   ✅ Admin user created successfully")
        else:
            print(f"   ❌ Admin user creation failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error creating admin user: {str(e)}")
        return None
    
    # Test getting all companies with admin authentication
    print("\n📋 Testing All Companies API with admin authentication...")
    headers = {'Authorization': f'Token {admin_token}'}
    
    try:
        response = requests.get(f"{BASE_URL}/api/companies/", headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            companies = response.json()
            print(f"   ✅ Successfully retrieved companies!")
            print(f"   📊 Total companies found: {len(companies)}")
            
            for i, company in enumerate(companies, 1):
                print(f"   {i}. ID: {company.get('id')} | Name: {company.get('name')} | Active: {company.get('is_active')}")
            
            return companies
        else:
            print(f"   ❌ Failed to retrieve companies: {response.text}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return []

def test_company_creation_via_api():
    """Test creating companies via the companies API"""
    print("\n🏗️ Testing Company Creation via API")
    print("=" * 50)
    
    # Create admin user if not exists
    admin_data = {
        'email': 'admin_create@example.com',
        'password': 'adminpass123',
        'full_name': 'Admin Create User',
        'company_name': 'Admin Company',
        'role': 'ADMIN'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=admin_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            admin_data = response.json()
            admin_token = admin_data['token']
            print("   ✅ Admin user created/retrieved successfully")
        else:
            print(f"   ❌ Admin user creation failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error creating admin user: {str(e)}")
        return None
    
    # Test creating a company via API
    headers = {
        'Authorization': f'Token {admin_token}',
        'Content-Type': 'application/json'
    }
    
    new_company_data = {
        'name': 'API Created Company',
        'description': 'This company was created via the API',
        'is_active': True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/companies/",
            json=new_company_data,
            headers=headers
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 201:
            company = response.json()
            print(f"   ✅ Company created successfully via API!")
            print(f"   - ID: {company.get('id')}")
            print(f"   - Name: {company.get('name')}")
            print(f"   - Description: {company.get('description')}")
            print(f"   - Active: {company.get('is_active')}")
            return company
        else:
            print(f"   ❌ Company creation failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def test_company_user_permissions():
    """Test company user permissions for company management"""
    print("\n🔒 Testing Company User Permissions")
    print("=" * 50)
    
    # Create a company user
    company_user_data = {
        'email': 'company_user@example.com',
        'password': 'companypass123',
        'full_name': 'Company User',
        'company_name': 'Test Company User',
        'role': 'COMPANY'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=company_user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            user_data = response.json()
            company_token = user_data['token']
            print("   ✅ Company user created successfully")
        else:
            print(f"   ❌ Company user creation failed: {response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ Error creating company user: {str(e)}")
        return
    
    # Test company user trying to access companies API
    headers = {'Authorization': f'Token {company_token}'}
    
    try:
        response = requests.get(f"{BASE_URL}/api/companies/", headers=headers)
        print(f"   📤 GET /api/companies/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            companies = response.json()
            print(f"   ✅ Company user can list companies")
            print(f"   📊 Companies visible: {len(companies)}")
        else:
            print(f"   ❌ Company user cannot list companies: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test company user trying to create a company
    headers = {
        'Authorization': f'Token {company_token}',
        'Content-Type': 'application/json'
    }
    
    new_company_data = {
        'name': 'Company User Created Company',
        'description': 'This should be blocked for company users',
        'is_active': True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/companies/",
            json=new_company_data,
            headers=headers
        )
        
        print(f"   📤 POST /api/companies/ - Status: {response.status_code}")
        
        if response.status_code == 403:
            print("   ✅ Company user properly blocked from creating companies")
        else:
            print(f"   ⚠️  Unexpected response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

def main():
    """Main test function"""
    print("🚀 Starting Register Company Endpoint Tests")
    print("=" * 60)
    
    # Test 1: Register company endpoint
    registered_companies = test_register_company_endpoint()
    
    # Test 2: All companies API
    all_companies = test_all_companies_api()
    
    # Test 3: Company creation via API
    api_created_company = test_company_creation_via_api()
    
    # Test 4: Company user permissions
    test_company_user_permissions()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    print(f"✅ Companies registered via /api/auth/register/: {len(registered_companies)}")
    print(f"✅ Companies found in /api/companies/: {len(all_companies) if all_companies else 0}")
    print(f"✅ Company created via /api/companies/: {'Yes' if api_created_company else 'No'}")
    
    # Check if registered companies appear in the all companies API
    if registered_companies and all_companies:
        print("\n🔍 Checking if registered companies appear in all companies API...")
        registered_company_names = [comp['company_name'] for comp in registered_companies]
        api_company_names = [comp.get('name') for comp in all_companies]
        
        found_companies = []
        missing_companies = []
        
        for reg_company in registered_company_names:
            if reg_company in api_company_names:
                found_companies.append(reg_company)
            else:
                missing_companies.append(reg_company)
        
        print(f"   ✅ Found in API: {len(found_companies)}")
        for company in found_companies:
            print(f"      - {company}")
        
        print(f"   ❌ Missing from API: {len(missing_companies)}")
        for company in missing_companies:
            print(f"      - {company}")
        
        if missing_companies:
            print("\n⚠️  ISSUE: Some registered companies are not appearing in the all companies API!")
            print("   This suggests the registration process is not creating Company model entries.")
        else:
            print("\n✅ SUCCESS: All registered companies appear in the all companies API!")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    main()
