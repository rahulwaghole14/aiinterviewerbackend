#!/usr/bin/env python
"""
Test login endpoint directly from backend
"""

import os
import sys
import django
import requests
import json

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from authapp.models import CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()


def test_login_direct():
    """Test login directly using Django"""
    email = "admin@rslsolution.com"
    password = "admin123"

    try:
        # Check if user exists
        user = User.objects.get(email=email)
        print(f"✅ User found: {user.email}")
        print(f"   Role: {user.role}")
        print(f"   Is active: {user.is_active}")
        print(f"   Username: {user.username}")

        # Test authentication
        from django.contrib.auth import authenticate

        authenticated_user = authenticate(username=email, password=password)

        if authenticated_user:
            print("✅ Authentication successful!")
            print(f"   Authenticated user: {authenticated_user.email}")
        else:
            print("❌ Authentication failed!")

            # Check if password is correct
            if user.check_password(password):
                print("✅ Password is correct")
            else:
                print("❌ Password is incorrect")

    except User.DoesNotExist:
        print(f"❌ User {email} not found")


def test_login_api():
    """Test login via API"""
    url = "http://localhost:8000/api/auth/login/"
    data = {"email": "admin@rslsolution.com", "password": "admin123"}

    try:
        response = requests.post(url, json=data)
        print(f"API Response Status: {response.status_code}")
        print(f"API Response Headers: {dict(response.headers)}")
        print(f"API Response Content: {response.text}")

        if response.status_code == 200:
            result = response.json()
            print("✅ API Login successful!")
            print(f"Token: {result.get('token', 'No token')}")
        else:
            print("❌ API Login failed!")

    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")


if __name__ == "__main__":
    print("🔍 Testing login directly...")
    test_login_direct()

    print("\n🔍 Testing login via API...")
    test_login_api()
