#!/usr/bin/env python
"""
Comprehensive test script to diagnose interview link email sending issues.

This script will:
1. Check email configuration
2. Test SMTP connection
3. Test sending a sample interview link email
4. Diagnose common issues

Run: python test_interview_email_sending.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")

try:
    django.setup()
except Exception as e:
    print(f"❌ Failed to setup Django: {e}")
    sys.exit(1)

from django.conf import settings
from django.core.mail import send_mail, get_connection
from django.core.mail.backends.console import EmailBackend
from notifications.services import NotificationService
from interviews.models import Interview, InterviewSchedule
from candidates.models import Candidate
from jobs.models import Job


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_section(text):
    """Print section header."""
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print(f"{'─' * 70}\n")


def check_email_configuration():
    """Check email configuration settings."""
    print_section("📧 Email Configuration Check")
    
    issues = []
    
    # Check EMAIL_BACKEND
    email_backend = getattr(settings, "EMAIL_BACKEND", None)
    print(f"EMAIL_BACKEND: {email_backend}")
    if not email_backend:
        issues.append("❌ EMAIL_BACKEND is not set")
    elif "console" in email_backend.lower():
        print("⚠️  Using console backend - emails will print to console, not send")
        issues.append("⚠️  Using console backend (emails won't actually be sent)")
    elif "smtp" not in email_backend.lower():
        issues.append(f"⚠️  Using non-SMTP backend: {email_backend}")
    
    # Check EMAIL_HOST
    email_host = getattr(settings, "EMAIL_HOST", "")
    print(f"EMAIL_HOST: {email_host if email_host else '❌ NOT SET'}")
    if not email_host:
        issues.append("❌ EMAIL_HOST is not set")
    
    # Check EMAIL_PORT
    email_port = getattr(settings, "EMAIL_PORT", None)
    print(f"EMAIL_PORT: {email_port}")
    if not email_port:
        issues.append("❌ EMAIL_PORT is not set")
    
    # Check EMAIL_HOST_USER
    email_user = getattr(settings, "EMAIL_HOST_USER", "")
    print(f"EMAIL_HOST_USER: {email_user if email_user else '❌ NOT SET'}")
    if not email_user:
        issues.append("❌ EMAIL_HOST_USER is not set")
    
    # Check EMAIL_HOST_PASSWORD
    email_password = getattr(settings, "EMAIL_HOST_PASSWORD", "")
    password_length = len(email_password) if email_password else 0
    print(f"EMAIL_HOST_PASSWORD: {'✅ SET' if email_password else '❌ NOT SET'} ({password_length} chars)")
    if not email_password:
        issues.append("❌ EMAIL_HOST_PASSWORD is not set")
    elif password_length < 8:
        issues.append("⚠️  EMAIL_HOST_PASSWORD seems too short (might be incorrect)")
    
    # Check DEFAULT_FROM_EMAIL
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "")
    print(f"DEFAULT_FROM_EMAIL: {from_email if from_email else '❌ NOT SET'}")
    if not from_email:
        issues.append("❌ DEFAULT_FROM_EMAIL is not set")
    
    # Check TLS/SSL settings
    use_tls = getattr(settings, "EMAIL_USE_TLS", False)
    use_ssl = getattr(settings, "EMAIL_USE_SSL", False)
    print(f"EMAIL_USE_TLS: {use_tls}")
    print(f"EMAIL_USE_SSL: {use_ssl}")
    
    if not use_tls and not use_ssl:
        issues.append("⚠️  Neither TLS nor SSL is enabled (may cause connection issues)")
    
    # Summary
    if issues:
        print("\n⚠️  Configuration Issues Found:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ Email configuration looks good!")
        return True


def test_smtp_connection():
    """Test SMTP connection."""
    print_section("🔌 SMTP Connection Test")
    
    try:
        connection = get_connection(
            backend="django.core.mail.backends.smtp.EmailBackend",
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            use_ssl=settings.EMAIL_USE_SSL,
            fail_silently=False,
        )
        
        print("Attempting to connect to SMTP server...")
        connection.open()
        print("✅ Successfully connected to SMTP server!")
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to SMTP server: {e}")
        print("\nCommon causes:")
        print("  1. Wrong email password (should be App Password for Gmail)")
        print("  2. Email host/port incorrect")
        print("  3. Firewall blocking connection")
        print("  4. TLS/SSL settings mismatch")
        return False


def test_simple_email():
    """Test sending a simple email."""
    print_section("📨 Simple Email Test")
    
    test_email = input("Enter your email address to receive test email (or press Enter to skip): ").strip()
    if not test_email:
        print("Skipping simple email test.")
        return None
    
    try:
        subject = "Test Email - AI Interview Portal"
        message = "This is a test email from the AI Interview Portal. If you receive this, email configuration is working correctly!"
        
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        
        if result:
            print(f"✅ Email sent successfully! Check {test_email}")
            return True
        else:
            print("❌ Email send returned False")
            return False
            
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        print("\nError details:")
        print(f"  Type: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        
        # Check if it's an authentication error
        if "authentication" in str(e).lower() or "535" in str(e) or "535-5.7.8" in str(e):
            print("\n⚠️  This looks like an authentication error.")
            print("   For Gmail, make sure you're using an App Password, not your regular password.")
            print("   Generate one at: https://myaccount.google.com/apppasswords")
        
        return False


def test_interview_notification():
    """Test interview notification email sending."""
    print_section("🔗 Interview Link Email Test")
    
    # Check if we have any interviews
    interviews = Interview.objects.all()[:5]
    if not interviews.exists():
        print("❌ No interviews found in database. Cannot test interview notification.")
        print("   Please create an interview first to test this functionality.")
        return False
    
    print(f"Found {interviews.count()} interview(s). Select one to test:")
    for idx, interview in enumerate(interviews, 1):
        candidate = interview.candidate
        print(f"  {idx}. Interview ID: {interview.id} - {candidate.full_name} ({candidate.email})")
    
    try:
        choice = input("\nEnter interview number (1-5) or press Enter to use first interview: ").strip()
        if choice:
            interview = interviews[int(choice) - 1]
        else:
            interview = interviews[0]
        
        print(f"\nTesting with Interview ID: {interview.id}")
        print(f"Candidate: {interview.candidate.full_name} ({interview.candidate.email})")
        
        # Check if interview has a schedule
        if not hasattr(interview, 'schedule') or not interview.schedule:
            print("⚠️  Interview doesn't have a schedule. Creating test schedule...")
            # Try to create a simple schedule for testing
            from interviews.models import InterviewSlot
            slot = InterviewSlot.objects.first()
            if slot:
                from interviews.models import InterviewSchedule
                schedule, created = InterviewSchedule.objects.get_or_create(
                    interview=interview,
                    slot=slot,
                    defaults={"status": "pending", "booking_notes": "Test schedule"}
                )
                print(f"{'Created' if created else 'Using existing'} schedule: {schedule.id}")
            else:
                print("❌ No interview slots found. Cannot create schedule.")
                return False
        
        # Test the notification service
        print("\nSending interview notification email...")
        result = NotificationService.send_candidate_interview_scheduled_notification(interview)
        
        if result:
            print("✅ Interview notification email sent successfully!")
            print(f"   Check {interview.candidate.email} for the email")
            return True
        else:
            print("❌ Interview notification email failed")
            return False
            
    except ValueError:
        print("❌ Invalid choice")
        return False
    except Exception as e:
        print(f"❌ Error testing interview notification: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_notification_service():
    """Check if notification service can access email settings."""
    print_section("🔍 Notification Service Check")
    
    try:
        # Check if the service can access settings
        from django.conf import settings as django_settings
        
        print("Checking notification service email configuration access...")
        
        # Simulate what the notification service does
        from_email = settings.DEFAULT_FROM_EMAIL
        email_backend = settings.EMAIL_BACKEND
        
        print(f"✅ Can access DEFAULT_FROM_EMAIL: {from_email}")
        print(f"✅ Can access EMAIL_BACKEND: {email_backend}")
        
        if "console" in email_backend.lower():
            print("⚠️  Notification service will use console backend (emails print to console)")
        else:
            print("✅ Notification service will use SMTP backend")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking notification service: {e}")
        return False


def main():
    """Main test function."""
    print_header("Interview Link Email Sending Diagnostics")
    
    print("This script will help diagnose why interview link emails are not being sent.")
    print("\nTests will check:")
    print("  1. Email configuration (credentials, host, port, etc.)")
    print("  2. SMTP connection")
    print("  3. Simple email sending")
    print("  4. Interview notification email sending")
    print("  5. Notification service configuration")
    
    proceed = input("\nReady to start diagnostics? (y/n): ").strip().lower()
    if proceed != "y":
        print("Diagnostics cancelled.")
        return
    
    results = {}
    
    # Test 1: Configuration check
    results['config'] = check_email_configuration()
    
    # Test 2: SMTP connection (only if not using console backend)
    email_backend = getattr(settings, "EMAIL_BACKEND", "")
    if "smtp" in email_backend.lower():
        results['smtp'] = test_smtp_connection()
    else:
        print("\n⚠️  Skipping SMTP connection test (not using SMTP backend)")
        results['smtp'] = None
    
    # Test 3: Simple email
    if results.get('config') or input("\nContinue with simple email test? (y/n): ").strip().lower() == "y":
        results['simple_email'] = test_simple_email()
    
    # Test 4: Notification service check
    results['notification_service'] = check_notification_service()
    
    # Test 5: Interview notification
    if input("\nTest interview notification email? (y/n): ").strip().lower() == "y":
        results['interview_notification'] = test_interview_notification()
    
    # Summary
    print_header("Diagnostics Summary")
    
    print("\nTest Results:")
    print(f"  Configuration Check: {'✅ PASS' if results.get('config') else '❌ FAIL'}")
    if results.get('smtp') is not None:
        print(f"  SMTP Connection: {'✅ PASS' if results.get('smtp') else '❌ FAIL'}")
    print(f"  Simple Email: {'✅ PASS' if results.get('simple_email') else '❌ FAIL' if results.get('simple_email') is not None else '⏭️  SKIPPED'}")
    print(f"  Notification Service: {'✅ PASS' if results.get('notification_service') else '❌ FAIL'}")
    print(f"  Interview Notification: {'✅ PASS' if results.get('interview_notification') else '❌ FAIL' if results.get('interview_notification') is not None else '⏭️  SKIPPED'}")
    
    # Recommendations
    print("\n📋 Recommendations:")
    
    if not results.get('config'):
        print("  • Fix email configuration issues first")
        print("  • Check your .env file or environment variables")
        print("  • See EMAIL_HOST_PASSWORD_GUIDE.md for setup instructions")
    
    if results.get('config') and not results.get('smtp'):
        print("  • SMTP connection failed - check credentials")
        print("  • For Gmail: Use App Password (not regular password)")
        print("  • Verify EMAIL_HOST and EMAIL_PORT are correct")
    
    if results.get('simple_email') is False:
        print("  • Simple email test failed - this will affect interview emails")
        print("  • Check email credentials and SMTP settings")
    
    if results.get('notification_service') and not results.get('interview_notification'):
        print("  • Notification service works but interview emails fail")
        print("  • Check if interviews have proper schedules and candidates")
    
    print("\n✅ Diagnostics complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnostics cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

