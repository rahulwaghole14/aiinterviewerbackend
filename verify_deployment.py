#!/usr/bin/env python
"""
Deployment verification script for Render
This script verifies that all deployment configurations are correct.
"""
import os
import sys

def verify_wsgi_module():
    """Verify that the WSGI module can be imported"""
    try:
        import interview_app.wsgi
        print("✅ WSGI module 'interview_app.wsgi' imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import WSGI module 'interview_app.wsgi': {e}")
        return False

def verify_settings():
    """Verify that Django settings can be loaded"""
    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
        from django.conf import settings
        print(f"✅ Django settings module 'interview_app.settings' loaded successfully")
        print(f"   DEBUG: {settings.DEBUG}")
        print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        return True
    except Exception as e:
        print(f"❌ Failed to load Django settings: {e}")
        return False

def verify_wsgi_application():
    """Verify that the WSGI application object exists"""
    try:
        from interview_app.wsgi import application
        print("✅ WSGI application object found")
        return True
    except ImportError as e:
        print(f"❌ Failed to import WSGI application: {e}")
        return False

def main():
    """Run all verification checks"""
    print("🔍 Verifying deployment configuration...")
    print("=" * 50)
    
    checks = [
        verify_wsgi_module(),
        verify_settings(),
        verify_wsgi_application(),
    ]
    
    print("=" * 50)
    if all(checks):
        print("✅ All deployment checks passed!")
        return 0
    else:
        print("❌ Some deployment checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())

