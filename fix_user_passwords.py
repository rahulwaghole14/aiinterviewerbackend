#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from authapp.models import CustomUser


def fix_user_passwords():
    """Fix passwords for existing users so they can login"""

    print("🔧 Fixing User Passwords")
    print("=" * 50)

    # Get all users
    users = CustomUser.objects.all()
    print(f"Total users found: {users.count()}")

    # Common password to set for all users
    common_password = "password123"

    fixed_count = 0

    for user in users:
        print(f"\n👤 Processing user: {user.email}")
        print(f"   - Role: {user.role}")
        print(f"   - Company: {user.company_name}")

        # Check if user can authenticate with common password
        if user.check_password(common_password):
            print(f"   - ✅ Already has correct password")
            continue

        # Set the password
        try:
            user.set_password(common_password)
            user.save()
            print(f"   - ✅ Password fixed")
            fixed_count += 1
        except Exception as e:
            print(f"   - ❌ Failed to fix password: {e}")

    print(f"\n✅ Fixed passwords for {fixed_count} users")
    print(f"📝 All users now have password: {common_password}")


def create_test_users():
    """Create fresh test users with known passwords"""

    print("\n🔧 Creating Fresh Test Users")
    print("=" * 50)

    # Test users to create
    test_users = [
        {
            "email": "company_test@example.com",
            "password": "password123",
            "full_name": "Company Test User",
            "company_name": "Test Company",
            "role": "COMPANY",
        },
        {
            "email": "agency_test@example.com",
            "password": "password123",
            "full_name": "Agency Test User",
            "company_name": "Test Agency",
            "role": "HIRING_AGENCY",
        },
        {
            "email": "recruiter_test@example.com",
            "password": "password123",
            "full_name": "Recruiter Test User",
            "company_name": "Test Company",
            "role": "RECRUITER",
        },
    ]

    created_count = 0

    for user_data in test_users:
        # Check if user already exists
        try:
            existing_user = CustomUser.objects.get(email=user_data["email"])
            print(f"👤 User {user_data['email']} already exists, updating password...")
            existing_user.set_password(user_data["password"])
            existing_user.save()
            print(f"   - ✅ Password updated")
            created_count += 1
        except CustomUser.DoesNotExist:
            # Create new user
            try:
                user = CustomUser.objects.create_user(
                    username=user_data["email"],
                    email=user_data["email"],
                    password=user_data["password"],
                    full_name=user_data["full_name"],
                    company_name=user_data["company_name"],
                    role=user_data["role"],
                )
                print(f"👤 Created user: {user.email}")
                print(f"   - Role: {user.role}")
                print(f"   - Company: {user.company_name}")
                created_count += 1
            except Exception as e:
                print(f"❌ Failed to create user {user_data['email']}: {e}")

    print(f"\n✅ Created/Updated {created_count} test users")
    print(f"📝 All test users have password: password123")


def test_login_after_fix():
    """Test login for users after fixing passwords"""

    print("\n🔍 Testing Login After Password Fix")
    print("=" * 50)

    from django.contrib.auth import authenticate
    from rest_framework.authtoken.models import Token

    # Test users
    test_credentials = [
        {"email": "company_test@example.com", "password": "password123"},
        {"email": "agency_test@example.com", "password": "password123"},
        {"email": "recruiter_test@example.com", "password": "password123"},
        {"email": "admin@rslsolution.com", "password": "admin123"},
    ]

    for creds in test_credentials:
        print(f"\n🔐 Testing login for {creds['email']}...")

        # Test authentication
        user = authenticate(email=creds["email"], password=creds["password"])
        if user:
            print(f"✅ Authentication successful")
            print(f"   - User: {user.full_name}")
            print(f"   - Role: {user.role}")
            print(f"   - Company: {user.company_name}")

            # Test token creation
            try:
                token, created = Token.objects.get_or_create(user=user)
                print(f"   - Token: {token.key[:10]}...")
            except Exception as e:
                print(f"   - ❌ Token creation failed: {e}")
        else:
            print(f"❌ Authentication failed")


if __name__ == "__main__":
    print("🚀 Starting User Password Fix Process")
    print("=" * 60)

    # Fix existing user passwords
    fix_user_passwords()

    # Create fresh test users
    create_test_users()

    # Test login after fixes
    test_login_after_fix()

    print("\n✅ Password fix process completed!")
    print("\n📋 Login Credentials Summary:")
    print("=" * 40)
    print("Admin: admin@rslsolution.com / admin123")
    print("Company: company_test@example.com / password123")
    print("Agency: agency_test@example.com / password123")
    print("Recruiter: recruiter_test@example.com / password123")
    print("\n💡 All other users now have password: password123")
