#!/usr/bin/env python
"""
Fix login by creating admin user and testing API
"""
import os
import django
import requests
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
django.setup()

from django.contrib.auth import get_user_model

def create_admin_user():
    """Create admin user with specified credentials"""
    User = get_user_model()
    email = "admin@example.com"
    password = "admin@123"
    
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": email,
            "full_name": "Admin User",
            "role": "ADMIN",
            "is_active": True,
        }
    )
    
    if not created:
        user.username = email
        user.full_name = user.full_name or "Admin User"
        user.role = "ADMIN"
        user.is_active = True
    
    user.set_password(password)
    user.save()
    
    print(f"✅ {'Created' if created else 'Updated'} admin user: {email}")
    return user

def test_login_api():
    """Test login API with the credentials"""
    url = "http://127.0.0.1:8000/api/auth/login/"
    data = {
        "email": "admin@example.com",
        "password": "admin@123"
    }
    
    try:
        response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        print(f"Login API Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            print(f"Token: {result.get('token', 'N/A')[:20]}...")
            print(f"User: {result.get('user', {}).get('email', 'N/A')}")
        else:
            print("❌ Login failed")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    print("🔧 Creating admin user and testing login...")
    create_admin_user()
    test_login_api()
    print("✅ Done!")
