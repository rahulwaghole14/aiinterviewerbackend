#!/usr/bin/env python
"""
Reset admin user password
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from authapp.models import CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()

def reset_admin_password():
    """Reset admin user password"""
    email = 'admin@rslsolution.com'
    new_password = 'admin123'
    
    try:
        user = User.objects.get(email=email)
        print(f"Found user: {user.email}")
        
        # Reset password
        user.set_password(new_password)
        user.save()
        
        print(f"✅ Password reset successfully!")
        print(f"New password: {new_password}")
        
        # Verify the password
        if user.check_password(new_password):
            print("✅ Password verification successful!")
        else:
            print("❌ Password verification failed!")
            
        return user
    except User.DoesNotExist:
        print(f"❌ User {email} not found")
        return None

if __name__ == '__main__':
    print("🔧 Resetting admin password...")
    reset_admin_password()
    print("✅ Done!") 