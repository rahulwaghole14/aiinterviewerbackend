#!/usr/bin/env python
"""
Check current email backend configuration
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
django.setup()

from django.conf import settings

print("=" * 70)
print("📧 Current Email Backend Configuration")
print("=" * 70)

email_backend = settings.EMAIL_BACKEND
print(f"\nCurrent EMAIL_BACKEND: {email_backend}")

if "smtp" in str(email_backend).lower():
    print("✅ Email backend is set to SMTP (correct for sending emails)")
else:
    print("❌ Email backend is NOT set to SMTP")
    print("   Current value will NOT send actual emails!")

print("\n" + "=" * 70)
print("📋 For Render Deployment:")
print("=" * 70)
print("\n1. Go to Render Dashboard → Your Backend Service → Environment")
print("2. Add/Update this environment variable:")
print("\n   Key: EMAIL_BACKEND")
print("   Value: django.core.mail.backends.smtp.EmailBackend")
print("\n3. Make sure it's NOT set to:")
print("   ❌ django.core.mail.backends.console.EmailBackend")
print("   ❌ django.core.mail.backends.locmem.EmailBackend")
print("\n4. Save changes - Render will automatically redeploy")
print("=" * 70)


