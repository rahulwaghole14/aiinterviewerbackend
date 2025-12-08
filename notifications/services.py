from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
from .models import (
    Notification,
    NotificationTemplate,
    UserNotificationPreference,
    NotificationType,
    NotificationChannel,
    NotificationPriority,
)
from utils.logger import ActionLogger
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """Service class for handling notifications"""

    @staticmethod
    def create_notification(
        recipient,
        notification_type,
        title,
        message,
        channels=None,
        priority=NotificationPriority.MEDIUM,
        metadata=None,
    ):
        """Create and send a notification"""
        try:
            # Get user notification preferences
            preferences, created = UserNotificationPreference.objects.get_or_create(
                user=recipient,
                defaults={
                    "email_enabled": True,
                    "in_app_enabled": True,
                    "sms_enabled": False,
                },
            )

            # Filter channels based on user preferences
            if channels is None:
                channels = preferences.get_enabled_channels()
            else:
                # Only use channels that user has enabled
                enabled_channels = preferences.get_enabled_channels()
                channels = [ch for ch in channels if ch in enabled_channels]

            # Check if user wants this type of notification
            if not NotificationService._should_send_notification(
                preferences, notification_type
            ):
                return None

            # Create notification
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                channels=channels,
                metadata=metadata or {},
            )

            # Send notification
            notification.send_notification()

            # Log the notification
            ActionLogger.log_user_action(
                user=recipient,
                action="notification_sent",
                details={
                    "notification_id": notification.id,
                    "type": notification_type,
                    "channels": channels,
                    "priority": priority,
                },
                status="SUCCESS",
            )

            return notification

        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            ActionLogger.log_user_action(
                user=recipient,
                action="notification_failed",
                details={"type": notification_type, "error": str(e)},
                status="FAILED",
            )
            return None

    @staticmethod
    def create_notification_from_template(
        recipient, template_name, context=None, channels=None, priority=None
    ):
        """Create notification using a template"""
        try:
            template = NotificationTemplate.objects.get(
                name=template_name, is_active=True
            )

            # Render template with context
            title, message = template.render_template(context or {})

            # Use template priority if not specified
            if priority is None:
                priority = template.priority

            # Use template channels if not specified
            if channels is None:
                channels = template.channels

            return NotificationService.create_notification(
                recipient=recipient,
                notification_type=template.notification_type,
                title=title,
                message=message,
                channels=channels,
                priority=priority,
                metadata={"template": template_name, "context": context},
            )

        except NotificationTemplate.DoesNotExist:
            logger.error(f"Notification template '{template_name}' not found")
            return None
        except Exception as e:
            logger.error(f"Error creating notification from template: {e}")
            return None

    @staticmethod
    def send_interview_scheduled_notification(interview, recipient=None):
        """Send notification when interview is scheduled"""
        if recipient is None:
            recipient = interview.candidate.recruiter

        context = {
            "candidate_name": interview.candidate.full_name,
            "job_title": interview.job.job_title if interview.job else "N/A",
            "interview_date": (
                interview.started_at.strftime("%B %d, %Y at %I:%M %p")
                if interview.started_at
                else "TBD"
            ),
            "company_name": interview.job.company_name if interview.job else "N/A",
        }

        return NotificationService.create_notification_from_template(
            recipient=recipient,
            template_name="interview_scheduled",
            context=context,
            priority=NotificationPriority.HIGH,
        )

    @staticmethod
    def send_candidate_interview_scheduled_notification(interview):
        """Send notification directly to candidate when interview is scheduled"""
        logger.info(f"📧 send_candidate_interview_scheduled_notification called for interview: {interview.id if interview else 'None'}")
        print(f"\n{'='*70}")
        print(f"[EMAIL DEBUG] send_candidate_interview_scheduled_notification called")
        print(f"  Interview ID: {interview.id if interview else 'None'}")
        print(f"{'='*70}\n")
        
        try:
            # CRITICAL: Validate interview has candidate before proceeding
            if not interview:
                logger.error("❌ Cannot send email: interview is None")
                print("[EMAIL FAILED] Interview is None")
                return False
            
            if not interview.candidate:
                logger.error(f"❌ Cannot send email: interview {interview.id} has no candidate")
                print(f"[EMAIL FAILED] Interview {interview.id} has no associated candidate")
                return False
            
            # Get interview details
            candidate_name = interview.candidate.full_name or "Candidate"
            candidate_email = interview.candidate.email
            
            # CRITICAL: Validate candidate email exists
            if not candidate_email or not candidate_email.strip():
                logger.error(f"❌ Cannot send email: candidate {interview.candidate.id} has no email address")
                print(f"[EMAIL FAILED] Candidate {interview.candidate.id} has no email address")
                return False

            # Try to get job information from multiple sources
            job_title = "Interview Position"
            company_name = "Company"

            # First try: direct interview job link
            if interview.job:
                job_title = interview.job.job_title or "Interview Position"
                company_name = interview.job.company_name or "Company"
            # Second try: job from slot
            elif (
                hasattr(interview, "schedule")
                and interview.schedule
                and interview.schedule.slot
                and hasattr(interview.schedule.slot, 'job')
                and interview.schedule.slot.job
            ):
                job_title = interview.schedule.slot.job.job_title or "Interview Position"
                company_name = interview.schedule.slot.job.company_name or "Company"
            # Third try: job from candidate
            elif interview.candidate and interview.candidate.job:
                job_title = interview.candidate.job.job_title or "Interview Position"
                company_name = interview.candidate.job.company_name or "Company"

            # Get comprehensive slot details
            slot_details = ""
            scheduled_time = "TBD"
            duration = "TBD"
            interview_type = "AI Interview"
            
            # CRITICAL: Always use interview.started_at/ended_at for time display - they are timezone-aware (stored in UTC)
            # Convert to IST (Asia/Kolkata) for display in emails
            import pytz
            ist = pytz.timezone('Asia/Kolkata')
            
            if interview.started_at and interview.ended_at:
                # Convert UTC to IST for display
                start_ist = interview.started_at.astimezone(ist)
                end_ist = interview.ended_at.astimezone(ist)
                
                scheduled_time = start_ist.strftime("%B %d, %Y at %I:%M %p IST")
                end_time = end_ist.strftime("%I:%M %p IST")
                duration = f"{(interview.ended_at - interview.started_at).total_seconds() / 60:.0f} minutes"
                interview_type = (
                    interview.ai_interview_type.title()
                    if interview.ai_interview_type
                    else "AI Interview"
                )
                
                # Get slot details if available for additional info
                if hasattr(interview, "schedule") and interview.schedule:
                    slot = interview.schedule.slot
                    slot_details = f"""
📅 **Detailed Schedule:**
• Start Time: {start_ist.strftime('%B %d, %Y at %I:%M %p IST')}
• End Time: {end_ist.strftime('%I:%M %p IST')}
• Duration: {slot.duration_minutes if slot else duration} minutes
• Interview Type: {slot.ai_interview_type.title() if slot and slot.ai_interview_type else interview_type}
• Time Zone: IST (Indian Standard Time)
"""
                else:
                    slot_details = ""
            elif hasattr(interview, "schedule") and interview.schedule:
                # Fallback: use slot times if started_at not available (shouldn't happen after booking)
                slot = interview.schedule.slot
                # Combine slot date + time and treat as IST
                start_datetime_naive = datetime.combine(slot.interview_date, slot.start_time)
                end_datetime_naive = datetime.combine(slot.interview_date, slot.end_time)
                start_dt = ist.localize(start_datetime_naive)
                end_dt = ist.localize(end_datetime_naive)
                
                scheduled_time = start_dt.strftime("%B %d, %Y at %I:%M %p IST")
                end_time = end_dt.strftime("%I:%M %p IST")
                duration = f"{slot.duration_minutes} minutes"
                interview_type = (
                    slot.ai_interview_type.title()
                    if slot.ai_interview_type
                    else "AI Interview"
                )

                slot_details = f"""
📅 **Detailed Schedule:**
• Start Time: {start_dt.strftime('%B %d, %Y at %I:%M %p IST')}
• End Time: {end_dt.strftime('%I:%M %p IST')}
• Duration: {slot.duration_minutes} minutes
• Interview Type: {interview_type}
• Time Zone: IST (Indian Standard Time)
"""

            # Set interview times from slot if not already set
            # IMPORTANT: Combine slot date + time to create proper DateTime objects
            # IMPORTANT: Interpret slot times in IST (Asia/Kolkata) since that's likely where users are
            if (
                hasattr(interview, "schedule")
                and interview.schedule
                and interview.schedule.slot
            ):
                slot = interview.schedule.slot
                # ALWAYS update interview times from slot, even if already set (in case of incorrect values)
                if slot.interview_date and slot.start_time:
                    # Combine date and time - assume slot times are in IST (India Standard Time)
                    import pytz
                    ist = pytz.timezone('Asia/Kolkata')
                    start_datetime_naive = datetime.combine(slot.interview_date, slot.start_time)
                    end_datetime_naive = datetime.combine(slot.interview_date, slot.end_time)
                    
                    # Localize to IST (treat slot times as IST)
                    start_datetime = ist.localize(start_datetime_naive)
                    end_datetime = ist.localize(end_datetime_naive)
                    
                    # Convert to UTC for storage (Django stores in UTC)
                    start_datetime_utc = start_datetime.astimezone(pytz.UTC)
                    end_datetime_utc = end_datetime.astimezone(pytz.UTC)
                    
                    interview.started_at = start_datetime_utc
                    interview.ended_at = end_datetime_utc
                    interview.save(update_fields=["started_at", "ended_at"])

            # Generate interview link if not already generated
            if not interview.interview_link:
                try:
                    interview_link = interview.generate_interview_link()
                    # Save the generated link
                    interview.interview_link = interview_link
                    interview.save(update_fields=["interview_link"])
                except Exception as e:
                    logger.error(f"Failed to generate interview link: {e}")
                    interview_link = None
            else:
                interview_link = interview.interview_link

            # Get the full interview URL - prioritize session_key from InterviewSession
            interview_url = None
            session_key = None
            
            # First, try to get session_key from Interview model
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
                    logger.warning(f"Could not fetch InterviewSession: {e}")
            
            # Generate URL using session_key - format must match interview_portal view
            if session_key:
                # Use BACKEND_URL from settings or fallback to localhost
                # CRITICAL: BACKEND_URL must be set in Render environment variables!
                base_url = getattr(settings, "BACKEND_URL", None)
                if not base_url or "localhost" in str(base_url).lower():
                    # Try to get from environment directly
                    import os
                    base_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
                    if "localhost" in base_url.lower():
                        logger.warning("⚠️ BACKEND_URL not set in Render! Using localhost. Add BACKEND_URL=https://aiinterviewerbackend-2.onrender.com to Render environment variables")
                        print(f"⚠️ WARNING: BACKEND_URL not set in Render environment variables!")
                        print(f"   Add BACKEND_URL=https://aiinterviewerbackend-2.onrender.com to Render → Environment")
                
                # Format: https://your-render-url.onrender.com/interview/?session_key=xxx
                # Use /interview/ route which is the actual interview portal
                interview_url = f"{base_url}/interview/?session_key={session_key}"
                logger.info(f"📧 Generated interview URL: {interview_url}")
                print(f"[EMAIL DEBUG] Generated interview URL: {interview_url}")
            else:
                # Fallback: try interview.get_interview_url()
                try:
                    interview_url = interview.get_interview_url()
                    if interview_url:
                        # Extract session_key from URL if possible
                        if 'session_key=' in interview_url:
                            session_key = interview_url.split('session_key=')[-1].split('&')[0]
                except Exception as e:
                    logger.warning(f"Failed to get interview URL: {e}")
                
                # Final fallback: use interview_link if available
                if not interview_url and interview.interview_link:
                    interview_url = interview.interview_link
                
                # Last resort: generate URL
                if not interview_url:
                    base_url = getattr(settings, "BACKEND_URL", "http://localhost:8000")
                    interview_url = f"{base_url}/interview_app/?interview_id={interview.id}"
                    logger.warning(f"Using fallback interview URL: {interview_url}")

            # Get booking notes if available
            booking_notes = ""
            if (
                hasattr(interview, "schedule")
                and interview.schedule
                and interview.schedule.booking_notes
            ):
                booking_notes = f"""
📝 **Additional Notes:**
{interview.schedule.booking_notes}
"""

            # Create email subject and message
            subject = f"Interview Scheduled - {job_title} at {company_name}"

            message = f"""
Dear {candidate_name},

Your interview has been scheduled successfully!

📋 **Interview Details:**
• Position: {job_title}
• Company: {company_name}
• Date & Time: {scheduled_time}
• Duration: {duration}
• Interview Type: {interview_type}

{slot_details}
🔗 **Join Your Interview:**
Click the link below to join your interview at the scheduled time:
{interview_url if interview_url != "Interview link will be provided separately" else "Your interview link will be sent separately."}

⚠️ **Important Instructions:**
• Please join the interview 5-10 minutes before the scheduled time
• You can only access the interview link at the scheduled date and time
• The link will be active 15 minutes before the interview starts
• Make sure you have a stable internet connection and a quiet environment
• Ensure your camera and microphone are working properly
• Have a valid government-issued ID ready for verification

{booking_notes}
📧 **Contact Information:**
If you have any questions or need to reschedule, please contact your recruiter.

Best regards,
{company_name} Recruitment Team

---
This is an automated message. Please do not reply to this email.
            """

            # Send email to candidate - Support both SendGrid and SMTP
            # Note: settings is already imported at the top of the file
            # Get email configuration from settings (loaded from .env)
            use_sendgrid = getattr(settings, 'USE_SENDGRID', False)
            sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', '')
            email_backend = settings.EMAIL_BACKEND
            email_host = settings.EMAIL_HOST
            email_port = settings.EMAIL_PORT
            email_use_tls = settings.EMAIL_USE_TLS
            email_use_ssl = settings.EMAIL_USE_SSL
            email_user = settings.EMAIL_HOST_USER
            email_password = settings.EMAIL_HOST_PASSWORD
            default_from_email = settings.DEFAULT_FROM_EMAIL
            
            # CRITICAL VALIDATION: Check if email configuration is complete
            if use_sendgrid:
                # Using SendGrid API
                if not sendgrid_api_key:
                    logger.error(
                        f"SENDGRID_API_KEY is not set - cannot send email to {candidate_email}. "
                        "Set SENDGRID_API_KEY in environment variables"
                    )
                    print(f"\n[EMAIL NOT SENT] SENDGRID_API_KEY is not set")
                    print(f"To fix: Set SENDGRID_API_KEY in Render environment variables")
                    return False
                logger.info(f"📧 Using SendGrid API for email sending")
                print(f"[EMAIL DEBUG] Using SendGrid API")
            else:
                # Using SMTP - validate SMTP configuration
                if not email_host or not email_user or not email_password:
                    logger.error(
                        f"❌ Email configuration incomplete. Cannot send email to {candidate_email}. "
                        f"EMAIL_HOST: {'SET' if email_host else 'NOT SET'}, "
                        f"EMAIL_HOST_USER: {'SET' if email_user else 'NOT SET'}, "
                        f"EMAIL_HOST_PASSWORD: {'SET' if email_password else 'NOT SET'}"
                    )
                    print(f"\n[EMAIL FAILED] Configuration incomplete:")
                    print(f"  EMAIL_HOST: {'SET' if email_host else 'NOT SET'}")
                    print(f"  EMAIL_HOST_USER: {'SET' if email_user else 'NOT SET'}")
                    print(f"  EMAIL_HOST_PASSWORD: {'SET' if email_password else 'NOT SET'}")
                    print(f"  Please configure these in .env file, or set USE_SENDGRID=True")
                    return False
                
                # CRITICAL: Fix TLS/SSL conflict - for Gmail with port 587, use TLS only
                # Same approach as test_email_sending_live.py - modify settings directly
                if email_port == 587 and email_use_tls and email_use_ssl:
                    logger.warning("Both TLS and SSL are enabled. Disabling SSL for port 587 (TLS only)...")
                    settings.EMAIL_USE_SSL = False
                    email_use_ssl = False
                    print("  EMAIL_USE_SSL set to: False (temporarily for this email)")
                
                # Final check for TLS/SSL conflict
                if email_use_tls and email_use_ssl:
                    logger.error("EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be True!")
                    print(f"\n[EMAIL NOT SENT] EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be True!")
                    print(f"To fix: For Gmail port 587, set EMAIL_USE_TLS=True and EMAIL_USE_SSL=False in .env")
                    return False

                # CRITICAL: Check email configuration BEFORE attempting to send (same checks as test script)
                if "console" in email_backend.lower():
                    logger.warning(
                        f"EMAIL_BACKEND is set to console - email will not be sent to {candidate_email}. "
                        "Update .env: EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend or USE_SENDGRID=True"
                    )
                    print(f"\n[EMAIL NOT SENT] EMAIL_BACKEND is 'console' - email would print to console only")
                    print(f"To fix: Set USE_SENDGRID=True and SENDGRID_API_KEY, or set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")
                    return False
                elif not email_host:
                    logger.error(
                        f"EMAIL_HOST is not set - cannot send email to {candidate_email}. "
                        "Update .env: EMAIL_HOST=smtp.gmail.com or USE_SENDGRID=True"
                    )
                    print(f"\n[EMAIL NOT SENT] EMAIL_HOST is not set")
                    print(f"To fix: Set USE_SENDGRID=True and SENDGRID_API_KEY, or set EMAIL_HOST=smtp.gmail.com")
                    return False
                elif not email_user or not email_password:
                    logger.error(
                        f"Email credentials incomplete - cannot send email to {candidate_email}. "
                        f"Missing: EMAIL_HOST_USER={bool(email_user)}, EMAIL_HOST_PASSWORD={bool(email_password)}"
                    )
                    print(f"\n[EMAIL NOT SENT] Email credentials incomplete")
                    print(f"To fix: Set USE_SENDGRID=True and SENDGRID_API_KEY, or set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
                    return False

            # Send email - Support both SendGrid and SMTP
            try:
                logger.info(f"Attempting to send interview notification email to {candidate_email}...")
                
                if use_sendgrid:
                    print(f"EMAIL: Configuration check (SendGrid):")
                    print(f"  EMAIL_BACKEND: {email_backend}")
                    print(f"  USE_SENDGRID: {use_sendgrid}")
                    print(f"  SENDGRID_API_KEY: {'SET' if sendgrid_api_key else 'NOT SET'}")
                    print(f"  DEFAULT_FROM_EMAIL: {default_from_email}")
                else:
                    print(f"EMAIL: Configuration check (SMTP):")
                    print(f"  EMAIL_BACKEND: {email_backend}")
                    print(f"  EMAIL_HOST: {email_host}")
                    print(f"  EMAIL_PORT: {email_port}")
                    print(f"  EMAIL_USE_TLS: {email_use_tls}")
                    print(f"  EMAIL_USE_SSL: {email_use_ssl}")
                    print(f"  EMAIL_HOST_USER: {email_user[:20] + '...' if email_user and len(email_user) > 20 else email_user}")
                    print(f"  EMAIL_HOST_PASSWORD: {'SET' if email_password else 'NOT SET'}")
                    print(f"  DEFAULT_FROM_EMAIL: {default_from_email}")
                
                print(f"EMAIL: Sending interview notification email")
                print(f"EMAIL: To: {candidate_email}")
                print(f"EMAIL: Subject: {subject}")
                print(f"EMAIL: Interview URL: {interview_url}")
                
                # Use DEFAULT_FROM_EMAIL (same as test_email_sending_live.py)
                from_email = default_from_email
                
                logger.info(f"📧 About to call send_mail() for {candidate_email}")
                print(f"[EMAIL DEBUG] About to call send_mail()")
                print(f"  From: {from_email}")
                print(f"  To: {candidate_email}")
                print(f"  Subject: {subject[:50]}...")
                print(f"  Backend: {email_backend}")
                print(f"  Host: {email_host}:{email_port}")
                print(f"  TLS: {email_use_tls}, SSL: {email_use_ssl}")
                
                # CRITICAL: Verify EMAIL_BACKEND is not console
                if "console" in str(email_backend).lower():
                    logger.error(f"❌ EMAIL_BACKEND is set to console - email will not be sent!")
                    print(f"\n[EMAIL FAILED] EMAIL_BACKEND is '{email_backend}'")
                    print(f"  This means emails will only print to console, not actually send")
                    print(f"  Fix: Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend in Render environment variables")
                    return False
                
                # Send email - Support both SendGrid and SMTP
                if use_sendgrid:
                    # Use SendGrid API (more reliable for cloud deployments)
                    try:
                        logger.info(f"📧 Sending email via SendGrid API...")
                        print(f"[EMAIL DEBUG] Sending via SendGrid API...")
                        print(f"  From: {from_email}")
                        print(f"  To: {candidate_email}")
                        print(f"  Subject: {subject[:50]}...")
                        
                        result = send_mail(
                            subject=subject,
                            message=message,
                            from_email=from_email,
                            recipient_list=[candidate_email],
                            fail_silently=False,
                        )
                        
                        if result:
                            logger.info(f"✅ Interview notification sent via SendGrid successfully: {candidate_email}")
                            print(f"\n[SUCCESS] Interview notification email sent successfully via SendGrid!")
                            print(f"  ✅ send_mail() returned: {result}")
                            print(f"  ✅ Recipient: {candidate_email}")
                            print(f"  ✅ Interview URL: {interview_url}")
                            print(f"  Check inbox for interview link!")
                            return True
                        else:
                            logger.warning(f"⚠️ send_mail() returned False (0) for {candidate_email}")
                            print(f"\n[EMAIL WARNING] send_mail() returned False")
                            print(f"  Recipient: {candidate_email}")
                            return False
                            
                    except Exception as sendgrid_error:
                        error_msg = str(sendgrid_error)
                        error_type = type(sendgrid_error).__name__
                        logger.error(f"❌ SendGrid email sending failed for {candidate_email}: {error_msg} (Type: {error_type})")
                        print(f"\n[EMAIL FAILED] SendGrid Error Type: {error_type}")
                        print(f"  Error Message: {error_msg}")
                        print(f"  Recipient: {candidate_email}")
                        print(f"  This usually means:")
                        print(f"  1. SENDGRID_API_KEY is invalid or expired")
                        print(f"  2. SendGrid account is suspended")
                        print(f"  3. From email is not verified in SendGrid")
                        import traceback
                        traceback.print_exc()
                        return False
                else:
                    # Use SMTP (Gmail, etc.)
                    import socket
                    import smtplib
                    from django.core.mail import get_connection
                    
                    original_timeout = socket.getdefaulttimeout()
                    socket.setdefaulttimeout(30)  # 30 second timeout for SMTP connection
                    
                    try:
                        # Log before attempting to send
                        logger.info(f"📧 Attempting SMTP connection to {email_host}:{email_port}")
                        print(f"[EMAIL DEBUG] Attempting SMTP connection...")
                        print(f"  Host: {email_host}:{email_port}")
                        print(f"  User: {email_user}")
                        print(f"  TLS: {email_use_tls}, SSL: {email_use_ssl}")
                        
                        # Try to get connection first to test connectivity
                        try:
                            connection = get_connection(
                                backend=email_backend,
                                host=email_host,
                                port=email_port,
                                username=email_user,
                                password=email_password,
                                use_tls=email_use_tls,
                                use_ssl=email_use_ssl,
                                fail_silently=False,
                            )
                            logger.info(f"📧 Connection object created successfully")
                            print(f"[EMAIL DEBUG] Connection object created")
                        except Exception as conn_error:
                            error_msg = str(conn_error)
                            error_type = type(conn_error).__name__
                            logger.error(f"❌ Failed to create email connection: {error_msg} (Type: {error_type})")
                            print(f"\n[EMAIL FAILED] Connection creation failed")
                            print(f"  Error Type: {error_type}")
                            print(f"  Error Message: {error_msg}")
                            import traceback
                            traceback.print_exc()
                            return False
                        
                        # Now try to send the email
                        logger.info(f"📧 Calling send_mail()...")
                        print(f"[EMAIL DEBUG] Calling send_mail()...")
                        
                        result = send_mail(
                            subject=subject,
                            message=message,
                            from_email=from_email,
                            recipient_list=[candidate_email],
                            connection=connection,
                            fail_silently=False,
                        )
                        
                        logger.info(f"📧 send_mail() completed, result: {result}")
                        print(f"[EMAIL DEBUG] send_mail() completed, result: {result}")
                        
                        if result:
                            logger.info(f"✅ Interview notification sent via email successfully: {candidate_email}")
                            print(f"\n[SUCCESS] Interview notification email sent successfully!")
                            print(f"  ✅ send_mail() returned: {result}")
                            print(f"  ✅ Recipient: {candidate_email}")
                            print(f"  ✅ Interview URL: {interview_url}")
                            print(f"  Check inbox for interview link!")
                            return True
                        else:
                            logger.warning(f"⚠️ send_mail() returned False (0) for {candidate_email}")
                            print(f"\n[EMAIL WARNING] send_mail() returned False")
                            print(f"  Recipient: {candidate_email}")
                            print(f"  This might indicate email was not sent")
                            return False
                            
                    except socket.timeout as timeout_err:
                        error_msg = f"SMTP connection timeout (>30 seconds): {str(timeout_err)}"
                        logger.error(f"❌ Email timeout for {candidate_email}: {error_msg}")
                        print(f"\n[EMAIL TIMEOUT] Connection to SMTP server timed out")
                        print(f"  Error: {str(timeout_err)}")
                        print(f"  This usually means:")
                        print(f"  1. SMTP server is slow or unreachable")
                        print(f"  2. Network issues on Render")
                        print(f"  3. Gmail is blocking the connection")
                        print(f"  Recipient: {candidate_email}")
                        import traceback
                        traceback.print_exc()
                        return False
                    except smtplib.SMTPAuthenticationError as auth_err:
                        error_msg = f"SMTP Authentication failed: {str(auth_err)}"
                        logger.error(f"❌ Email authentication failed for {candidate_email}: {error_msg}")
                        print(f"\n[EMAIL FAILED] Authentication Error")
                        print(f"  Error: {str(auth_err)}")
                        print(f"  This usually means:")
                        print(f"  1. EMAIL_HOST_PASSWORD is incorrect")
                        print(f"  2. Gmail App Password is not set correctly")
                        print(f"  3. 2-Step Verification is not enabled")
                        print(f"  Recipient: {candidate_email}")
                        import traceback
                        traceback.print_exc()
                        return False
                    except smtplib.SMTPConnectError as conn_err:
                        error_msg = f"SMTP Connection failed: {str(conn_err)}"
                        logger.error(f"❌ Email connection failed for {candidate_email}: {error_msg}")
                        print(f"\n[EMAIL FAILED] Connection Error")
                        print(f"  Error: {str(conn_err)}")
                        print(f"  This usually means:")
                        print(f"  1. Cannot reach SMTP server")
                        print(f"  2. Port {email_port} is blocked")
                        print(f"  3. Firewall/network issue")
                        print(f"  Recipient: {candidate_email}")
                        import traceback
                        traceback.print_exc()
                        return False
                    except Exception as smtp_error:
                        error_msg = str(smtp_error)
                        error_type = type(smtp_error).__name__
                        logger.error(f"❌ Email sending failed for {candidate_email}: {error_msg} (Type: {error_type})")
                        print(f"\n[EMAIL FAILED] Error Type: {error_type}")
                        print(f"  Error Message: {error_msg}")
                        print(f"  Recipient: {candidate_email}")
                        import traceback
                        traceback.print_exc()
                        return False
                    finally:
                        socket.setdefaulttimeout(original_timeout)  # Reset to original timeout
                        try:
                            if 'connection' in locals():
                                connection.close()
                                logger.info(f"📧 Email connection closed")
                        except:
                            pass
                
                # Also create an in-app notification for the recruiter
                try:
                    NotificationService.send_interview_scheduled_notification(interview)
                except Exception as notif_error:
                    logger.warning(f"Failed to send in-app notification: {notif_error}")
                
                return True
            except Exception as email_error:
                error_msg = str(email_error)
                error_type = type(email_error).__name__
                logger.error(
                    f"❌ SMTP email failed for {candidate_email}: {error_msg} (Type: {error_type})"
                )
                print(f"\n[EMAIL FAILED] Error sending email to {candidate_email}")
                print(f"Error Type: {error_type}")
                print(f"Error Message: {error_msg}")
                import traceback
                print(f"\nFull Traceback:")
                traceback.print_exc()
                
                # Provide helpful error messages (same as test script)
                if "authentication" in error_msg.lower() or "535" in error_msg:
                    logger.error(
                        "⚠️  Authentication failed - Check EMAIL_HOST_PASSWORD. "
                        "For Gmail, use an App Password (not your regular password). "
                        "Generate at: https://myaccount.google.com/apppasswords"
                    )
                    print("\nPossible fixes:")
                    print("1. Check EMAIL_HOST_PASSWORD - use Gmail App Password, not regular password")
                    print("2. Generate new App Password at: https://myaccount.google.com/apppasswords")
                elif "connection" in error_msg.lower() or "timed out" in error_msg.lower():
                    logger.error(
                        "⚠️  Connection failed - Check EMAIL_HOST and EMAIL_PORT. "
                        "For Gmail: smtp.gmail.com:587 with TLS"
                    )
                    print("\nPossible fixes:")
                    print("1. Check EMAIL_HOST and EMAIL_PORT in .env")
                    print("2. Verify EMAIL_USE_TLS=True for port 587")
                    print("3. Check internet connection and firewall settings")
                else:
                    print("\nPossible fixes:")
                    print("1. Verify all email settings in .env file")
                    print("2. Check EMAIL_HOST_PASSWORD - use Gmail App Password")
                    print("3. Ensure EMAIL_USE_TLS=True for port 587")
                
                # Don't fallback - fail explicitly so user knows
                return False

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Failed to send candidate interview notification: {error_msg}")
            print(f"\n[EMAIL FAILED] Exception in send_candidate_interview_scheduled_notification:")
            print(f"  Error: {error_msg}")
            print(f"  Interview ID: {interview.id if interview else 'N/A'}")
            print(f"  Candidate: {interview.candidate.id if interview and interview.candidate else 'N/A'}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def send_resume_processed_notification(resume, recipient=None):
        """Send notification when resume is processed"""
        if recipient is None:
            recipient = resume.user

        context = {
            "filename": resume.file.name.split("/")[-1],
            "extracted_data": (
                resume.parsed_text[:100] + "..."
                if resume.parsed_text
                else "No text extracted"
            ),
        }

        return NotificationService.create_notification_from_template(
            recipient=recipient,
            template_name="resume_processed",
            context=context,
            priority=NotificationPriority.MEDIUM,
        )

    @staticmethod
    def send_bulk_upload_completed_notification(user, results):
        """Send notification for bulk resume upload completion"""
        try:
            summary = results.get("summary", {})
            total_files = summary.get("total_files", 0)
            successful = summary.get("successful", 0)
            failed = summary.get("failed", 0)

            message = (
                f"Bulk resume upload completed: {successful}/{total_files} successful"
            )
            if failed > 0:
                message += f", {failed} failed"

            NotificationService.create_notification(
                user=user,
                notification_type="BULK_UPLOAD_COMPLETED",
                title="Bulk Resume Upload Completed",
                message=message,
                details={
                    "total_files": total_files,
                    "successful": successful,
                    "failed": failed,
                    "results": results.get("results", []),
                },
            )
        except Exception as e:
            logger.error(f"Failed to send bulk upload notification: {e}")

    @staticmethod
    def send_bulk_candidate_creation_notification(user, successful_count, domain, role):
        """Send notification for bulk candidate creation completion"""
        try:
            message = f"Bulk candidate creation completed: {successful_count} candidates created for {domain}/{role}"

            NotificationService.create_notification(
                user=user,
                notification_type="BULK_CANDIDATE_CREATION_COMPLETED",
                title="Bulk Candidate Creation Completed",
                message=message,
                details={
                    "successful_count": successful_count,
                    "domain": domain,
                    "role": role,
                },
            )
        except Exception as e:
            logger.error(f"Failed to send bulk candidate creation notification: {e}")

    @staticmethod
    def send_candidate_added_notification(candidate, recipient=None):
        """Send notification when candidate is added"""
        if recipient is None:
            recipient = candidate.recruiter

        context = {
            "candidate_name": candidate.full_name,
            "candidate_email": candidate.email,
            "domain": candidate.domain,
        }

        return NotificationService.create_notification_from_template(
            recipient=recipient,
            template_name="candidate_added",
            context=context,
            priority=NotificationPriority.MEDIUM,
        )

    @staticmethod
    def send_job_created_notification(job, recipient=None):
        """Send notification when job is created"""
        if recipient is None:
            # Send to all hiring agencies under the company
            from hiring_agency.models import UserData

            recipients = UserData.objects.filter(company_name=job.company_name)
        else:
            recipients = [recipient]

        context = {
            "job_title": job.job_title,
            "company_name": job.company_name,
            "position_level": job.position_level,
            "number_to_hire": job.number_to_hire,
        }

        notifications = []
        for recipient in recipients:
            notification = NotificationService.create_notification_from_template(
                recipient=recipient.user,
                template_name="job_created",
                context=context,
                priority=NotificationPriority.MEDIUM,
            )
            if notification:
                notifications.append(notification)

        return notifications

    @staticmethod
    def send_interview_reminder_notification(interview):
        """Send reminder notification for upcoming interview"""
        context = {
            "candidate_name": interview.candidate.full_name,
            "interview_date": (
                interview.started_at.strftime("%B %d, %Y at %I:%M %p")
                if interview.started_at
                else "TBD"
            ),
            "job_title": interview.job.job_title if interview.job else "N/A",
        }

        # Send to both candidate's recruiter and candidate (if they have an account)
        recipients = [interview.candidate.recruiter]
        if hasattr(interview.candidate, "user") and interview.candidate.user:
            recipients.append(interview.candidate.user)

        notifications = []
        for recipient in recipients:
            notification = NotificationService.create_notification_from_template(
                recipient=recipient,
                template_name="interview_reminder",
                context=context,
                priority=NotificationPriority.HIGH,
            )
            if notification:
                notifications.append(notification)

        return notifications

    @staticmethod
    def mark_notification_as_read(notification_id, user):
        """Mark a notification as read"""
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.mark_as_read()

            ActionLogger.log_user_action(
                user=user,
                action="notification_read",
                details={"notification_id": notification_id},
                status="SUCCESS",
            )

            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    def get_unread_notifications_count(user):
        """Get count of unread notifications for user"""
        return Notification.objects.filter(
            recipient=user, status__in=["pending", "sent"]
        ).count()

    @staticmethod
    def _should_send_notification(preferences, notification_type):
        """Check if user wants to receive this type of notification"""
        if notification_type in [
            NotificationType.INTERVIEW_SCHEDULED,
            NotificationType.INTERVIEW_REMINDER,
        ]:
            return preferences.interview_notifications
        elif notification_type in [
            NotificationType.RESUME_PROCESSED,
            NotificationType.BULK_UPLOAD_COMPLETED,
        ]:
            return preferences.resume_notifications
        elif notification_type == NotificationType.SYSTEM_ALERT:
            return preferences.system_notifications
        else:
            return True  # Default to sending other types
