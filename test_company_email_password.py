#!/usr/bin/env python3
"""
Test script to verify company creation with email/password and get all companies API
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

def test_create_company_with_email_password(token):
    """Test creating a company with email and password"""
    print("\n🔧 Testing Company Creation with Email and Password")
    print("=" * 50)
    
    try:
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        
        # Test data for company creation
        company_data = {
            "name": "Test Company with Email",
            "email": "testcompany@example.com",
            "password": "company123",
            "description": "A test company with email and password"
        }
        
        print(f"📤 Creating company with data: {json.dumps(company_data, indent=2)}")
        
        response = requests.post(f"{BASE_URL}/api/companies/", json=company_data, headers=headers)
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Company created successfully with email and password")
            return response.json()
        else:
            print("❌ Company creation failed")
            return None
            
    except Exception as e:
        print(f"❌ Error during company creation: {e}")
        return None

def test_get_all_companies_returns_email(token):
    """Test that get all companies API returns email field"""
    print("\n🔧 Testing Get All Companies API Returns Email")
    print("=" * 50)
    
    try:
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        
        print("📤 Fetching all companies...")
        
        response = requests.get(f"{BASE_URL}/api/companies/", headers=headers)
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            companies = response.json()
            print(f"📥 Found {len(companies)} companies")
            
            # Check if email field is present in response
            email_found = False
            for company in companies:
                if 'email' in company:
                    email_found = True
                    print(f"✅ Company '{company['name']}' has email: {company['email']}")
                else:
                    print(f"❌ Company '{company['name']}' missing email field")
            
            if email_found:
                print("✅ Email field is returned in get all companies API")
                return True
            else:
                print("❌ No companies have email field")
                return False
        else:
            print(f"❌ Failed to fetch companies: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during get all companies: {e}")
        return False

def test_create_company_without_email_password(token):
    """Test creating a company without email and password (backward compatibility)"""
    print("\n🔧 Testing Company Creation without Email and Password")
    print("=" * 50)
    
    try:
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        
        # Test data for company creation without email/password
        company_data = {
            "name": "Test Company without Email",
            "description": "A test company without email and password"
        }
        
        print(f"📤 Creating company with data: {json.dumps(company_data, indent=2)}")
        
        response = requests.post(f"{BASE_URL}/api/companies/", json=company_data, headers=headers)
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Company created successfully without email and password")
            return response.json()
        else:
            print("❌ Company creation failed")
            return None
            
    except Exception as e:
        print(f"❌ Error during company creation: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 Starting Company Email/Password API Tests")
    print("=" * 60)
    
    # Get admin token
    token = get_admin_token()
    if not token:
        print("❌ Cannot proceed without admin token")
        return
    
    print(f"✅ Admin token obtained: {token[:20]}...")
    
    # Test 1: Create company with email and password
    created_company = test_create_company_with_email_password(token)
    
    # Test 2: Get all companies and verify email is returned
    email_returned = test_get_all_companies_returns_email(token)
    
    # Test 3: Create company without email and password (backward compatibility)
    created_company_simple = test_create_company_without_email_password(token)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if created_company:
        print("✅ Company creation with email/password: PASSED")
    else:
        print("❌ Company creation with email/password: FAILED")
    
    if email_returned:
        print("✅ Get all companies returns email: PASSED")
    else:
        print("❌ Get all companies returns email: FAILED")
    
    if created_company_simple:
        print("✅ Company creation without email/password: PASSED")
    else:
        print("❌ Company creation without email/password: FAILED")
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    main()
