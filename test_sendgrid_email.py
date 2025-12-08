"""
Test script to send email via SendGrid
"""
import os
import sys
import django
from pathlib import Path

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / ".env")
    print("✅ Loaded .env file")
except ImportError:
    print("[WARNING] python-dotenv not installed. Ensure environment variables are set manually.")
except Exception as e:
    print(f"[WARNING] Error loading .env file: {e}")

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
try:
    django.setup()
except Exception as e:
    print(f"[ERROR] Django setup failed: {e}")
    print("Please ensure your Django settings are valid and all dependencies are installed.")
    sys.exit(1)

from django.conf import settings
from django.core.mail import send_mail

print("=" * 70)
print("📧 SendGrid Email Test")
print("=" * 70)

# Check SendGrid configuration
use_sendgrid = getattr(settings, 'USE_SENDGRID', False)
sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', '')
default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
email_backend = getattr(settings, 'EMAIL_BACKEND', '')

print(f"\n📋 Configuration:")
print(f"  USE_SENDGRID: {use_sendgrid}")
print(f"  SENDGRID_API_KEY: {'SET' if sendgrid_api_key else 'NOT SET'}")
print(f"  EMAIL_BACKEND: {email_backend}")
print(f"  DEFAULT_FROM_EMAIL: {default_from_email}")

# Validate configuration
if not use_sendgrid:
    print(f"\n❌ ERROR: USE_SENDGRID is not set to True")
    print(f"   Set USE_SENDGRID=True in .env file or environment variables")
    sys.exit(1)

if not sendgrid_api_key:
    print(f"\n❌ ERROR: SENDGRID_API_KEY is not set")
    print(f"   Set SENDGRID_API_KEY=SG.your-api-key in .env file or environment variables")
    sys.exit(1)

if not default_from_email:
    print(f"\n❌ ERROR: DEFAULT_FROM_EMAIL is not set")
    print(f"   Set DEFAULT_FROM_EMAIL=your-email@example.com in .env file")
    sys.exit(1)

# Test recipient
test_recipient = "paturkardhananjay9075@gmail.com"

print(f"\n📧 Sending test email...")
print(f"  From: {default_from_email}")
print(f"  To: {test_recipient}")
print(f"  Backend: {email_backend}")

try:
    result = send_mail(
        subject="Test Email from SendGrid - AI Interview Platform",
        message=f"""
Hello!

This is a test email sent via SendGrid from the AI Interview Platform.

If you received this email, SendGrid is configured correctly! ✅

Configuration Details:
- Backend: {email_backend}
- From: {default_from_email}
- Sent via: SendGrid API

Best regards,
AI Interview Platform
        """,
        from_email=default_from_email,
        recipient_list=[test_recipient],
        fail_silently=False,
    )
    
    if result:
        print(f"\n✅ SUCCESS! Email sent successfully!")
        print(f"   send_mail() returned: {result}")
        print(f"   Check inbox: {test_recipient}")
        print(f"   (Also check spam folder if not received)")
    else:
        print(f"\n⚠️ WARNING: send_mail() returned False")
        print(f"   Email might not have been sent")
        
except Exception as e:
    error_type = type(e).__name__
    error_msg = str(e)
    print(f"\n❌ ERROR: Failed to send email")
    print(f"   Error Type: {error_type}")
    print(f"   Error Message: {error_msg}")
    print(f"\n💡 Troubleshooting:")
    
    if "403" in error_msg or "forbidden" in error_msg.lower():
        print(f"   ❌ HTTP 403 Forbidden - This usually means:")
        print(f"   1. API Key is invalid or expired")
        print(f"   2. API Key doesn't have 'Mail Send' permissions")
        print(f"   3. Sender email ({default_from_email}) is not verified in SendGrid")
        print(f"   ")
        print(f"   🔧 Solutions:")
        print(f"   a) Verify sender email:")
        print(f"      - Go to SendGrid Dashboard → Settings → Sender Authentication")
        print(f"      - Click 'Verify a Single Sender'")
        print(f"      - Enter: {default_from_email}")
        print(f"      - Complete verification process")
        print(f"   ")
        print(f"   b) Check API Key permissions:")
        print(f"      - Go to SendGrid Dashboard → Settings → API Keys")
        print(f"      - Edit your API key")
        print(f"      - Ensure 'Mail Send' permission is enabled")
        print(f"   ")
        print(f"   c) Regenerate API Key if needed:")
        print(f"      - Create a new API key with 'Full Access' or 'Mail Send'")
        print(f"      - Update SENDGRID_API_KEY in .env file")
    elif "API key" in error_msg.lower() or "unauthorized" in error_msg.lower():
        print(f"   1. Verify SENDGRID_API_KEY is correct")
        print(f"   2. Check if API key has 'Mail Send' permissions")
        print(f"   3. Regenerate API key in SendGrid dashboard")
    elif "sender" in error_msg.lower() or "from" in error_msg.lower():
        print(f"   1. Verify sender email in SendGrid dashboard")
        print(f"   2. Go to Settings → Sender Authentication")
        print(f"   3. Verify the email: {default_from_email}")
    else:
        print(f"   1. Check SendGrid account status")
        print(f"   2. Verify API key permissions")
        print(f"   3. Check SendGrid dashboard for errors")
    
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ Test completed!")
print("=" * 70)

