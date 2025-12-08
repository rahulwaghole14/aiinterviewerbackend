#!/usr/bin/env python
"""
Test email sending functionality for interview link emails
Run this script to verify email configuration is working
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from django.core.mail.backends import console, smtp

print("=" * 70)
print("📧 Testing Email Sending Functionality")
print("=" * 70)

# Check email configuration
print("\n📋 Email Configuration Check:")
print("-" * 70)

email_backend = settings.EMAIL_BACKEND
email_host = settings.EMAIL_HOST
email_port = settings.EMAIL_PORT
email_use_tls = settings.EMAIL_USE_TLS
email_use_ssl = settings.EMAIL_USE_SSL
email_user = settings.EMAIL_HOST_USER
email_password = settings.EMAIL_HOST_PASSWORD
default_from = settings.DEFAULT_FROM_EMAIL

print(f"EMAIL_BACKEND: {email_backend}")
print(f"EMAIL_HOST: {email_host or 'NOT SET'}")
print(f"EMAIL_PORT: {email_port}")
print(f"EMAIL_USE_TLS: {email_use_tls}")
print(f"EMAIL_USE_SSL: {email_use_ssl}")
print(f"EMAIL_HOST_USER: {email_user or 'NOT SET'}")
print(f"EMAIL_HOST_PASSWORD: {'SET' if email_password else 'NOT SET'}")
print(f"DEFAULT_FROM_EMAIL: {default_from}")

# Validation checks
print("\n🔍 Validation Checks:")
print("-" * 70)

issues = []

# Check 1: Email backend
if "console" in str(email_backend).lower():
    issues.append("❌ EMAIL_BACKEND is set to 'console' - emails won't be sent!")
    issues.append("   Fix: Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")
else:
    print("✅ EMAIL_BACKEND is set to SMTP")

# Check 2: Email host
if not email_host:
    issues.append("❌ EMAIL_HOST is not set")
    issues.append("   Fix: Set EMAIL_HOST=smtp.gmail.com")
else:
    print(f"✅ EMAIL_HOST is set: {email_host}")

# Check 3: Email credentials
if not email_user:
    issues.append("❌ EMAIL_HOST_USER is not set")
    issues.append("   Fix: Set EMAIL_HOST_USER=your-email@gmail.com")
else:
    print(f"✅ EMAIL_HOST_USER is set: {email_user}")

if not email_password:
    issues.append("❌ EMAIL_HOST_PASSWORD is not set")
    issues.append("   Fix: Set EMAIL_HOST_PASSWORD=your-gmail-app-password")
else:
    print(f"✅ EMAIL_HOST_PASSWORD is set")

# Check 4: TLS/SSL configuration
if email_port == 587:
    if not email_use_tls:
        issues.append("❌ EMAIL_USE_TLS should be True for port 587")
        issues.append("   Fix: Set EMAIL_USE_TLS=True")
    else:
        print("✅ EMAIL_USE_TLS is True (correct for port 587)")
    
    if email_use_ssl:
        issues.append("❌ EMAIL_USE_SSL should be False for port 587")
        issues.append("   Fix: Set EMAIL_USE_SSL=False")
    else:
        print("✅ EMAIL_USE_SSL is False (correct for port 587)")
elif email_port == 465:
    if email_use_tls:
        issues.append("❌ EMAIL_USE_TLS should be False for port 465")
        issues.append("   Fix: Set EMAIL_USE_TLS=False")
    else:
        print("✅ EMAIL_USE_TLS is False (correct for port 465)")
    
    if not email_use_ssl:
        issues.append("❌ EMAIL_USE_SSL should be True for port 465")
        issues.append("   Fix: Set EMAIL_USE_SSL=True")
    else:
        print("✅ EMAIL_USE_SSL is True (correct for port 465)")

# Check 5: TLS/SSL conflict
if email_use_tls and email_use_ssl:
    issues.append("❌ EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be True!")
    issues.append("   Fix: For port 587, set EMAIL_USE_TLS=True and EMAIL_USE_SSL=False")
    issues.append("   Fix: For port 465, set EMAIL_USE_TLS=False and EMAIL_USE_SSL=True")

# Display issues
if issues:
    print("\n⚠️  Configuration Issues Found:")
    print("-" * 70)
    for issue in issues:
        print(issue)
    print("\n" + "=" * 70)
    print("❌ Email configuration has issues. Please fix them before testing.")
    print("=" * 70)
    sys.exit(1)

print("\n✅ All configuration checks passed!")

# Test email sending
print("\n" + "=" * 70)
print("📤 Attempting to Send Test Email")
print("=" * 70)

# Get test email address
test_email = input("\nEnter your email address to receive test email (or press Enter to skip): ").strip()

if not test_email:
    print("\n⚠️  No email address provided. Skipping actual email send test.")
    print("✅ Configuration check completed successfully!")
    print("\nTo test actual email sending, run this script again and provide an email address.")
    sys.exit(0)

print(f"\n📧 Sending test email to: {test_email}")
print("   From: " + default_from)
print("   Subject: Test Email from Django AI Interview Platform")

try:
    result = send_mail(
        subject='Test Email from Django AI Interview Platform',
        message='''
This is a test email from your Django AI Interview Platform.

If you received this email, your email configuration is working correctly! ✅

Email Configuration:
- EMAIL_HOST: {email_host}
- EMAIL_PORT: {email_port}
- EMAIL_USE_TLS: {email_use_tls}
- EMAIL_USE_SSL: {email_use_ssl}

You can now send interview link emails to candidates.

Best regards,
AI Interview Platform
        '''.format(
            email_host=email_host,
            email_port=email_port,
            email_use_tls=email_use_tls,
            email_use_ssl=email_use_ssl
        ),
        from_email=default_from,
        recipient_list=[test_email],
        fail_silently=False,
    )
    
    print("\n" + "=" * 70)
    print("✅ SUCCESS! Test email sent successfully!")
    print("=" * 70)
    print(f"📧 Check your inbox at: {test_email}")
    print(f"📬 Also check spam/junk folder if not in inbox")
    print("\n✅ Email sending functionality is working correctly!")
    print("=" * 70)
    
except Exception as e:
    error_msg = str(e)
    print("\n" + "=" * 70)
    print("❌ FAILED! Email sending failed")
    print("=" * 70)
    print(f"Error: {error_msg}")
    
    # Provide helpful error messages
    if "authentication" in error_msg.lower() or "535" in error_msg:
        print("\n🔧 Possible Solutions:")
        print("1. Check EMAIL_HOST_PASSWORD - use Gmail App Password, not regular password")
        print("2. Generate new App Password at: https://myaccount.google.com/apppasswords")
        print("3. Make sure 2-Step Verification is enabled on your Gmail account")
    elif "connection" in error_msg.lower() or "timed out" in error_msg.lower():
        print("\n🔧 Possible Solutions:")
        print("1. Check EMAIL_HOST and EMAIL_PORT are correct")
        print("2. Verify EMAIL_USE_TLS=True for port 587")
        print("3. Check internet connection and firewall settings")
        print("4. Try port 465 with SSL instead")
    elif "ssl" in error_msg.lower() or "tls" in error_msg.lower():
        print("\n🔧 Possible Solutions:")
        print("1. For port 587: Set EMAIL_USE_TLS=True and EMAIL_USE_SSL=False")
        print("2. For port 465: Set EMAIL_USE_TLS=False and EMAIL_USE_SSL=True")
    else:
        print("\n🔧 General Solutions:")
        print("1. Verify all email settings in .env file or Render environment variables")
        print("2. Check EMAIL_HOST_PASSWORD is Gmail App Password (16 characters)")
        print("3. Ensure EMAIL_BACKEND is set to smtp.EmailBackend")
        print("4. Review error message above for specific details")
    
    print("\n" + "=" * 70)
    sys.exit(1)

