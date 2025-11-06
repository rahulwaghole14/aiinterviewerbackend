#!/usr/bin/env python
"""
Test email sending with current configuration
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")

try:
    django.setup()
except Exception as e:
    print(f"Failed to setup Django: {e}")
    sys.exit(1)

from django.conf import settings
from django.core.mail import send_mail

def test_email():
    """Test email sending"""
    print("\n" + "=" * 70)
    print("  Email Sending Test")
    print("=" * 70 + "\n")
    
    print("Current Configuration:")
    print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"  EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
    print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER[:20]}..." if settings.EMAIL_HOST_USER else "  EMAIL_HOST_USER: NOT SET")
    print(f"  EMAIL_HOST_PASSWORD: {'SET' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print()
    
    # Fix TLS/SSL conflict - for Gmail with port 587, use TLS only
    if settings.EMAIL_PORT == 587 and settings.EMAIL_USE_TLS and settings.EMAIL_USE_SSL:
        print("[WARNING] Both TLS and SSL are enabled. Disabling SSL for port 587 (TLS only)...")
        settings.EMAIL_USE_SSL = False
        print("  EMAIL_USE_SSL set to: False")
        print()
    
    # Check configuration
    if "console" in settings.EMAIL_BACKEND.lower():
        print("[ERROR] EMAIL_BACKEND is set to console - emails won't be sent!")
        print("Fix: Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend in .env")
        return False
    
    if not settings.EMAIL_HOST:
        print("[ERROR] EMAIL_HOST is not set!")
        print("Fix: Set EMAIL_HOST=smtp.gmail.com in .env")
        return False
    
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("[ERROR] Email credentials not set!")
        return False
    
    # Final check for TLS/SSL conflict
    if settings.EMAIL_USE_TLS and settings.EMAIL_USE_SSL:
        print("[ERROR] EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be True!")
        print("Fix: For Gmail port 587, set EMAIL_USE_TLS=True and EMAIL_USE_SSL=False in .env")
        return False
    
    # Test email - use command line argument or default to specified email
    import sys
    if len(sys.argv) > 1:
        test_email_to = sys.argv[1]
        print(f"Using email from command line argument: {test_email_to}")
    else:
        # Default to specific test email
        test_email_to = "paturkardhananjay9075@gmail.com"
        print(f"Using default test email: {test_email_to}")
    
    print(f"\nSending test email to: {test_email_to}")
    
    try:
        send_mail(
            subject="Test Email - Interview Portal",
            message="This is a test email from the Interview Portal system.\n\nIf you received this, email configuration is working correctly!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email_to],
            fail_silently=False,
        )
        print("[SUCCESS] Test email sent successfully!")
        print(f"Check inbox at: {test_email_to}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        print("\nPossible fixes:")
        print("1. Check EMAIL_HOST_PASSWORD - use Gmail App Password")
        print("2. Check EMAIL_HOST and EMAIL_PORT")
        print("3. Verify EMAIL_USE_TLS=True for port 587")
        return False

if __name__ == "__main__":
    test_email()

