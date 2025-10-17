#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from authapp.models import CustomUser


def fix_admin_password():
    """Fix the admin user password"""

    print("🔧 Fixing Admin User Password")
    print("=" * 50)

    try:
        admin_user = CustomUser.objects.get(email="admin@rslsolution.com")
        print(f"👤 Found admin user: {admin_user.email}")
        print(f"   - Role: {admin_user.role}")
        print(f"   - Company: {admin_user.company_name}")

        # Set the password
        admin_user.set_password("admin123")
        admin_user.save()

        # Verify the password
        if admin_user.check_password("admin123"):
            print(f"   ✅ Password set successfully")
        else:
            print(f"   ❌ Password verification failed")

    except CustomUser.DoesNotExist:
        print(f"❌ Admin user not found")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    fix_admin_password()
    print("\n✅ Admin password fix completed!")
