#!/usr/bin/env python
"""
Test interview email sending functionality
Simulates sending an interview scheduled email
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
django.setup()

from django.conf import settings
from notifications.services import NotificationService
from interviews.models import Interview
from candidates.models import Candidate
from jobs.models import Job

print("=" * 70)
print("📧 Testing Interview Email Sending")
print("=" * 70)

# Check email configuration first
print("\n📋 Email Configuration:")
print("-" * 70)
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")

if "console" in str(settings.EMAIL_BACKEND).lower():
    print("\n❌ ERROR: EMAIL_BACKEND is set to console - emails won't be sent!")
    print("   Fix: Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")
    sys.exit(1)

# Try to find a recent interview
print("\n🔍 Looking for recent interviews...")
try:
    # Get the most recent interview
    interview = Interview.objects.filter(
        candidate__isnull=False,
        candidate__email__isnull=False
    ).exclude(
        candidate__email=''
    ).order_by('-created_at').first()
    
    if not interview:
        print("❌ No interviews found with candidate email addresses")
        print("\n💡 Creating a test interview...")
        
        # Try to get or create a test candidate
        candidate, created = Candidate.objects.get_or_create(
            email='paturakrdhananjay9075@gmail.com',
            defaults={
                'full_name': 'Test Candidate',
                'phone_number': '1234567890',
            }
        )
        
        # Try to get a job
        job = Job.objects.first()
        
        if not job:
            print("❌ No jobs found. Cannot create test interview.")
            sys.exit(1)
        
        # Create a test interview
        from datetime import datetime, timedelta
        import pytz
        
        ist = pytz.timezone('Asia/Kolkata')
        start_time = datetime.now(ist) + timedelta(hours=2)
        end_time = start_time + timedelta(hours=1)
        
        interview = Interview.objects.create(
            candidate=candidate,
            job=job,
            started_at=start_time.astimezone(pytz.UTC),
            ended_at=end_time.astimezone(pytz.UTC),
            status='scheduled',
        )
        
        print(f"✅ Created test interview: {interview.id}")
    else:
        print(f"✅ Found interview: {interview.id}")
        print(f"   Candidate: {interview.candidate.email}")
        print(f"   Status: {interview.status}")
    
    # Test sending email
    print("\n📤 Attempting to send interview email...")
    print(f"   To: {interview.candidate.email}")
    print(f"   Interview ID: {interview.id}")
    
    result = NotificationService.send_candidate_interview_scheduled_notification(interview)
    
    if result:
        print("\n" + "=" * 70)
        print("✅ SUCCESS! Interview email sent successfully!")
        print("=" * 70)
        print(f"📧 Email sent to: {interview.candidate.email}")
        print(f"📬 Check inbox and spam folder")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ FAILED! Interview email was not sent")
        print("=" * 70)
        print("Check the error messages above for details")
        print("=" * 70)
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


