#!/usr/bin/env python
"""
Send interview scheduling emails to candidates using the same reliable approach as test_email_sending_live.py
Gets candidate emails from scheduled interviews and sends interview link
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
from interviews.models import Interview
import pytz
from datetime import datetime

def send_interview_email_to_candidate(interview):
    """Send interview scheduling email to candidate using same approach as test_email_sending_live.py"""
    
    # Get candidate details
    candidate_email = interview.candidate.email
    candidate_name = interview.candidate.full_name
    
    # Get interview details
    job_title = "N/A"
    company_name = "N/A"
    
    if interview.job:
        job_title = interview.job.job_title
        company_name = interview.job.company_name
    elif hasattr(interview, "schedule") and interview.schedule and interview.schedule.slot:
        if interview.schedule.slot.job:
            job_title = interview.schedule.slot.job.job_title
            company_name = interview.schedule.slot.job.company_name
    
    # Get interview times in IST
    ist = pytz.timezone('Asia/Kolkata')
    if interview.started_at and interview.ended_at:
        start_ist = interview.started_at.astimezone(ist)
        end_ist = interview.ended_at.astimezone(ist)
        scheduled_time = start_ist.strftime("%B %d, %Y at %I:%M %p IST")
        end_time = end_ist.strftime("%I:%M %p IST")
        duration = f"{(interview.ended_at - interview.started_at).total_seconds() / 60:.0f} minutes"
    else:
        scheduled_time = "TBD"
        end_time = "TBD"
        duration = "TBD"
    
    # Get interview link
    interview_url = None
    session_key = None
    
    # Try to get session_key from Interview model
    if interview.session_key:
        session_key = interview.session_key
    else:
        # Try to get from InterviewSession
        try:
            from interview_app.models import InterviewSession
            session = InterviewSession.objects.filter(
                candidate_email=candidate_email,
                scheduled_at__isnull=False
            ).order_by('-created_at').first()
            if session:
                session_key = session.session_key
                interview.session_key = session_key
                interview.save(update_fields=['session_key'])
        except Exception as e:
            print(f"Warning: Could not fetch InterviewSession: {e}")
    
    # Generate URL using session_key
    if session_key:
        base_url = getattr(settings, "BACKEND_URL", "http://localhost:8000")
        interview_url = f"{base_url}/?session_key={session_key}"
    else:
        # Fallback: try interview.get_interview_url()
        try:
            interview_url = interview.get_interview_url()
            if interview_url and 'session_key=' in interview_url:
                session_key = interview_url.split('session_key=')[-1].split('&')[0]
        except Exception as e:
            print(f"Warning: Failed to get interview URL: {e}")
        
        # Final fallback
        if not interview_url:
            base_url = getattr(settings, "BACKEND_URL", "http://localhost:8000")
            interview_url = f"{base_url}/interview_app/?interview_id={interview.id}"
    
    # Create email subject and message
    subject = f"Interview Scheduled - {job_title} at {company_name}"
    
    message = f"""Dear {candidate_name},

Your interview has been scheduled successfully!

📋 **Interview Details:**
• Position: {job_title}
• Company: {company_name}
• Date & Time: {scheduled_time}
• End Time: {end_time}
• Duration: {duration}
• Interview Type: {interview.ai_interview_type.title() if interview.ai_interview_type else 'AI Interview'}

🔗 **Join Your Interview:**
Click the link below to join your interview at the scheduled time:
{interview_url}

⚠️ **Important Instructions:**
• Please join the interview 5-10 minutes before the scheduled time
• You can only access the interview link at the scheduled date and time
• The link will be active 15 minutes before the interview starts
• Make sure you have a stable internet connection and a quiet environment
• Ensure your camera and microphone are working properly
• Have a valid government-issued ID ready for verification

📧 **Contact Information:**
If you have any questions or need to reschedule, please contact your recruiter.

Best regards,
{company_name} Recruitment Team

---
This is an automated message. Please do not reply to this email.
"""
    
    # Use same email sending approach as test_email_sending_live.py
    email_backend = settings.EMAIL_BACKEND
    email_host = settings.EMAIL_HOST
    email_port = settings.EMAIL_PORT
    email_use_tls = settings.EMAIL_USE_TLS
    email_use_ssl = settings.EMAIL_USE_SSL
    email_user = settings.EMAIL_HOST_USER
    email_password = settings.EMAIL_HOST_PASSWORD
    default_from_email = settings.DEFAULT_FROM_EMAIL
    
    # Fix TLS/SSL conflict - for Gmail with port 587, use TLS only (same as test script)
    if email_port == 587 and email_use_tls and email_use_ssl:
        print("[WARNING] Both TLS and SSL are enabled. Disabling SSL for port 587 (TLS only)...")
        settings.EMAIL_USE_SSL = False
        email_use_ssl = False
    
    # Check configuration (same checks as test script)
    if "console" in email_backend.lower():
        print(f"[ERROR] EMAIL_BACKEND is set to console - email will not be sent to {candidate_email}!")
        return False
    
    if not email_host:
        print(f"[ERROR] EMAIL_HOST is not set!")
        return False
    
    if not email_user or not email_password:
        print(f"[ERROR] Email credentials not set!")
        return False
    
    # Final check for TLS/SSL conflict
    if email_use_tls and email_use_ssl:
        print(f"[ERROR] EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be True!")
        return False
    
    # Send email using same approach as test_email_sending_live.py
    try:
        print(f"\n📧 Sending interview email to: {candidate_email}")
        print(f"   Interview ID: {interview.id}")
        print(f"   Candidate: {candidate_name}")
        print(f"   Scheduled Time: {scheduled_time}")
        print(f"   Interview URL: {interview_url}")
        
        send_mail(
            subject=subject,
            message=message,
            from_email=default_from_email,
            recipient_list=[candidate_email],
            fail_silently=False,
        )
        print(f"[SUCCESS] Interview email sent successfully to {candidate_email}!")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email to {candidate_email}: {e}")
        print("\nPossible fixes:")
        print("1. Check EMAIL_HOST_PASSWORD - use Gmail App Password")
        print("2. Check EMAIL_HOST and EMAIL_PORT")
        print("3. Verify EMAIL_USE_TLS=True for port 587")
        return False

def main():
    """Main function to send emails to scheduled interviews"""
    print("\n" + "=" * 70)
    print("  Send Interview Emails to Candidates")
    print("=" * 70 + "\n")
    
    # Get all scheduled interviews
    scheduled_interviews = Interview.objects.filter(
        status='scheduled'
    ).select_related('candidate', 'job', 'schedule', 'schedule__slot')
    
    total = scheduled_interviews.count()
    print(f"Found {total} scheduled interview(s)\n")
    
    if total == 0:
        print("No scheduled interviews found.")
        return
    
    # Ask which interviews to send
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            # Send to all
            interviews_to_send = scheduled_interviews
        else:
            # Send to specific interview ID
            try:
                interview_id = sys.argv[1]
                interviews_to_send = scheduled_interviews.filter(id=interview_id)
            except:
                print(f"[ERROR] Invalid interview ID: {sys.argv[1]}")
                return
    else:
        # Interactive mode - show list and ask
        print("Scheduled Interviews:")
        for idx, interview in enumerate(scheduled_interviews, 1):
            candidate_email = interview.candidate.email
            print(f"  {idx}. Interview {interview.id} - {interview.candidate.full_name} ({candidate_email})")
        
        choice = input(f"\nSend emails to (1-{total} for specific, 'all' for all, 'q' to quit): ").strip().lower()
        
        if choice == 'q':
            print("Cancelled.")
            return
        elif choice == 'all':
            interviews_to_send = scheduled_interviews
        else:
            try:
                idx = int(choice) - 1
                interviews_to_send = [scheduled_interviews[idx]]
            except:
                print("[ERROR] Invalid choice.")
                return
    
    # Send emails
    sent_count = 0
    failed_count = 0
    
    for interview in interviews_to_send:
        candidate_email = interview.candidate.email
        candidate_name = interview.candidate.full_name
        
        if not candidate_email:
            print(f"\n[SKIPPED] Interview {interview.id} - No email for {candidate_name}")
            failed_count += 1
            continue
        
        if send_interview_email_to_candidate(interview):
            sent_count += 1
        else:
            failed_count += 1
        
        print()  # Blank line between emails
    
    # Summary
    print("=" * 70)
    print(f"\nSummary:")
    print(f"  Total: {total}")
    print(f"  Sent: {sent_count}")
    print(f"  Failed: {failed_count}")
    print()

if __name__ == "__main__":
    main()

