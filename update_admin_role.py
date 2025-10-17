#!/usr/bin/env python
"""
Script to update admin user role
Run this with: python update_admin_role.py
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


def update_admin_role():
    """Update admin user role to ADMIN"""
    email = "admin@rslsolution.com"

    try:
        user = User.objects.get(email=email)
        print(f"Found user: {user.email}")
        print(f"Current role: {user.role}")

        # Update role to ADMIN
        user.role = "ADMIN"
        user.save()

        print(f"✅ Updated role to: {user.role}")
        return user
    except User.DoesNotExist:
        print(f"❌ User {email} not found")
        return None


if __name__ == "__main__":
    print("🔧 Updating admin user role...")
    update_admin_role()
    print("✅ Done!")
