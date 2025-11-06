#!/usr/bin/env python
"""
Test interview link generation and email sending
Creates InterviewSession, generates link, and sends email to paturkardhananjay9075@gmail.com
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
from django.utils import timezone
from interview_app.models import InterviewSession
import pytz
from datetime import datetime, timedelta

def test_interview_link_generation():
    """Test interview link generation and email sending"""
    print("\n" + "=" * 70)
    print("  Interview Link Generation & Email Sending Test")
    print("=" * 70 + "\n")
    
    # Test candidate details
    candidate_name = "Test Candidate"
    candidate_email = "paturkardhananjay9075@gmail.com"
    job_description = "Software Engineer - AI/ML Position"
    resume_text = "Experienced software engineer with 5 years of experience in AI/ML"
    
    # Schedule for 1 hour from now (IST)
    ist = pytz.timezone('Asia/Kolkata')
    scheduled_time = datetime.now(ist) + timedelta(hours=1)
    
    print("Creating InterviewSession...")
    print(f"  Candidate: {candidate_name}")
    print(f"  Email: {candidate_email}")
    print(f"  Scheduled Time: {scheduled_time.strftime('%B %d, %Y at %I:%M %p IST')}")
    print()
    
    try:
        # Create InterviewSession
        session = InterviewSession.objects.create(
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            job_description=job_description,
            resume_text=resume_text,
            scheduled_at=scheduled_time.astimezone(pytz.UTC),  # Store in UTC
            language_code='en',
            accent_tld='co.in',
            status='SCHEDULED'
        )
        
        print(f"[SUCCESS] InterviewSession created successfully!")
        print(f"  Session ID: {session.id}")
        print(f"  Session Key: {session.session_key}")
        print()
        
        # Generate interview link
        base_url = getattr(settings, "BACKEND_URL", "http://localhost:8000")
        interview_link = f"{base_url}/?session_key={session.session_key}"
        
        print(f"Generated Interview Link:")
        print(f"  {interview_link}")
        print()
        
        # Get email configuration
        email_backend = settings.EMAIL_BACKEND
        email_host = settings.EMAIL_HOST
        email_port = settings.EMAIL_PORT
        email_use_tls = settings.EMAIL_USE_TLS
        email_use_ssl = settings.EMAIL_USE_SSL
        email_user = settings.EMAIL_HOST_USER
        email_password = settings.EMAIL_HOST_PASSWORD
        default_from_email = settings.DEFAULT_FROM_EMAIL
        
        print("Email Configuration:")
        print(f"  EMAIL_BACKEND: {email_backend}")
        print(f"  EMAIL_HOST: {email_host}")
        print(f"  EMAIL_PORT: {email_port}")
        print(f"  EMAIL_USE_TLS: {email_use_tls}")
        print(f"  EMAIL_USE_SSL: {email_use_ssl}")
        print(f"  EMAIL_HOST_USER: {email_user[:20] + '...' if email_user and len(email_user) > 20 else email_user}")
        print(f"  EMAIL_HOST_PASSWORD: {'SET' if email_password else 'NOT SET'}")
        print(f"  DEFAULT_FROM_EMAIL: {default_from_email}")
        print()
        
        # CRITICAL: Fix TLS/SSL conflict - for Gmail with port 587, use TLS only
        if email_port == 587 and email_use_tls and email_use_ssl:
            print("[WARNING] Both TLS and SSL are enabled. Disabling SSL for port 587 (TLS only)...")
            settings.EMAIL_USE_SSL = False
            email_use_ssl = False
            print("  EMAIL_USE_SSL set to: False")
            print()
        
        # Check configuration
        if "console" in str(email_backend).lower():
            print("[ERROR] EMAIL_BACKEND is set to console - emails won't be sent!")
            print("Fix: Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend in .env")
            return False
        
        if not email_host:
            print("[ERROR] EMAIL_HOST is not set!")
            print("Fix: Set EMAIL_HOST=smtp.gmail.com in .env")
            return False
        
        if not email_user or not email_password:
            print("[ERROR] Email credentials not set!")
            print("Fix: Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env")
            return False
        
        # Final check for TLS/SSL conflict
        if email_use_tls and email_use_ssl:
            print("[ERROR] EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be True!")
            print("Fix: For Gmail port 587, set EMAIL_USE_TLS=True and EMAIL_USE_SSL=False in .env")
            return False
        
        # Format scheduled time in IST for email
        scheduled_time_ist = scheduled_time
        scheduled_time_str = scheduled_time_ist.strftime('%A, %B %d, %Y at %I:%M %p IST')
        scheduled_date = scheduled_time_ist.strftime('%B %d, %Y')
        scheduled_time_only = scheduled_time_ist.strftime('%I:%M %p IST')
        
        # Extract job title from job_description
        job_title = "Software Engineer"
        if job_description:
            lines = job_description.split('\n')
            for line in lines:
                if 'Job Title:' in line or 'Title:' in line:
                    job_title = line.split(':')[-1].strip()
                    break
                elif 'Position:' in line:
                    job_title = line.split(':')[-1].strip()
                    break
            if ' - ' in job_description:
                job_title = job_description.split(' - ')[0].strip()
        
        # Create email content
        email_subject = f"Your Interview Has Been Scheduled - {job_title}"
        email_body = f"""Dear {candidate_name},

Your AI interview has been scheduled successfully!

**Interview Details:**
- Candidate: {candidate_name}
- Position: {job_title}
- Date: {scheduled_date}
- Time: {scheduled_time_only}
- Session ID: {session.id}

**Join Your Interview:**
Click the link below to join your interview at the scheduled time:
{interview_link}

**Important Instructions:**
- Please join the interview 5-10 minutes before the scheduled time
- The link will be active 30 seconds before the scheduled time
- The link will expire 10 minutes after the scheduled start time
- Make sure you have a stable internet connection and a quiet environment
- Ensure your camera and microphone are working properly
- Have a valid government-issued ID ready for verification

Best of luck with your interview!

---
This is an automated message. Please do not reply to this email.
"""
        
        print("=" * 70)
        print("Sending Email...")
        print("=" * 70)
        print(f"To: {candidate_email}")
        print(f"Subject: {email_subject}")
        print(f"Interview Link: {interview_link}")
        print()
        
        # Send email
        try:
            send_mail(
                email_subject,
                email_body,
                default_from_email,
                [candidate_email],
                fail_silently=False,
            )
            
            print("=" * 70)
            print("[SUCCESS] Email sent successfully!")
            print("=" * 70)
            print(f"Recipient: {candidate_email}")
            print(f"Interview Link: {interview_link}")
            print(f"Scheduled Time: {scheduled_time_str}")
            print()
            print("[SUCCESS] Test completed successfully!")
            print()
            print("Next Steps:")
            print(f"1. Check inbox at {candidate_email}")
            print(f"2. Click the interview link: {interview_link}")
            print("3. The interview portal should open automatically")
            print()
            
            return True
            
        except Exception as email_error:
            error_msg = str(email_error)
            print("=" * 70)
            print("[EMAIL FAILED] Error sending email")
            print("=" * 70)
            print(f"Error: {error_msg}")
            print()
            
            # Provide helpful error messages
            if "authentication" in error_msg.lower() or "535" in error_msg:
                print("Possible fixes:")
                print("1. Check EMAIL_HOST_PASSWORD - use Gmail App Password, not regular password")
                print("2. Generate new App Password at: https://myaccount.google.com/apppasswords")
            elif "connection" in error_msg.lower() or "timed out" in error_msg.lower():
                print("Possible fixes:")
                print("1. Check EMAIL_HOST and EMAIL_PORT in .env")
                print("2. Verify EMAIL_USE_TLS=True for port 587")
                print("3. Check internet connection and firewall settings")
            else:
                print("Possible fixes:")
                print("1. Verify all email settings in .env file")
                print("2. Check EMAIL_HOST_PASSWORD - use Gmail App Password")
                print("3. Ensure EMAIL_USE_TLS=True for port 587")
            
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to create interview session: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_interview_link_generation()
    sys.exit(0 if success else 1)

