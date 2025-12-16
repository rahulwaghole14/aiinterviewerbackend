#!/usr/bin/env python
"""
Script to verify and create admin user if needed.
Run this on Render via shell to check if admin user exists.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from authapp.models import Role

User = get_user_model()

def verify_or_create_admin():
    admin_email = "admin@rslsolution.com"
    admin_password = "admin123456"
    admin_full_name = "Admin User"
    
    print("=" * 60)
    print("🔍 Checking for admin user...")
    print("=" * 60)
    
    # Check if user exists
    user = User.objects.filter(email=admin_email).first()
    
    if user:
        print(f"✅ Admin user found: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Full Name: {user.full_name}")
        print(f"   Role: {user.role}")
        print(f"   Is Superuser: {user.is_superuser}")
        print(f"   Is Staff: {user.is_staff}")
        print(f"   Is Active: {user.is_active}")
        
        # Test password
        if user.check_password(admin_password):
            print(f"✅ Password is correct!")
        else:
            print(f"⚠️  Password is incorrect. Updating password...")
            user.password = make_password(admin_password)
            user.save()
            print(f"✅ Password updated!")
        
        return user
    else:
        print(f"❌ Admin user not found. Creating...")
        
        # Create admin user
        username = admin_email
        if User.objects.filter(username=username).exists():
            username = f"{admin_email}_{User.objects.count()}"
        
        user = User.objects.create(
            username=username,
            email=admin_email,
            full_name=admin_full_name,
            role="ADMIN",
            password=make_password(admin_password),
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {user.email}")
        print(f"   Password: {admin_password}")
        print(f"   Role: {user.role}")
        
        return user

if __name__ == "__main__":
    try:
        verify_or_create_admin()
        print("\n" + "=" * 60)
        print("✅ Verification complete!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



