#!/usr/bin/env python
"""
Script to create an admin user for testing
Run this with: python create_admin_user.py
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from authapp.models import CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()


def create_admin_user():
    """Create an admin user if it doesn't exist"""
    email = "admin@rslsolution.com"
    password = "admin123"

    try:
        # Check if user already exists
        user = User.objects.get(email=email)
        print(f"✅ User {email} already exists")
        print(f"   ID: {user.id}")
        print(f"   Role: {user.role}")
        print(f"   Is active: {user.is_active}")
        return user
    except User.DoesNotExist:
        # Create new admin user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            full_name="Admin User",
            role="ADMIN",
            company_name="RSL Solutions",
            is_active=True,
        )
        print(f"✅ Created admin user: {email}")
        print(f"   ID: {user.id}")
        print(f"   Role: {user.role}")
        return user


def list_users():
    """List all users in the database"""
    users = User.objects.all()
    print(f"\n📋 Total users in database: {users.count()}")
    for user in users:
        print(f"   - {user.email} (Role: {user.role}, Active: {user.is_active})")


if __name__ == "__main__":
    print("🔧 Creating admin user for testing...")
    create_admin_user()
    list_users()
    print("\n✅ Done! You can now test login with:")
    print("   Email: admin@rslsolution.com")
    print("   Password: admin123")
