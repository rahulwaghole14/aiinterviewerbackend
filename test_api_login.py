#!/usr/bin/env python
import requests
import json

def test_api_login():
    """Test the API login endpoint with different user types"""
    
    base_url = "http://localhost:8000"
    login_url = f"{base_url}/api/auth/login/"
    
    print("🔍 Testing API Login Endpoint")
    print("=" * 50)
    
    # Test credentials
    test_users = [
        {
            'email': 'company_test@example.com',
            'password': 'password123',
            'role': 'COMPANY'
        },
        {
            'email': 'agency_test@example.com',
            'password': 'password123',
            'role': 'HIRING_AGENCY'
        },
        {
            'email': 'recruiter_test@example.com',
            'password': 'password123',
            'role': 'RECRUITER'
        },
        {
            'email': 'admin@rslsolution.com',
            'password': 'admin123',
            'role': 'ADMIN'
        }
    ]
    
    for user_data in test_users:
        print(f"\n🔐 Testing login for {user_data['role']} user...")
        print(f"   Email: {user_data['email']}")
        
        try:
            # Make login request
            response = requests.post(
                login_url,
                json={
                    'email': user_data['email'],
                    'password': user_data['password']
                },
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Login successful!")
                print(f"   - Token: {data['token'][:10]}...")
                print(f"   - User: {data['user']['full_name']}")
                print(f"   - Role: {data['user']['role']}")
                print(f"   - Company: {data['user']['company_name']}")
                
                # Test using the token for a protected endpoint
                test_protected_endpoint(data['token'], user_data['role'])
                
            elif response.status_code == 400:
                print(f"   ❌ Bad Request: {response.text}")
            elif response.status_code == 401:
                print(f"   ❌ Unauthorized: {response.text}")
            else:
                print(f"   ❌ Unexpected status: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection Error: Make sure the server is running on {base_url}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_protected_endpoint(token, user_role):
    """Test accessing a protected endpoint with the token"""
    
    base_url = "http://localhost:8000"
    
    # Test different endpoints based on user role
    endpoints = [
        '/api/candidates/',
        '/api/jobs/',
        '/api/resumes/',
        '/api/interviews/'
    ]
    
    print(f"   🔒 Testing protected endpoints...")
    
    for endpoint in endpoints:
        try:
            response = requests.get(
                f"{base_url}{endpoint}",
                headers={
                    'Authorization': f'Token {token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                print(f"   ✅ {endpoint} - Access granted")
            elif response.status_code == 403:
                print(f"   ⚠️  {endpoint} - Access forbidden (expected for some roles)")
            else:
                print(f"   ❌ {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {str(e)}")

def test_user_registration():
    """Test user registration endpoint"""
    
    base_url = "http://localhost:8000"
    register_url = f"{base_url}/api/auth/register/"
    
    print(f"\n🔍 Testing User Registration")
    print("=" * 50)
    
    # Test registration data
    test_registration = {
        'email': 'new_company@example.com',
        'password': 'password123',
        'full_name': 'New Company User',
        'company_name': 'New Company',
        'role': 'COMPANY'
    }
    
    print(f"📝 Testing registration for: {test_registration['email']}")
    
    try:
        response = requests.post(
            register_url,
            json=test_registration,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Registration successful!")
            print(f"   - Token: {data['token'][:10]}...")
            print(f"   - User: {data['user']['full_name']}")
            print(f"   - Role: {data['user']['role']}")
        else:
            print(f"   ❌ Registration failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection Error: Make sure the server is running on {base_url}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting API Login Tests")
    print("=" * 60)
    
    # Test API login
    test_api_login()
    
    # Test user registration
    test_user_registration()
    
    print("\n✅ API tests completed!")
    print("\n📋 Working Login Credentials:")
    print("=" * 40)
    print("Company: company_test@example.com / password123")
    print("Agency: agency_test@example.com / password123")
    print("Recruiter: recruiter_test@example.com / password123")
    print("Admin: admin@rslsolution.com / admin123") 