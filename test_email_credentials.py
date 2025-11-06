#!/usr/bin/env python
"""
Test email sending with credentials from .env file
Sends test email to: paturkardhananjay9075@gmail.com
"""

import os
import sys

# Setup Django first to load .env
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")

try:
    import django
    django.setup()
except Exception as e:
    print(f"❌ Failed to setup Django: {e}")
    sys.exit(1)

from django.conf import settings
from django.core.mail import send_mail, get_connection

def print_config():
    """Print current email configuration."""
    print("\n" + "=" * 70)
    print("  Current Email Configuration")
    print("=" * 70 + "\n")
    
    print(f"EMAIL_BACKEND:      {getattr(settings, 'EMAIL_BACKEND', 'NOT SET')}")
    print(f"EMAIL_HOST:         {getattr(settings, 'EMAIL_HOST', 'NOT SET')}")
    print(f"EMAIL_PORT:         {getattr(settings, 'EMAIL_PORT', 'NOT SET')}")
    print(f"EMAIL_USE_TLS:      {getattr(settings, 'EMAIL_USE_TLS', 'NOT SET')}")
    print(f"EMAIL_USE_SSL:      {getattr(settings, 'EMAIL_USE_SSL', 'NOT SET')}")
    print(f"EMAIL_HOST_USER:    {getattr(settings, 'EMAIL_HOST_USER', 'NOT SET')}")
    password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    password_status = "SET" if password else "NOT SET"
    print(f"EMAIL_HOST_PASSWORD: {password_status} ({len(password)} chars)")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")

def test_smtp_connection():
    """Test SMTP connection."""
    print("\n" + "=" * 70)
    print("  Testing SMTP Connection")
    print("=" * 70 + "\n")
    
    try:
        # Ensure TLS and SSL are not both True
        use_tls = settings.EMAIL_USE_TLS
        use_ssl = settings.EMAIL_USE_SSL
        if use_tls and use_ssl:
            # For port 587, prefer TLS; for 465, prefer SSL
            if settings.EMAIL_PORT == 587:
                use_ssl = False
            elif settings.EMAIL_PORT == 465:
                use_tls = False
            else:
                use_ssl = False  # Default to TLS
        
        connection = get_connection(
            backend="django.core.mail.backends.smtp.EmailBackend",
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=use_tls,
            use_ssl=use_ssl,
            fail_silently=False,
        )
        
        print("Attempting to connect to SMTP server...")
        connection.open()
        print("[SUCCESS] Successfully connected to SMTP server!")
        connection.close()
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Failed to connect to SMTP server: {error_msg}")
        if "mutually exclusive" in error_msg.lower():
            print("[INFO] Fix: Set either EMAIL_USE_TLS=True OR EMAIL_USE_SSL=True (not both)")
            print("        For Gmail port 587: Use EMAIL_USE_TLS=True, EMAIL_USE_SSL=False")
            print("        For Gmail port 465: Use EMAIL_USE_TLS=False, EMAIL_USE_SSL=True")
        return False

def send_test_email():
    """Send test email to paturkardhananjay9075@gmail.com"""
    print("\n" + "=" * 70)
    print("  Sending Test Email")
    print("=" * 70 + "\n")
    
    to_email = "paturkardhananjay9075@gmail.com"
    subject = "Test Email - AI Interview Portal Email Configuration"
    
    message = """
Hello!

This is a test email from the AI Interview Portal to verify that email credentials are configured correctly.

If you received this email, it means:
✅ SMTP connection is working
✅ Email credentials are correct
✅ Interview link emails will be sent successfully

Email Configuration Test:
- Backend: {backend}
- Host: {host}
- Port: {port}
- From: {from_email}

Best regards,
AI Interview Portal System
    """.format(
        backend=settings.EMAIL_BACKEND,
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        from_email=settings.DEFAULT_FROM_EMAIL
    )
    
    try:
        print(f"Sending email to: {to_email}")
        print(f"From: {settings.DEFAULT_FROM_EMAIL}")
        print(f"Subject: {subject}")
        print("\nSending...")
        
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        
        if result:
            print(f"\n[SUCCESS] Email sent successfully!")
            print(f"[INFO] Please check the inbox of: {to_email}")
            print("   (Also check spam/junk folder if not in inbox)")
            return True
        else:
            print("\n[ERROR] Email send returned False (no error but email not sent)")
            return False
            
    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] Failed to send email: {error_msg}")
        
        # Provide helpful error messages
        if "authentication" in error_msg.lower() or "535" in error_msg:
            print("\n[WARNING] Authentication Error Detected!")
            print("   This usually means:")
            print("   1. Wrong password (should be App Password for Gmail)")
            print("   2. 2-Step Verification not enabled")
            print("   Generate App Password at: https://myaccount.google.com/apppasswords")
        elif "connection" in error_msg.lower():
            print("\n[WARNING] Connection Error Detected!")
            print("   Check:")
            print("   - EMAIL_HOST is correct")
            print("   - EMAIL_PORT is correct")
            print("   - Internet connection")
            print("   - Firewall settings")
        
        return False

def main():
    """Main function."""
    print("\n" + "=" * 70)
    print("  EMAIL CREDENTIALS TEST")
    print("=" * 70)
    
    # Step 1: Show configuration
    print_config()
    
    # Check if using console backend
    email_backend = getattr(settings, 'EMAIL_BACKEND', '')
    if 'console' in email_backend.lower():
        print("\n[WARNING] EMAIL_BACKEND is set to console!")
        print("   Email will print to console, not actually send.")
        print("   Setting EMAIL_BACKEND to SMTP for this test...")
        # Override for this test
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    
    # Check if credentials are set
    email_host = getattr(settings, 'EMAIL_HOST', '')
    email_user = getattr(settings, 'EMAIL_HOST_USER', '')
    email_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    
    if not email_host:
        print("\n[WARNING] EMAIL_HOST not set. Setting to smtp.gmail.com for Gmail...")
        settings.EMAIL_HOST = 'smtp.gmail.com'
        email_host = 'smtp.gmail.com'
    
    # Fix TLS/SSL conflict - for Gmail with port 587, use TLS only
    if settings.EMAIL_PORT == 587 and settings.EMAIL_USE_TLS and settings.EMAIL_USE_SSL:
        print("\n[WARNING] Both TLS and SSL are enabled. Disabling SSL for port 587 (TLS only)...")
        settings.EMAIL_USE_SSL = False
    
    if not email_user or not email_password:
        print("\n[ERROR] Email credentials incomplete!")
        print("   Missing:")
        if not email_user:
            print("   - EMAIL_HOST_USER")
        if not email_password:
            print("   - EMAIL_HOST_PASSWORD")
        print("\n   Please set these in your .env file.")
        return
    
    # Step 2: Test SMTP connection
    print("\n")
    connection_ok = test_smtp_connection()
    
    if not connection_ok:
        print("\n[INFO] SMTP connection failed, but continuing with email test...")
    
    # Step 3: Send test email
    print("\n")
    success = send_test_email()
    
    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70 + "\n")
    
    print(f"SMTP Connection: {'[PASSED]' if connection_ok else '[FAILED]'}")
    print(f"Email Send:      {'[PASSED]' if success else '[FAILED]'}")
    
    if success:
        print("\n[SUCCESS] Email test completed successfully!")
        print(f"[INFO] Check paturkardhananjay9075@gmail.com for the test email")
    else:
        print("\n[ERROR] Email test failed. Check error messages above.")
        print("\nNext steps:")
        print("1. Verify credentials in .env file")
        print("2. For Gmail: Use App Password (not regular password)")
        print("3. Check EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS settings")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

