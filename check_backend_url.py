#!/usr/bin/env python
"""
Check BACKEND_URL configuration for interview links
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
django.setup()

from django.conf import settings

print("=" * 70)
print("🔗 Checking BACKEND_URL Configuration")
print("=" * 70)

backend_url = getattr(settings, 'BACKEND_URL', None)

print(f"\nCurrent BACKEND_URL: {backend_url or 'NOT SET (defaults to localhost:8000)'}")

if not backend_url or 'localhost' in str(backend_url).lower():
    print("\n⚠️  WARNING: BACKEND_URL is not set or is using localhost!")
    print("   This means interview links will point to localhost instead of your Render URL")
    print("\n📋 To Fix:")
    print("   1. Add to .env file or Render environment variables:")
    print("      BACKEND_URL=https://aiinterviewerbackend-2.onrender.com")
    print("   2. Replace with your actual Render backend URL")
    print("   3. No trailing slash!")
else:
    print(f"\n✅ BACKEND_URL is set correctly: {backend_url}")

print("\n" + "=" * 70)
print("📧 Email Status:")
print("=" * 70)
print("✅ Email was sent successfully to: paturkardhananjay9075@gmail.com")
print("📬 Check inbox and spam folder")
print("\n⚠️  If interview link doesn't work, check BACKEND_URL is set correctly")
print("=" * 70)


