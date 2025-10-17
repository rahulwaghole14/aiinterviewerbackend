#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from django.contrib.auth import authenticate
from authapp.models import CustomUser, Role
from rest_framework.authtoken.models import Token


def test_user_creation_and_login():
    """Test creating different user types and their login"""

    print("🔍 Testing User Creation and Login")
    print("=" * 50)

    # Test data for different user types
    test_users = [
        {
            "email": "company@test.com",
            "password": "testpass123",
            "full_name": "Company User",
            "company_name": "Test Company",
            "role": "COMPANY",
        },
        {
            "email": "agency@test.com",
            "password": "testpass123",
            "full_name": "Agency User",
            "company_name": "Test Agency",
            "role": "HIRING_AGENCY",
        },
        {
            "email": "recruiter@test.com",
            "password": "testpass123",
            "full_name": "Recruiter User",
            "company_name": "Test Company",
            "role": "RECRUITER",
        },
    ]

    for user_data in test_users:
        print(f"\n📝 Testing {user_data['role']} user...")

        # Check if user already exists
        try:
            existing_user = CustomUser.objects.get(email=user_data["email"])
            print(f"✅ User {user_data['email']} already exists")
            user = existing_user
        except CustomUser.DoesNotExist:
            # Create new user
            try:
                user = CustomUser.objects.create_user(
                    username=user_data["email"],  # Use email as username
                    email=user_data["email"],
                    password=user_data["password"],
                    full_name=user_data["full_name"],
                    company_name=user_data["company_name"],
                    role=user_data["role"],
                )
                print(f"✅ Created user: {user.email} with role: {user.role}")
            except Exception as e:
                print(f"❌ Failed to create user: {e}")
                continue

        # Test authentication
        print(f"🔐 Testing authentication for {user.email}...")

        # Method 1: Using authenticate with email
        auth_user = authenticate(email=user.email, password=user_data["password"])
        if auth_user:
            print(f"✅ Authentication successful with email: {auth_user.email}")
        else:
            print(f"❌ Authentication failed with email")

        # Method 2: Using authenticate with username
        auth_user2 = authenticate(
            username=user.username, password=user_data["password"]
        )
        if auth_user2:
            print(f"✅ Authentication successful with username: {auth_user2.username}")
        else:
            print(f"❌ Authentication failed with username")

        # Method 3: Direct password check
        if user.check_password(user_data["password"]):
            print(f"✅ Password check successful")
        else:
            print(f"❌ Password check failed")

        # Test token creation
        try:
            token, created = Token.objects.get_or_create(user=user)
            print(
                f"✅ Token {'created' if created else 'retrieved'}: {token.key[:10]}..."
            )
        except Exception as e:
            print(f"❌ Token creation failed: {e}")

        # Print user details
        print(f"📋 User details:")
        print(f"   - ID: {user.id}")
        print(f"   - Email: {user.email}")
        print(f"   - Username: {user.username}")
        print(f"   - Full Name: {user.full_name}")
        print(f"   - Role: {user.role}")
        print(f"   - Company: {user.company_name}")
        print(f"   - Is Active: {user.is_active}")
        print(f"   - Is Staff: {user.is_staff}")
        print(f"   - Is Superuser: {user.is_superuser}")


def test_existing_users():
    """Test existing users in the system"""
    print("\n🔍 Testing Existing Users")
    print("=" * 50)

    users = CustomUser.objects.all()
    print(f"Total users in system: {users.count()}")

    for user in users:
        print(f"\n👤 User: {user.email}")
        print(f"   - Role: {user.role}")
        print(f"   - Company: {user.company_name}")
        print(f"   - Active: {user.is_active}")

        # Test authentication for existing users
        if user.check_password("admin123"):  # Common password
            print(f"   - ✅ Can authenticate with 'admin123'")
        elif user.check_password("password123"):  # Another common password
            print(f"   - ✅ Can authenticate with 'password123'")
        else:
            print(f"   - ❌ Cannot authenticate with common passwords")


def test_authentication_backend():
    """Test the authentication backend"""
    print("\n🔍 Testing Authentication Backend")
    print("=" * 50)

    from authapp.backends import EmailBackend

    backend = EmailBackend()

    # Test with a known user
    try:
        user = CustomUser.objects.first()
        if user:
            print(f"Testing with user: {user.email}")

            # Test backend authentication
            auth_user = backend.authenticate(
                None, email=user.email, password="admin123"
            )
            if auth_user:
                print(f"✅ Backend authentication successful")
            else:
                print(f"❌ Backend authentication failed")
        else:
            print("❌ No users found in system")
    except Exception as e:
        print(f"❌ Backend test failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting User Creation and Login Tests")
    print("=" * 60)

    # Test existing users first
    test_existing_users()

    # Test user creation and login
    test_user_creation_and_login()

    # Test authentication backend
    test_authentication_backend()

    print("\n✅ Tests completed!")
