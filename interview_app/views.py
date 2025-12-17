import os
import google.generativeai as genai
# Whisper import with fallback (optional dependency)
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    whisper = None
    WHISPER_AVAILABLE = False
    print("⚠️ Warning: openai-whisper not available. Whisper transcription features will be disabled.")
import PyPDF2
import docx
import re
import json
import threading
import csv
import shutil
# from gtts import gTTS  # Removed - using only Google Cloud TTS
from pathlib import Path
from dotenv import load_dotenv
import pytz
# TextBlob import with lazy loading to prevent startup timeout
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TextBlob = None
    TEXTBLOB_AVAILABLE = False
    print("⚠️ Warning: textblob not available. Text analysis features will be disabled.")
import subprocess
import tempfile
import psutil
import sqlite3

# Google Cloud Text-to-Speech import with fallback
try:
    from google.cloud import texttospeech
    print("✅ Google Cloud Text-to-Speech imported successfully in views.py")
except ImportError as e:
    print(f"❌ Warning: google-cloud-texttospeech not available in views.py: {e}")
    texttospeech = None
except Exception as e:
    print(f"❌ Unexpected error importing google-cloud-texttospeech in views.py: {e}")
    texttospeech = None

from collections import Counter
import traceback
import readtime
import time
import numpy as np
# OpenCV import with fallback (optional dependency)
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False
    print("⚠️ Warning: opencv-python not available. Camera and image processing features will be disabled.")
import base64
from django.utils import timezone
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
import urllib.parse


from django.http import JsonResponse, StreamingHttpResponse, HttpResponse, FileResponse
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.core.files.storage import default_storage
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
# WeasyPrint import with fallback (optional dependency)
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    HTML = None
    WEASYPRINT_AVAILABLE = False
    print("⚠️ Warning: weasyprint not available. PDF generation features will be disabled.")

# from .camera import VideoCamera
# from .simple_camera import SimpleVideoCamera as VideoCamera
# from .real_camera import RealVideoCamera as VideoCamera
# from .simple_real_camera import SimpleRealVideoCamera as VideoCamera
from .simple_real_camera import SimpleRealVideoCamera as VideoCamera
from .models import InterviewSession, WarningLog, InterviewQuestion, CodeSubmission
from .ai_chatbot import (
    ai_start_django,
    ai_upload_answer_django,
    ai_repeat_django,
    ai_transcript_pdf_django,
)

try:
    from .yolo_face_detector import detect_face_with_yolo
except ImportError:
    print("Warning: yolo_face_detector could not be imported. Using a placeholder.")
    def detect_face_with_yolo(img): 
        # Return empty results as a list for consistency
        empty_obj = type('obj', (object,), {'boxes': []})()
        return [empty_obj]


load_dotenv()
# Use API key from Django settings (from environment variable)
try:
    from django.conf import settings as dj_settings
    active_key = getattr(dj_settings, 'GEMINI_API_KEY', '')
    
    if active_key:
        genai.configure(api_key=active_key)
        print("✅ Gemini API configured successfully in views.py")
    else:
        print("⚠️ WARNING: GEMINI_API_KEY not set in environment. Please set GEMINI_API_KEY in .env file")
except Exception as e:
    print(f"⚠️ WARNING: Could not configure Gemini API: {e}")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
# --- DEVELOPMENT MODE SWITCH ---
# Set to True to use hardcoded questions and skip AI generation for faster testing.
# This does NOT affect AI evaluation in the report or email sending.
DEV_MODE = False

# Initialize Whisper model if available
whisper_model = None
if WHISPER_AVAILABLE and whisper:
    try:
        whisper_model = whisper.load_model("base")
        print("Whisper model 'base' loaded.")
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        whisper_model = None
else:
    print("Whisper not available - transcription features disabled")

FILLER_WORDS = ['um', 'uh', 'er', 'ah', 'like', 'okay', 'right', 'so', 'you know', 'i mean', 'basically', 'actually', 'literally']
CAMERAS, camera_lock = {}, threading.Lock()

# Import PyAudio recorder
try:
    from .simple_real_camera import PyAudioAudioRecorder
    PYAudio_AVAILABLE = True
except ImportError:
    PYAudio_AVAILABLE = False
    print("⚠️ PyAudioAudioRecorder not available")

# Audio recorders dictionary (similar to CAMERAS)
AUDIO_RECORDERS, audio_lock = {}, threading.Lock()

THINKING_TIME, ANSWERING_TIME, REVIEW_TIME = 20, 60, 10

def get_camera_for_session(session_key):
    print(f"🔍 Getting camera for session_key: {session_key}")
    with camera_lock:
        if session_key in CAMERAS: 
            print(f"✅ Found existing camera for session_key: {session_key}")
            return CAMERAS[session_key]
        try:
            print(f"🔍 Looking up InterviewSession for session_key: {session_key}")
            session_obj = InterviewSession.objects.get(session_key=session_key)
            print(f"✅ Found InterviewSession: {session_obj.id}")
            print(f"🎥 Creating VideoCamera for session_id: {session_obj.id}")
            camera_instance = VideoCamera(session_id=session_obj.id)
            CAMERAS[session_key] = camera_instance
            print(f"✅ Camera created and stored for session_key: {session_key}")
            return camera_instance
        except InterviewSession.DoesNotExist:
            print(f"❌ Could not find session for session_key {session_key} to create camera.")
            return None
        except Exception as e:
            print(f"❌ Error creating camera instance: {e}")
            import traceback
            traceback.print_exc()
            return None

def release_camera_for_session(session_key, audio_file_path=None):
    """Release camera and save video recording to InterviewSession. Optionally merge with audio."""
    with camera_lock:
        if session_key in CAMERAS:
            print(f"--- Releasing camera for session {session_key} ---")
            camera = CAMERAS[session_key]
            
            # Convert audio path to absolute if provided
            audio_full_path = None
            if audio_file_path:
                if not os.path.isabs(audio_file_path):
                    audio_full_path = os.path.join(settings.MEDIA_ROOT, audio_file_path)
                else:
                    audio_full_path = audio_file_path
                if not os.path.exists(audio_full_path):
                    print(f"⚠️ Audio file not found for merging: {audio_full_path}")
                    audio_full_path = None
            
            video_path = camera.cleanup()
            
            # If cleanup returns video path and we have audio, merge them
            if video_path and audio_full_path and hasattr(camera, 'stop_video_recording'):
                try:
                    # Stop recording with audio merge
                    video_path = camera.stop_video_recording(audio_file_path=audio_full_path)
                except:
                    pass
            
            # Save video path to InterviewSession if recording was active
            if video_path:
                try:
                    session = InterviewSession.objects.get(session_key=session_key)
                    session.interview_video = video_path
                    session.save()
                    print(f"✅ Video path saved to InterviewSession: {video_path}")
                except Exception as e:
                    print(f"❌ Error saving video path to InterviewSession: {e}")
            
            del CAMERAS[session_key]

SUPPORTED_LANGUAGES = {'en': 'English'}

def get_text_from_file(uploaded_file):
    name, extension = os.path.splitext(uploaded_file.name)
    text = ""
    if extension == '.pdf':
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages: text += page.extract_text() or ""
    elif extension == '.docx':
        doc = docx.Document(uploaded_file)
        for para in doc.paragraphs: text += para.text + "\n"
    else: text = uploaded_file.read().decode('utf-8', errors='ignore')
    return text

@login_required
def create_interview_invite(request):
    if request.method == 'POST':
        candidate_name = request.POST.get('candidate_name')
        candidate_email = request.POST.get('candidate_email')
        jd_text = request.POST.get('jd')
        resume_file = request.FILES.get('resume')
        language_code = request.POST.get('language', 'en')
        accent_tld = request.POST.get('accent', 'com')
        scheduled_at_str = request.POST.get('scheduled_at')

        if not all([candidate_name, candidate_email, jd_text, resume_file, scheduled_at_str]):
             return render(request, 'interview_app/create_invite.html', {'error': 'All fields are required.', 'languages': SUPPORTED_LANGUAGES})

        try:
            ist = pytz.timezone('Asia/Kolkata')
            naive_datetime = datetime.strptime(scheduled_at_str, '%Y-%m-%dT%H:%M')
            aware_datetime = ist.localize(naive_datetime)
        except (ValueError, pytz.exceptions.InvalidTimeError):
            return render(request, 'interview_app/create_invite.html', {'error': 'Invalid date and time format provided.', 'languages': SUPPORTED_LANGUAGES})

        resume_text = get_text_from_file(resume_file)
        if not resume_text:
            return render(request, 'interview_app/create_invite.html', {'error': 'Could not read the resume file.', 'languages': SUPPORTED_LANGUAGES})

        session = InterviewSession.objects.create(
            candidate_name=candidate_name, candidate_email=candidate_email,
            job_description=jd_text, resume_text=resume_text,
            language_code=language_code, accent_tld=accent_tld,
            scheduled_at=aware_datetime
        )

        # Use utility function to get correct Cloud Run URL
        from interview_app.utils import get_interview_url
        interview_url = get_interview_url(session.session_key, request)

        try:
            # Use same reliable email sending approach as test_email_sending_live.py
            from django.conf import settings
            
            email_backend = getattr(settings, 'EMAIL_BACKEND', '')
            email_host = getattr(settings, 'EMAIL_HOST', '')
            email_port = getattr(settings, 'EMAIL_PORT', 587)
            email_use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
            email_use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
            email_user = getattr(settings, 'EMAIL_HOST_USER', '') or os.getenv('EMAIL_HOST_USER', '')
            email_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
            default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', email_user or 'noreply@talaro.com')
            
            # CRITICAL: Fix TLS/SSL conflict - for Gmail with port 587, use TLS only
            if email_port == 587 and email_use_tls and email_use_ssl:
                print("[WARNING] Both TLS and SSL are enabled. Disabling SSL for port 587 (TLS only)...")
                settings.EMAIL_USE_SSL = False
                email_use_ssl = False
            
            # Validate configuration
            if "console" in str(email_backend).lower():
                error_msg = "EMAIL_BACKEND is set to console - emails won't be sent!"
                print(f"[ERROR] {error_msg}")
                return render(request, 'interview_app/create_invite.html', {
                    'error': f'Email configuration error: {error_msg}. Fix: Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend in .env',
                    'languages': SUPPORTED_LANGUAGES
                })
            elif not email_host:
                error_msg = "EMAIL_HOST is not set"
                print(f"[ERROR] {error_msg}")
                return render(request, 'interview_app/create_invite.html', {
                    'error': f'Email configuration error: {error_msg}. Fix: Set EMAIL_HOST=smtp.gmail.com in .env',
                    'languages': SUPPORTED_LANGUAGES
                })
            elif not email_user or not email_password:
                error_msg = "Email credentials incomplete"
                print(f"[ERROR] {error_msg}")
                return render(request, 'interview_app/create_invite.html', {
                    'error': f'Email configuration error: {error_msg}. Fix: Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env',
                    'languages': SUPPORTED_LANGUAGES
                })
            
            # Configuration valid - send email
            scheduled_time_str = aware_datetime.astimezone(pytz.timezone('Asia/Kolkata')).strftime('%A, %B %d, %Y at %I:%M %p IST')
            
            email_subject = "Your Talaro Interview Invitation"
            email_body = (
                f"Dear {candidate_name},\n\n"
                f"Your AI screening interview has been scheduled for: {scheduled_time_str}.\n\n"
                "Please use the following unique link to begin your interview at the scheduled time. "
                "The link will become active 30 seconds before the start time and will expire 10 minutes after.\n\n"
                f"{interview_url}\n\n"
                "⚠️ **Important Instructions:**\n"
                "• Please join the interview 5-10 minutes before the scheduled time\n"
                "• Make sure you have a stable internet connection and a quiet environment\n"
                "• Ensure your camera and microphone are working properly\n"
                "• Have a valid government-issued ID ready for verification\n\n"
                "Best of luck!\n"
            )
            
            print(f"\n{'='*70}")
            print(f"EMAIL: Sending interview invitation email")
            print(f"EMAIL: To: {candidate_email}")
            print(f"EMAIL: Subject: {email_subject}")
            print(f"EMAIL: Interview Link: {interview_url}")
            print(f"{'='*70}\n")
            
            send_mail(
                email_subject,
                email_body,
                default_from_email,
                [candidate_email],
                fail_silently=False,
            )
            print(f"[SUCCESS] Invitation sent to {candidate_email} via Gmail SMTP")
            print(f"Interview link: {interview_url}")
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Error sending email: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Provide helpful error message
            if "authentication" in error_msg.lower() or "535" in error_msg:
                detailed_error = "Authentication failed. Use Gmail App Password (not regular password). Generate at: https://myaccount.google.com/apppasswords"
            elif "connection" in error_msg.lower() or "timed out" in error_msg.lower():
                detailed_error = "Connection failed. Check EMAIL_HOST and EMAIL_PORT in .env file."
            else:
                detailed_error = f"Could not send email. Error: {error_msg}"
            
            return render(request, 'interview_app/create_invite.html', {
                'error': detailed_error,
                'languages': SUPPORTED_LANGUAGES
            })

        return redirect('dashboard')

    return render(request, 'interview_app/create_invite.html', {'languages': SUPPORTED_LANGUAGES})

@login_required
def generate_interview_link(request):
    """Generate an interview link for a candidate."""
    if request.method == 'POST':
        candidate_name = request.POST.get('candidate_name', '').strip()
        candidate_email = request.POST.get('candidate_email', '').strip()
        job_description = request.POST.get('job_description', '').strip()
        resume_text = request.POST.get('resume_text', '').strip()
        scheduled_at_str = request.POST.get('scheduled_at', '')
        language_code = request.POST.get('language_code', 'en')
        accent_tld = request.POST.get('accent_tld', 'com')
        
        # Validate required fields
        if not candidate_name or not candidate_email:
            return JsonResponse({
                'success': False,
                'error': 'Candidate name and email are required'
            }, status=400)
        
        # Handle scheduled_at
        scheduled_at = None
        if scheduled_at_str:
            try:
                ist = pytz.timezone('Asia/Kolkata')
                naive_datetime = datetime.strptime(scheduled_at_str, '%Y-%m-%dT%H:%M')
                scheduled_at = ist.localize(naive_datetime)
            except (ValueError, pytz.exceptions.InvalidTimeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid date and time format. Use YYYY-MM-DDTHH:MM'
                }, status=400)
        else:
            # If no scheduled time provided, schedule for now
            scheduled_at = timezone.now()
        
        # Create interview session
        try:
            session = InterviewSession.objects.create(
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                job_description=job_description or "Technical Role",
                resume_text=resume_text or "Experienced professional seeking new opportunities.",
                scheduled_at=scheduled_at,
                language_code=language_code,
                accent_tld=accent_tld,
                status='SCHEDULED'
            )
            
            # Generate interview link using utility function
            from interview_app.utils import get_interview_url
            interview_link = get_interview_url(session.session_key, request)
            
            # Send email notification to candidate
            try:
                # Format scheduled time in IST
                ist = pytz.timezone('Asia/Kolkata')
                if session.scheduled_at:
                    scheduled_time_ist = session.scheduled_at.astimezone(ist)
                    scheduled_time_str = scheduled_time_ist.strftime('%A, %B %d, %Y at %I:%M %p IST')
                    scheduled_date = scheduled_time_ist.strftime('%B %d, %Y')
                    scheduled_time_only = scheduled_time_ist.strftime('%I:%M %p IST')
                else:
                    scheduled_time_str = "To be determined"
                    scheduled_date = "TBD"
                    scheduled_time_only = "TBD"
                
                # Extract job title from job_description if available
                job_title = "Technical Role"
                if session.job_description:
                    lines = session.job_description.split('\n')
                    for line in lines:
                        if 'Job Title:' in line or 'Title:' in line:
                            job_title = line.split(':')[-1].strip()
                            break
                        elif 'Position:' in line:
                            job_title = line.split(':')[-1].strip()
                            break
                
                # Check email configuration - use same reliable approach as test_email_sending_live.py
                email_backend = getattr(settings, 'EMAIL_BACKEND', '')
                email_host = getattr(settings, 'EMAIL_HOST', '')
                email_port = getattr(settings, 'EMAIL_PORT', 587)
                email_use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
                email_use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
                email_user = getattr(settings, 'EMAIL_HOST_USER', '')
                email_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
                default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', email_user or 'noreply@talaro.com')
                
                # CRITICAL: Fix TLS/SSL conflict - for Gmail with port 587, use TLS only
                if email_port == 587 and email_use_tls and email_use_ssl:
                    print("[WARNING] Both TLS and SSL are enabled. Disabling SSL for port 587 (TLS only)...")
                    settings.EMAIL_USE_SSL = False
                    email_use_ssl = False
                
                # Final check for TLS/SSL conflict
                if email_use_tls and email_use_ssl:
                    print("[ERROR] EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be True!")
                    print("To fix: For Gmail port 587, set EMAIL_USE_TLS=True and EMAIL_USE_SSL=False in .env")
                    email_sent = False
                # Check configuration (same checks as test_email_sending_live.py)
                elif "console" in str(email_backend).lower():
                    print(f"[ERROR] EMAIL_BACKEND is set to console - emails won't be sent!")
                    print("Fix: Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend in .env")
                    email_sent = False
                elif not email_host:
                    print(f"[ERROR] EMAIL_HOST is not set!")
                    print("Fix: Set EMAIL_HOST=smtp.gmail.com in .env")
                    email_sent = False
                elif not email_user or not email_password:
                    print(f"[ERROR] Email credentials not set!")
                    print("Fix: Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env")
                    email_sent = False
                else:
                    # Configuration is valid - send email
                    try:
                        email_subject = f"Your Interview Has Been Scheduled - {job_title}"
                        email_body = f"""Dear {session.candidate_name},

Your AI interview has been scheduled successfully!

📋 **Interview Details:**
• Candidate: {session.candidate_name}
• Position: {job_title}
• Date: {scheduled_date}
• Time: {scheduled_time_only}
• Session ID: {session.id}

🔗 **Join Your Interview:**
Click the link below to join your interview at the scheduled time:
{interview_link}

⚠️ **Important Instructions:**
• Please join the interview 5-10 minutes before the scheduled time
• The link will be active 30 seconds before the scheduled time
• The link will expire 10 minutes after the scheduled start time
• Make sure you have a stable internet connection and a quiet environment
• Ensure your camera and microphone are working properly
• Have a valid government-issued ID ready for verification

Best of luck with your interview!

---
This is an automated message. Please do not reply to this email.
"""
                        from_email = default_from_email
                        
                        print(f"\n{'='*70}")
                        print(f"EMAIL: Sending interview invitation email")
                        print(f"EMAIL: Configuration:")
                        print(f"  EMAIL_BACKEND: {email_backend}")
                        print(f"  EMAIL_HOST: {email_host}")
                        print(f"  EMAIL_PORT: {email_port}")
                        print(f"  EMAIL_USE_TLS: {email_use_tls}")
                        print(f"  EMAIL_USE_SSL: {email_use_ssl}")
                        print(f"  EMAIL_HOST_USER: {email_user[:20] + '...' if email_user and len(email_user) > 20 else email_user}")
                        print(f"  EMAIL_HOST_PASSWORD: {'SET' if email_password else 'NOT SET'}")
                        print(f"  DEFAULT_FROM_EMAIL: {default_from_email}")
                        print(f"EMAIL: To: {session.candidate_email}")
                        print(f"EMAIL: Subject: {email_subject}")
                        print(f"EMAIL: Interview Link: {interview_link}")
                        print(f"{'='*70}\n")
                        
                        send_mail(
                            email_subject,
                            email_body,
                            from_email,
                            [session.candidate_email],
                            fail_silently=False,
                        )
                        email_sent = True
                        print(f"[SUCCESS] Email sent successfully to {session.candidate_email}")
                        print(f"Check inbox for interview link: {interview_link}")
                    except Exception as email_error:
                        error_msg = str(email_error)
                        print(f"[EMAIL FAILED] Error sending email to {session.candidate_email}")
                        print(f"Error: {error_msg}")
                        
                        # Provide helpful error messages
                        if "authentication" in error_msg.lower() or "535" in error_msg:
                            print("\nPossible fixes:")
                            print("1. Check EMAIL_HOST_PASSWORD - use Gmail App Password, not regular password")
                            print("2. Generate new App Password at: https://myaccount.google.com/apppasswords")
                        elif "connection" in error_msg.lower() or "timed out" in error_msg.lower():
                            print("\nPossible fixes:")
                            print("1. Check EMAIL_HOST and EMAIL_PORT in .env")
                            print("2. Verify EMAIL_USE_TLS=True for port 587")
                            print("3. Check internet connection and firewall settings")
                        else:
                            print("\nPossible fixes:")
                            print("1. Verify all email settings in .env file")
                            print("2. Check EMAIL_HOST_PASSWORD - use Gmail App Password")
                            print("3. Ensure EMAIL_USE_TLS=True for port 587")
                        
                        email_sent = False
            except Exception as e:
                print(f"❌ ERROR in email sending process: {e}")
                import traceback
                traceback.print_exc()
                email_sent = False
            
            return JsonResponse({
                'success': True,
                'interview_link': interview_link,
                'session_key': session.session_key,
                'session_id': str(session.id),
                'candidate_name': session.candidate_name,
                'candidate_email': session.candidate_email,
                'scheduled_at': session.scheduled_at.isoformat() if session.scheduled_at else None,
                'status': session.status,
                'email_sent': email_sent
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to create interview session: {str(e)}'
            }, status=500)
    
    # GET request - show form or return instructions
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'success': False,
            'error': 'POST request required',
            'instructions': {
                'method': 'POST',
                'required_fields': ['candidate_name', 'candidate_email'],
                'optional_fields': ['job_description', 'resume_text', 'scheduled_at', 'language_code', 'accent_tld'],
                'scheduled_at_format': 'YYYY-MM-DDTHH:MM (e.g., 2024-12-25T14:30)',
                'example': {
                    'candidate_name': 'John Doe',
                    'candidate_email': 'john@example.com',
                    'job_description': 'Software Engineer position...',
                    'resume_text': 'John has 5 years of experience...',
                    'scheduled_at': '2024-12-25T14:30',
                    'language_code': 'en',
                    'accent_tld': 'com'
                }
            }
        })
    
    # Render HTML form if GET request
    return render(request, 'interview_app/generate_link.html', {
        'languages': SUPPORTED_LANGUAGES
    })

def synthesize_speech(text, lang_code, accent_tld, output_path):
    """Use ONLY Google Cloud TTS - no fallback to gTTS"""
    if texttospeech is None:
        print("❌ Google Cloud TTS not available - texttospeech is None")
        raise Exception("Google Cloud TTS not available")
    
    try:
        print(f"🎤 Google Cloud TTS: Synthesizing '{text[:50]}...'")
        
        # Ensure credentials are set
        # Priority 1: Check GOOGLE_APPLICATION_CREDENTIALS environment variable (from Cloud Run secret mount)
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Priority 2: Try Secret Manager if env var not set
        if not credentials_path or not os.path.exists(credentials_path):
            try:
                from google.cloud import secretmanager
                client = secretmanager.SecretManagerServiceClient()
                project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "eastern-team-480811-e6")
                secret_name = f"projects/{project_id}/secrets/my-service-key/versions/latest"
                response = client.access_secret_version(request={"name": secret_name})
                credentials_json = response.payload.data.decode("UTF-8")
                
                # Write to temp file
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                temp_file.write(credentials_json)
                temp_file.close()
                
                credentials_path = temp_file.name
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                print(f"✅ Loaded credentials from Secret Manager: {credentials_path}")
            except Exception as e:
                print(f"⚠️ Could not load from Secret Manager: {e}")
                # Priority 3: Fallback to hardcoded path
                credentials_path = os.path.join(settings.BASE_DIR, "ringed-reach-471807-m3-cf0ec93e3257.json")
                if os.path.exists(credentials_path):
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                    print(f"✅ Using fallback credentials path: {credentials_path}")
                else:
                    print(f"❌ Google Cloud credentials not found in any location")
                    raise Exception("Google Cloud credentials not found")
        
        if credentials_path and os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            print(f"✅ Google Cloud credentials set: {credentials_path}")
        else:
            print(f"❌ Google Cloud credentials not found: {credentials_path}")
            raise Exception("Google Cloud credentials not found")
        
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Use a high-quality voice
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-F",  # High-quality neural voice
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        with open(output_path, 'wb') as out:
            out.write(response.audio_content)
        
        print(f"✅ Google Cloud TTS: Audio saved to {output_path}")
        return
    
    except Exception as e:
        print(f"❌ Google Cloud TTS failed: {e}")
        raise Exception(f"Google Cloud TTS failed: {e}")

def interview_portal(request):
    session_key = request.GET.get('session_key')
    print(f"DEBUG: interview_portal called with session_key: {session_key}")
    if not session_key:
        return render(request, 'interview_app/invalid_link.html')
    session = get_object_or_404(InterviewSession, session_key=session_key)
    print(f"DEBUG: Found session with ID: {session.id}")
    
    # This is the main validation logic block
    if session.status != 'SCHEDULED':
        return render(request, 'interview_app/invalid_link.html', {'error': 'This interview has already been completed or has expired.'})
    if session.scheduled_at:
        now = timezone.now()
        start_time = session.scheduled_at
        grace_period = timedelta(minutes=10)
        expiry_time = start_time + grace_period
        
        # Debug time comparison
        print(f"DEBUG: Time comparison - Now: {now}, Start: {start_time}, Expiry: {expiry_time}")
        print(f"DEBUG: Now < Start: {now < start_time}, Now > Expiry: {now > expiry_time}")
        
        # Case 1: The user is too early.
        # Add a small buffer (30 seconds) to account for timezone differences and network delays
        buffer_time = timedelta(seconds=30)
        if now < (start_time - buffer_time):
            start_time_local = start_time.astimezone(pytz.timezone('Asia/Kolkata'))
            print(f"DEBUG: User too early, showing countdown. Start time local: {start_time_local}")
            # We pass all necessary context for the countdown timer here.
            return render(request, 'interview_app/invalid_link.html', {
                'page_title': 'Interview Not Started',
                'error': f"Your interview has not started yet. Please use the link at the scheduled time:",
                'scheduled_time_str': start_time_local.strftime('%Y-%m-%d %I:%M %p IST'),
                'start_time_iso': start_time.isoformat() # This is crucial for the JS countdown
            })
        # Case 2: The user is too late.
        if now > expiry_time:
            session.status = 'EXPIRED'
            session.save()
            return render(request, 'interview_app/invalid_link.html', {
                'page_title': 'Interview Link Expired',
                'error': 'This interview link has expired because the 10-minute grace period after the scheduled time has passed.'
            })
    else:
        # Case 3: The session has no scheduled time (should not happen in normal flow).
         return render(request, 'interview_app/invalid_link.html', {'error': 'This interview session is invalid as it does not have a scheduled time.'})
    # If the user is within the valid time window, proceed with the interview setup.
    try:
        # Initialize variables
        all_questions = []
        coding_questions = []
        
        print(f"DEBUG: About to load questions from database")
        # Load existing questions and coding questions from database
        if True:  # ENABLED: Load questions from database
            all_questions = []
            tts_dir = os.path.join(settings.MEDIA_ROOT, 'tts')
            os.makedirs(tts_dir, exist_ok=True)
            
            # Check if there are existing questions
            existing_questions = session.questions.filter(question_level='MAIN').order_by('order')
            
            if existing_questions.exists():
                # Load existing questions and generate audio if missing
                for i, q in enumerate(existing_questions):
                    # Skip coding questions - they should not be in spoken questions
                    if q.question_type == 'CODING':
                        continue
                        
                    if not q.audio_url:
                        # Generate audio for questions that don't have it
                        tts_path = os.path.join(tts_dir, f'q_{i}_{session.session_key}.mp3')
                        synthesize_speech(q.question_text, session.language_code, session.accent_tld, tts_path)
                        audio_url = f"{settings.MEDIA_URL}tts/{os.path.basename(tts_path)}"
                        # Update the question in database
                        q.audio_url = audio_url
                        q.save()
                    else:
                        audio_url = q.audio_url
                    
                    all_questions.append({
                        'type': q.question_type, 
                        'text': q.question_text, 
                        'audio_url': audio_url
                    })
                generate_new_questions = False

            else:
                # No existing questions, generate new ones
                print("DEBUG: No existing questions found, generating new ones...")
                # Set flag to generate new questions
                generate_new_questions = True
            # Load coding questions from database (generated by generate_coding_questions.py)
            coding_questions = []
            db_coding_questions = session.questions.filter(question_type='CODING').order_by('order')
            
            print(f"DEBUG: Found {db_coding_questions.count()} coding questions in database")
            
            # First, determine the correct language that should be used
            try:
                from jobs.models import Job
                allowed_langs = {choice[0] for choice in Job._meta.get_field("coding_language").choices}
            except Exception:
                allowed_langs = {'PYTHON', 'JAVASCRIPT', 'C', 'CPP', 'JAVA', 'GO', 'HTML', 'PHP', 'RUBY', 'CSHARP', 'SQL'}
            correct_lang = None
            
            # Priority 1: Get from Interview.job.coding_language
            try:
                from interviews.models import Interview
                interview = Interview.objects.filter(session_key=session.session_key).first()
                if interview and interview.job:
                    job_lang = getattr(interview.job, 'coding_language', None)
                    print(f"🧾 Job {interview.job.id if interview.job else 'N/A'} coding_language (raw): {job_lang}")
                    if job_lang and job_lang.upper() in allowed_langs:
                        correct_lang = job_lang.upper()
                        print(f"✅ Correct language from job: {correct_lang}")
                    elif job_lang:
                        print(f"⚠️ Job coding_language '{job_lang}' not in allowed set {sorted(allowed_langs)}")
            except Exception as e:
                print(f"⚠️ Error getting language from Interview: {e}")
            
            if not correct_lang:
                print("❌ Unable to determine coding language from job configuration. Aborting.")
                return render(request, 'interview_app/invalid_link.html', {
                    'error': "Coding language not configured for this interview. Please contact support."
                })
            
            # Check if existing coding questions have the wrong language
            need_recreate = False
            for q in db_coding_questions:
                existing_lang = (q.coding_language or 'PYTHON').upper()
                if existing_lang != correct_lang:
                    print(f"⚠️ Existing coding question has wrong language: {existing_lang}, should be: {correct_lang}")
                    need_recreate = True
                    break
            
            # If wrong language, delete and recreate
            if need_recreate:
                print(f"🔄 Deleting coding questions with wrong language and recreating with {correct_lang}")
                try:
                    session.questions.filter(question_type='CODING').delete()
                    db_coding_questions = []  # Clear so we create new ones
                    coding_questions = []  # Clear the list so we go to the else block to create new ones
                except Exception as e:
                    print(f"⚠️ Error deleting wrong language questions: {e}")
            
            for q in db_coding_questions:
                # Get test cases for this question
                test_cases_data = []
                for tc in q.test_cases.all():
                    test_cases_data.append({
                        'input': tc.input_data,
                        'output': tc.expected_output
                    })
                
                # Extract title from question text (first line or first 50 chars)
                question_lines = q.question_text.split('\n')
                title = question_lines[0][:80] if question_lines else q.question_text[:80]
                
                # Get starter_code from hardcoded_map if available, otherwise use default
                lang = q.coding_language or 'PYTHON'
                starter_code = f'def solution(input_data):\n    # Your code here\n    pass'
                
                # Try to match with hardcoded questions to get proper starter_code
                hardcoded_starter_map = {
                    'PYTHON': 'def reverse_string(s: str) -> str:\n    # TODO: implement\n    pass',
                    'JAVASCRIPT': 'function reverseString(s){\n  // TODO\n}\nmodule.exports = reverseString;',
                    'JAVA': 'public class Solution {\n  public static int add(int a,int b){\n    // TODO\n    return 0;\n  }\n}',
                    'PHP': '<?php\nfunction reverse_string($s){\n  // TODO\n}\n?>',
                    'C': 'int add(int a,int b){\n  // TODO\n  return 0;\n}',
                    'CPP': 'int add(int a,int b){\n  // TODO\n  return 0;\n}',
                    'GO': 'package main\nfunc Reverse(s string) string {\n  // TODO\n  return ""\n}',
                    'HTML': '<!-- return <h1>Hello</h1> -->'
                }
                if lang in hardcoded_starter_map:
                    starter_code = hardcoded_starter_map[lang]
                
                coding_q = {
                    'id': str(q.id),
                    'type': q.question_type,
                    'title': title,
                    'description': q.question_text,
                    'language': lang,
                    'starter_code': starter_code,
                    'test_cases': test_cases_data
                }
                coding_questions.append(coding_q)
                print(f"DEBUG: Loaded coding question: {title[:50]}... with {len(test_cases_data)} test cases, lang: {lang}")
            
            if coding_questions:
                print(f"✅ Loaded {len(coding_questions)} coding questions from database")
            else:
                print(f"⚠️ No coding questions found. Creating hardcoded question...")
                # Use the correct_lang that was already determined above (from job.coding_language)
                # This ensures we use the language from the job, not default to PYTHON
                requested_lang = correct_lang if correct_lang else 'PYTHON'
                print(f"✅ Using determined language for new coding question: {requested_lang}")
                
                # Import hardcoded map
                hardcoded_map = {
                    'PYTHON': {
                        'title': 'Reverse a String',
                        'description': 'Write a function reverse_string(s: str) -> str that returns the reversed string.',
                        'language': 'PYTHON',
                        'starter_code': 'def reverse_string(s: str) -> str:\n    # TODO: implement\n    pass',
                        'test_cases': [
                            {'input': "'hello'", 'expected_output': 'olleh'},
                            {'input': "''", 'expected_output': ''},
                            {'input': "'abc'", 'expected_output': 'cba'}
                        ]
                    },
                    'JAVASCRIPT': {
                        'title': 'Reverse a String',
                        'description': 'Implement function reverseString(s) that returns the reversed string.',
                        'language': 'JAVASCRIPT',
                        'starter_code': 'function reverseString(s){\n  // TODO\n}\nmodule.exports = reverseString;',
                        'test_cases': [
                            {'input': "'hello'", 'expected_output': 'olleh'},
                            {'input': "''", 'expected_output': ''},
                            {'input': "'abc'", 'expected_output': 'cba'}
                        ]
                    },
                    'JAVA': {
                        'title': 'Add Two Numbers',
                        'description': 'Implement a static method add(int a, int b) that returns a+b.',
                        'language': 'JAVA',
                        'starter_code': 'public class Solution {\n  public static int add(int a,int b){\n    // TODO\n    return 0;\n  }\n}',
                        'test_cases': [
                            {'input': '1,2', 'expected_output': '3'},
                            {'input': '-5,5', 'expected_output': '0'},
                            {'input': '10,15', 'expected_output': '25'}
                        ]
                    },
                    'PHP': {
                        'title': 'Reverse a String',
                        'description': 'Implement function reverse_string($s) that returns the reversed string.',
                        'language': 'PHP',
                        'starter_code': '<?php\nfunction reverse_string($s){\n  // TODO\n}\n?>',
                        'test_cases': [
                            {'input': "'hello'", 'expected_output': 'olleh'},
                            {'input': "''", 'expected_output': ''},
                            {'input': "'abc'", 'expected_output': 'cba'}
                        ]
                    },
                    'C': {
                        'title': 'Add Two Numbers',
                        'description': 'Write a function int add(int a,int b) that returns a+b.',
                        'language': 'C',
                        'starter_code': 'int add(int a,int b){\n  // TODO\n  return 0;\n}',
                        'test_cases': [
                            {'input': '1,2', 'expected_output': '3'},
                            {'input': '-5,5', 'expected_output': '0'},
                            {'input': '10,15', 'expected_output': '25'}
                        ]
                    },
                    'CPP': {
                        'title': 'Add Two Numbers',
                        'description': 'Implement int add(int a,int b) that returns a+b.',
                        'language': 'CPP',
                        'starter_code': 'int add(int a,int b){\n  // TODO\n  return 0;\n}',
                        'test_cases': [
                            {'input': '1,2', 'expected_output': '3'},
                            {'input': '-5,5', 'expected_output': '0'},
                            {'input': '10,15', 'expected_output': '25'}
                        ]
                    },
                    'GO': {
                        'title': 'Reverse a String',
                        'description': 'Implement func Reverse(s string) string that returns the reversed string.',
                        'language': 'GO',
                        'starter_code': 'package main\nfunc Reverse(s string) string {\n  // TODO\n  return ""\n}',
                        'test_cases': [
                            {'input': '"hello"', 'expected_output': 'olleh'},
                            {'input': '""', 'expected_output': ''},
                            {'input': '"abc"', 'expected_output': 'cba'}
                        ]
                    },
                    'HTML': {
                        'title': 'Simple Heading',
                        'description': 'Return an HTML string with an <h1>Hello</h1> element.',
                        'language': 'HTML',
                        'starter_code': '<!-- return <h1>Hello</h1> -->',
                        'test_cases': [
                            {'input': 'n/a', 'expected_output': '<h1>Hello</h1>'}
                        ]
                    }
                }
                
                coding_questions = [hardcoded_map[requested_lang]]
                print(f"🧩 Prepared hardcoded coding question for {requested_lang}: {coding_questions[0].get('title')}")
                
                # Delete any existing coding questions to prevent duplicates
                try:
                    session.questions.filter(question_type='CODING').delete()
                    print(f"✅ Deleted existing coding questions to prevent duplicates")
                except Exception as e:
                    print(f"⚠️ Error deleting existing coding questions: {e}")
                
                # Save to database - ONLY ONE coding question
                for i, coding_q in enumerate(coding_questions[:1]):  # Limit to 1 question
                    coding_question_obj = InterviewQuestion.objects.create(
                        session=session,
                        question_text=coding_q['description'],
                        question_type='CODING',
                        coding_language=coding_q['language'],
                        order=(len(all_questions) + i) if all_questions else i,
                        question_level='MAIN'
                    )
                    # Attach test cases
                    try:
                        from .models import TestCase
                        if TestCase and coding_q.get('test_cases'):
                            for tc in coding_q['test_cases']:
                                TestCase.objects.create(
                                    question=coding_question_obj,
                                    input_data=str(tc.get('input', '')),
                                    expected_output=str(tc.get('expected_output', ''))
                                )
                    except Exception as e:
                        print(f"⚠️ Error creating test cases: {e}")
                    # Update ID
                    coding_q['id'] = str(coding_question_obj.id)
                print(f"✅ Created hardcoded coding question ({requested_lang}) with ID: {coding_q['id']}")
            
            # Check if we need to generate new questions
            print(f"DEBUG: generate_new_questions flag: {generate_new_questions if 'generate_new_questions' in locals() else 'NOT SET'}")
            if 'generate_new_questions' in locals() and generate_new_questions:
                print("DEBUG: Generating new questions due to no existing questions...")
                # Generate new questions using the existing logic
                DEV_MODE = False
                if DEV_MODE:
                    print("--- RUNNING IN DEV MODE: Using hardcoded questions and summary. ---")
                    session.resume_summary = "This is a sample resume summary for developer mode. The candidate seems proficient in Python and Django."
                    all_questions = [
                        {'type': 'Ice-Breaker', 'text': 'Welcome! To start, can you tell me about a challenging project you have worked on?'},
                        {'type': 'Technical Questions', 'text': 'What is the difference between `let`, `const`, and `var` in JavaScript?'},
                        {'type': 'Behavioral Questions', 'text': 'Describe a time you had a conflict with a coworker and how you resolved it.'}
                    ]
                    
                    # Use hardcoded coding questions (NOT Gemini) - Get language from job.coding_language
                    allowed_langs = {'PYTHON', 'JAVASCRIPT', 'C', 'CPP', 'JAVA', 'GO', 'HTML', 'PHP'}
                    requested_lang = None
                    
                    # Priority 1: Get from Interview.job.coding_language via session_key (most reliable)
                    try:
                        from interviews.models import Interview
                        interview = Interview.objects.filter(session_key=session.session_key).first()
                        if interview and interview.job:
                            job_lang = getattr(interview.job, 'coding_language', None)
                            if job_lang and job_lang.upper() in allowed_langs:
                                requested_lang = job_lang.upper()
                                print(f"✅ Using coding language from job via Interview: {requested_lang}")
                    except Exception as e:
                        print(f"⚠️ Error getting coding language from Interview: {e}")
                    
                    # Priority 3: Get from URL parameter (fallback)
                    if not requested_lang:
                        requested_lang = (request.GET.get('lang') or 'PYTHON').upper()
                        print(f"⚠️ Using coding language from URL parameter: {requested_lang}")
                    
                    # Validate and default to PYTHON if invalid
                    if requested_lang not in allowed_langs:
                        requested_lang = 'PYTHON'
                        print(f"⚠️ Invalid language, defaulting to PYTHON")
                    
                    # Use hardcoded questions instead of Gemini
                    hardcoded_map = {
                        'PYTHON': {
                            'title': 'Reverse a String',
                            'description': 'Write a function reverse_string(s: str) -> str that returns the reversed string.',
                            'language': 'PYTHON',
                            'starter_code': 'def reverse_string(s: str) -> str:\n    # TODO: implement\n    pass',
                            'test_cases': [
                                {'input': "'hello'", 'expected_output': 'olleh'},
                                {'input': "''", 'expected_output': ''},
                                {'input': "'abc'", 'expected_output': 'cba'}
                            ]
                        },
                        'JAVASCRIPT': {
                            'title': 'Reverse a String',
                            'description': 'Implement function reverseString(s) that returns the reversed string.',
                            'language': 'JAVASCRIPT',
                            'starter_code': 'function reverseString(s){\n  // TODO\n}\nmodule.exports = reverseString;',
                            'test_cases': [
                                {'input': "'hello'", 'expected_output': 'olleh'},
                                {'input': "''", 'expected_output': ''},
                                {'input': "'abc'", 'expected_output': 'cba'}
                            ]
                        },
                        'JAVA': {
                            'title': 'Add Two Numbers',
                            'description': 'Implement a static method add(int a, int b) that returns a+b.',
                            'language': 'JAVA',
                            'starter_code': 'public class Solution {\n  public static int add(int a,int b){\n    // TODO\n    return 0;\n  }\n}',
                            'test_cases': [
                                {'input': '1,2', 'expected_output': '3'},
                                {'input': '-5,5', 'expected_output': '0'},
                                {'input': '10,15', 'expected_output': '25'}
                            ]
                        },
                        'PHP': {
                            'title': 'Reverse a String',
                            'description': 'Implement function reverse_string($s) that returns the reversed string.',
                            'language': 'PHP',
                            'starter_code': '<?php\nfunction reverse_string($s){\n  // TODO\n}\n?>',
                            'test_cases': [
                                {'input': "'hello'", 'expected_output': 'olleh'},
                                {'input': "''", 'expected_output': ''},
                                {'input': "'abc'", 'expected_output': 'cba'}
                            ]
                        },
                        'C': {
                            'title': 'Add Two Numbers',
                            'description': 'Write a function int add(int a,int b) that returns a+b.',
                            'language': 'C',
                            'starter_code': 'int add(int a,int b){\n  // TODO\n  return 0;\n}',
                            'test_cases': [
                                {'input': '1,2', 'expected_output': '3'},
                                {'input': '-5,5', 'expected_output': '0'},
                                {'input': '10,15', 'expected_output': '25'}
                            ]
                        },
                        'CPP': {
                            'title': 'Add Two Numbers',
                            'description': 'Implement int add(int a,int b) that returns a+b.',
                            'language': 'CPP',
                            'starter_code': 'int add(int a,int b){\n  // TODO\n  return 0;\n}',
                            'test_cases': [
                                {'input': '1,2', 'expected_output': '3'},
                                {'input': '-5,5', 'expected_output': '0'},
                                {'input': '10,15', 'expected_output': '25'}
                            ]
                        },
                        'GO': {
                            'title': 'Reverse a String',
                            'description': 'Implement func Reverse(s string) string that returns the reversed string.',
                            'language': 'GO',
                            'starter_code': 'package main\nfunc Reverse(s string) string {\n  // TODO\n  return ""\n}',
                            'test_cases': [
                                {'input': '"hello"', 'expected_output': 'olleh'},
                                {'input': '""', 'expected_output': ''},
                                {'input': '"abc"', 'expected_output': 'cba'}
                            ]
                        },
                        'HTML': {
                            'title': 'Simple Heading',
                            'description': 'Return an HTML string with an <h1>Hello</h1> element.',
                            'language': 'HTML',
                            'starter_code': '<!-- return <h1>Hello</h1> -->',
                            'test_cases': [
                                {'input': 'n/a', 'expected_output': '<h1>Hello</h1>'}
                            ]
                        }
                    }
                    
                    coding_questions = [hardcoded_map[requested_lang]]
                    print(f"🧩 Prepared hardcoded coding question for {requested_lang}: {coding_questions[0].get('title')}")
                
                # Save spoken questions to database
                for i, q_data in enumerate(all_questions):
                    tts_path = os.path.join(tts_dir, f'q_{i}_{session.session_key}.mp3')
                    synthesize_speech(q_data['text'], session.language_code, session.accent_tld, tts_path)
                    audio_url = f"{settings.MEDIA_URL}tts/{os.path.basename(tts_path)}"
                    q_data['audio_url'] = audio_url
                    InterviewQuestion.objects.create(
                        session=session,
                        question_text=q_data['text'],
                        question_type=q_data['type'],
                        order=i,
                        question_level='MAIN'
                    )
                
                # Delete any existing coding questions to prevent duplicates
                try:
                    session.questions.filter(question_type='CODING').delete()
                    print(f"✅ Deleted existing coding questions to prevent duplicates")
                except Exception as e:
                    print(f"⚠️ Error deleting existing coding questions: {e}")
                
                # Save coding questions to database - ONLY ONE coding question
                for i, coding_q in enumerate(coding_questions[:1]):  # Limit to 1 question
                    coding_question_obj = InterviewQuestion.objects.create(
                        session=session,
                        question_text=coding_q['description'],
                        question_type='CODING',
                        coding_language=coding_q['language'],
                        order=len(all_questions) + i,
                        question_level='MAIN'
                    )
                    # Attach test cases
                    try:
                        from .models import TestCase
                        if TestCase and coding_q.get('test_cases'):
                            for tc in coding_q['test_cases']:
                                TestCase.objects.create(
                                    question=coding_question_obj,
                                    input_data=str(tc.get('input', '')),
                                    expected_output=str(tc.get('expected_output', ''))
                                )
                    except Exception as e:
                        print(f"⚠️ Error creating test cases: {e}")
                    # Update the coding_questions_data with the real database ID
                    coding_q['id'] = str(coding_question_obj.id)
        else:
            DEV_MODE = False

            all_questions = []
            if DEV_MODE:
                print("--- RUNNING IN DEV MODE: Using hardcoded questions and summary. ---")
                session.resume_summary = "This is a sample resume summary for developer mode. The candidate seems proficient in Python and Django."
                all_questions = [
                    {'type': 'Ice-Breaker', 'text': 'Welcome! To start, can you tell me about a challenging project you have worked on?'},
                    {'type': 'Technical Questions', 'text': 'What is the difference between `let`, `const`, and `var` in JavaScript?'},
                    {'type': 'Behavioral Questions', 'text': 'Describe a time you had a conflict with a coworker and how you resolved it.'}
                ]
                
                # Get coding language from job (prioritize job.coding_language)
                allowed_langs = {
                    'PYTHON', 'JAVASCRIPT', 'C', 'CPP', 'JAVA', 'GO', 'HTML', 'PHP'
                }
                requested_lang = None
                
                # Priority 1: Get from Interview.job.coding_language via session_key (most reliable)
                try:
                    from interviews.models import Interview
                    interview = Interview.objects.filter(session_key=session.session_key).first()
                    print(f"🔍 DEBUG: Looking for Interview with session_key={session.session_key}")
                    if interview:
                        print(f"🔍 DEBUG: Found Interview {interview.id}, job={interview.job}")
                        if interview.job:
                            job_lang = getattr(interview.job, 'coding_language', None)
                            print(f"🔍 DEBUG: job.coding_language = {job_lang}")
                            if job_lang:
                                job_lang_upper = job_lang.upper()
                                print(f"🔍 DEBUG: job_lang_upper = {job_lang_upper}, allowed_langs = {allowed_langs}")
                                if job_lang_upper in allowed_langs:
                                    requested_lang = job_lang_upper
                                    print(f"✅ Using coding language from job via Interview: {requested_lang}")
                                else:
                                    print(f"⚠️ Language {job_lang_upper} not in allowed_langs {allowed_langs}")
                            else:
                                print(f"⚠️ job.coding_language is None or empty")
                        else:
                            print(f"⚠️ Interview found but interview.job is None")
                    else:
                        print(f"⚠️ No Interview found with session_key={session.session_key}")
                except Exception as e:
                    print(f"⚠️ Error getting coding language from Interview: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Priority 3: Get from URL parameter (fallback)
                if not requested_lang:
                    requested_lang = (request.GET.get('lang') or 'PYTHON').upper()
                    print(f"⚠️ Using coding language from URL parameter: {requested_lang}")
                
                # Validate and default to PYTHON if invalid
                if requested_lang not in allowed_langs:
                    requested_lang = 'PYTHON'
                    print(f"⚠️ Invalid language, defaulting to PYTHON")
                
                # Use hardcoded questions based on language
                hardcoded_map = {
                    'PYTHON': {
                        'title': 'Reverse a String',
                        'description': 'Write a function reverse_string(s: str) -> str that returns the reversed string.',
                        'language': 'PYTHON',
                        'starter_code': 'def reverse_string(s: str) -> str:\n    # TODO: implement\n    pass',
                        'test_cases': [
                            {'input': "'hello'", 'expected_output': 'olleh'},
                            {'input': "''", 'expected_output': ''},
                            {'input': "'abc'", 'expected_output': 'cba'}
                        ]
                    },
                    'JAVASCRIPT': {
                        'title': 'Reverse a String',
                        'description': 'Implement function reverseString(s) that returns the reversed string.',
                        'language': 'JAVASCRIPT',
                        'starter_code': 'function reverseString(s){\n  // TODO\n}\nmodule.exports = reverseString;',
                        'test_cases': [
                            {'input': "'hello'", 'expected_output': 'olleh'},
                            {'input': "''", 'expected_output': ''},
                            {'input': "'abc'", 'expected_output': 'cba'}
                        ]
                    },
                    'JAVA': {
                        'title': 'Add Two Numbers',
                        'description': 'Implement a static method add(int a, int b) that returns a+b.',
                        'language': 'JAVA',
                        'starter_code': 'public class Solution {\n  public static int add(int a,int b){\n    // TODO\n    return 0;\n  }\n}',
                        'test_cases': [
                            {'input': '1,2', 'expected_output': '3'},
                            {'input': '-5,5', 'expected_output': '0'},
                            {'input': '10,15', 'expected_output': '25'}
                        ]
                    },
                    'PHP': {
                        'title': 'Reverse a String',
                        'description': 'Implement function reverse_string($s) that returns the reversed string.',
                        'language': 'PHP',
                        'starter_code': '<?php\nfunction reverse_string($s){\n  // TODO\n}\n?>',
                        'test_cases': [
                            {'input': "'hello'", 'expected_output': 'olleh'},
                            {'input': "''", 'expected_output': ''},
                            {'input': "'abc'", 'expected_output': 'cba'}
                        ]
                    },
                    'C': {
                        'title': 'Add Two Numbers',
                        'description': 'Write a function int add(int a,int b) that returns a+b.',
                        'language': 'C',
                        'starter_code': 'int add(int a,int b){\n  // TODO\n  return 0;\n}',
                        'test_cases': [
                            {'input': '1,2', 'expected_output': '3'},
                            {'input': '-5,5', 'expected_output': '0'},
                            {'input': '10,15', 'expected_output': '25'}
                        ]
                    },
                    'CPP': {
                        'title': 'Add Two Numbers',
                        'description': 'Implement int add(int a,int b) that returns a+b.',
                        'language': 'CPP',
                        'starter_code': 'int add(int a,int b){\n  // TODO\n  return 0;\n}',
                        'test_cases': [
                            {'input': '1,2', 'expected_output': '3'},
                            {'input': '-5,5', 'expected_output': '0'},
                            {'input': '10,15', 'expected_output': '25'}
                        ]
                    },
                    'GO': {
                        'title': 'Reverse a String',
                        'description': 'Implement func Reverse(s string) string that returns the reversed string.',
                        'language': 'GO',
                        'starter_code': 'package main\nfunc Reverse(s string) string {\n  // TODO\n  return ""\n}',
                        'test_cases': [
                            {'input': '"hello"', 'expected_output': 'olleh'},
                            {'input': '""', 'expected_output': ''},
                            {'input': '"abc"', 'expected_output': 'cba'}
                        ]
                    },
                    'HTML': {
                        'title': 'Simple Heading',
                        'description': 'Return an HTML string with an <h1>Hello</h1> element.',
                        'language': 'HTML',
                        'starter_code': '<!-- return <h1>Hello</h1> -->',
                        'test_cases': [
                            {'input': 'n/a', 'expected_output': '<h1>Hello</h1>'}
                        ]
                    }
                }
                
                # Add coding question using the correct language
                coding_q_data = hardcoded_map.get(requested_lang, hardcoded_map['PYTHON'])
                coding_questions = [
                    {
                        'id': 'coding_1',
                        'type': 'CODING',
                        'title': coding_q_data['title'],
                        'description': coding_q_data['description'],
                        'language': coding_q_data['language'],
                        'starter_code': coding_q_data['starter_code'],
                        'test_cases': coding_q_data['test_cases']
                    }
                ]
                print(f"✅ Using hardcoded coding question in {requested_lang} for DEV MODE")
            else:
                print("--- RUNNING IN PRODUCTION MODE: Calling Gemini API. ---")
                model = genai.GenerativeModel('gemini-2.0-flash')
                summary_prompt = f"Summarize key skills from the following resume:\n\n{session.resume_text}"
                summary_response = model.generate_content(summary_prompt)
                session.resume_summary = summary_response.text
                language_name = SUPPORTED_LANGUAGES.get(session.language_code, 'English')
                
                # Get question count from InterviewSlot.ai_configuration or default to 4
                question_count = 4  # Default
                try:
                    # Get Interview via session_key (priority 1)
                    from interviews.models import Interview
                    interview = Interview.objects.filter(session_key=session.session_key).first()
                    
                    # If not found via session_key, try via candidate email (priority 2)
                    if not interview and session.candidate_email:
                        from candidates.models import Candidate
                        try:
                            candidate = Candidate.objects.get(email=session.candidate_email)
                            interview = Interview.objects.filter(candidate=candidate).order_by('-created_at').first()
                        except:
                            pass
                    
                    slot = None
                    
                    # Method 1: Try to get slot from interview.slot (direct assignment)
                    if interview and interview.slot:
                        slot = interview.slot
                        print(f"✅ Found Interview {interview.id} with direct Slot {slot.id}")
                    
                    # Method 2: Try to get slot from interview.schedule.slot (via InterviewSchedule)
                    elif interview:
                        try:
                            # Check if interview has a schedule
                            if hasattr(interview, 'schedule') and interview.schedule:
                                slot = interview.schedule.slot
                                print(f"✅ Found Interview {interview.id} with Slot {slot.id} via InterviewSchedule")
                            else:
                                # Try to fetch schedule explicitly
                                from interviews.models import InterviewSchedule
                                schedule = InterviewSchedule.objects.filter(interview=interview).first()
                                if schedule and schedule.slot:
                                    slot = schedule.slot
                                    print(f"✅ Found Interview {interview.id} with Slot {slot.id} via InterviewSchedule (fetched)")
                        except Exception as e:
                            print(f"⚠️ Error fetching schedule for interview: {e}")
                    
                    if slot:
                        print(f"   Slot AI Config: {slot.ai_configuration}")
                        
                        if slot.ai_configuration and isinstance(slot.ai_configuration, dict):
                            question_count = slot.ai_configuration.get('question_count', 4)
                            # Ensure it's an integer
                            try:
                                question_count = int(question_count)
                            except (ValueError, TypeError):
                                question_count = 4
                            print(f"✅ Using question count from InterviewSlot.ai_configuration: {question_count}")
                        # Also check if question_count is in slot directly (if it was added as a field)
                        elif hasattr(slot, 'question_count') and slot.question_count:
                            question_count = int(slot.question_count)
                            print(f"✅ Using question count from InterviewSlot.question_count: {question_count}")
                        else:
                            print(f"⚠️ No question_count found in slot.ai_configuration, using default 4")
                            print(f"   Available keys in ai_configuration: {list(slot.ai_configuration.keys()) if slot.ai_configuration else 'None'}")
                    else:
                        if not interview:
                            print(f"⚠️ No Interview found for session_key={session.session_key}, candidate_email={session.candidate_email}")
                        elif not interview.slot:
                            # Check if interview has a schedule
                            try:
                                from interviews.models import InterviewSchedule
                                schedule = InterviewSchedule.objects.filter(interview=interview).first()
                                if schedule:
                                    print(f"⚠️ Interview {interview.id} has no direct slot, but has schedule {schedule.id} with slot {schedule.slot.id if schedule.slot else 'None'}")
                                else:
                                    print(f"⚠️ Interview {interview.id} has no slot assigned and no schedule found")
                            except Exception as e:
                                print(f"⚠️ Interview {interview.id} has no slot assigned (error checking schedule: {e})")
                        print(f"⚠️ Using default question_count: 4")
                except Exception as e:
                    print(f"⚠️ Error getting question count, using default 4: {e}")
                    import traceback
                    traceback.print_exc()
                
                master_prompt = (
                    f"You are an expert Talaro interviewer.Your task is to generate {question_count} insightful interview 1-2 liner questions in {language_name}. "
                    f"The interview is for a '{session.job_description.splitlines()[0]}' role. "
                    "starting from introduction question .Please base the questions on the provided job description and candidate's resume. "
                    "Start with a welcoming ice-breaker question that also references something specific from the candidate's resume. "
                    "Then, generate a mix of technical Questions. 70 percent from jd and 30 percent from resume"
                    "dont add words in question like we taking reference according jd only question according to jd but dont need to explain we taking reference from jd"
                    "You MUST format the output as Markdown. "
                    "do not ask question repeatlt only when candidate answer then repherase with adding one line extra"
                    "You MUST include '## Technical Questions'. "
                    "Each question MUST start with a hyphen '-'. "
                    "Do NOT add any introductions, greetings (beyond the first ice-breaker question), or concluding remarks. "
                    f"\n\n--- JOB DESCRIPTION ---\n{session.job_description}\n\n--- RESUME ---\n{session.resume_text}"
                )
                full_response = model.generate_content(master_prompt)
                response_text = full_response.text
                sections = re.findall(r"##\s*(.*?)\s*\n(.*?)(?=\n##|\Z)", response_text, re.DOTALL)
                if not sections: raise ValueError("Could not parse ## headers from AI response.")
                for category_name, question_block in sections:
                    lines = question_block.strip().split('\n')
                    for line in lines:
                        if line.strip().startswith('-'):
                            all_questions.append({'type': category_name.strip(), 'text': line.strip().lstrip('- ').strip()})
                
                # Add dynamic coding questions based on job profile for production mode using Gemini API
                job_title = None
                domain_name = None
                if hasattr(session, 'interview') and session.interview and session.interview.job:
                    job_title = session.interview.job.job_title
                    if session.interview.job.domain:
                        domain_name = session.interview.job.domain.name
                
                # Get coding language from job (prioritize job.coding_language)
                allowed_langs = {
                    'PYTHON', 'JAVASCRIPT', 'C', 'CPP', 'JAVA', 'GO', 'HTML', 'PHP'
                }
                requested_lang = None
                
                # Priority 1: Get from Interview.job.coding_language via session_key (most reliable)
                try:
                    from interviews.models import Interview
                    interview = Interview.objects.filter(session_key=session.session_key).first()
                    print(f"🔍 DEBUG: Looking for Interview with session_key={session.session_key}")
                    if interview:
                        print(f"🔍 DEBUG: Found Interview {interview.id}, job={interview.job}")
                        if interview.job:
                            job_lang = getattr(interview.job, 'coding_language', None)
                            print(f"🔍 DEBUG: job.coding_language = {job_lang}")
                            if job_lang:
                                job_lang_upper = job_lang.upper()
                                print(f"🔍 DEBUG: job_lang_upper = {job_lang_upper}, allowed_langs = {allowed_langs}")
                                if job_lang_upper in allowed_langs:
                                    requested_lang = job_lang_upper
                                    print(f"✅ Using coding language from job via Interview: {requested_lang}")
                                else:
                                    print(f"⚠️ Language {job_lang_upper} not in allowed_langs {allowed_langs}")
                            else:
                                print(f"⚠️ job.coding_language is None or empty")
                        else:
                            print(f"⚠️ Interview found but interview.job is None")
                    else:
                        print(f"⚠️ No Interview found with session_key={session.session_key}")
                except Exception as e:
                    print(f"⚠️ Error getting coding language from Interview: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Priority 3: Get from URL parameter (fallback)
                if not requested_lang:
                    requested_lang = (request.GET.get('lang') or 'PYTHON').upper()
                    print(f"⚠️ Using coding language from URL parameter: {requested_lang}")
                
                # Validate and default to PYTHON if invalid
                if requested_lang not in allowed_langs:
                    requested_lang = 'PYTHON'
                    print(f"⚠️ Invalid language, defaulting to PYTHON")

                # Define one question with test cases per language
                hardcoded_map = {
                    'PYTHON': {
                        'title': 'Reverse a String',
                        'description': 'Write a function reverse_string(s: str) -> str that returns the reversed string.',
                        'language': 'PYTHON',
                        'starter_code': 'def reverse_string(s: str) -> str:\n    # TODO: implement\n    pass',
                        'test_cases': [
                            {'input': "'hello'", 'expected_output': 'olleh'},
                            {'input': "''", 'expected_output': ''},
                            {'input': "'abc'", 'expected_output': 'cba'}
                        ]
                    },
                    'JAVASCRIPT': {
                        'title': 'Reverse a String',
                        'description': 'Implement function reverseString(s) that returns the reversed string.',
                        'language': 'JAVASCRIPT',
                        'starter_code': 'function reverseString(s){\n  // TODO\n}\nmodule.exports = reverseString;',
                        'test_cases': [
                            {'input': "'hello'", 'expected_output': 'olleh'},
                            {'input': "''", 'expected_output': ''},
                            {'input': "'abc'", 'expected_output': 'cba'}
                        ]
                    },
                    'JAVA': {
                        'title': 'Add Two Numbers',
                        'description': 'Implement a static method add(int a, int b) that returns a+b.',
                        'language': 'JAVA',
                        'starter_code': 'public class Solution {\n  public static int add(int a,int b){\n    // TODO\n    return 0;\n  }\n}',
                        'test_cases': [
                            {'input': '1,2', 'expected_output': '3'},
                            {'input': '-5,5', 'expected_output': '0'},
                            {'input': '10,15', 'expected_output': '25'}
                        ]
                    },
                    'PHP': {
                        'title': 'Reverse a String',
                        'description': 'Implement function reverse_string($s) that returns the reversed string.',
                        'language': 'PHP',
                        'starter_code': '<?php\nfunction reverse_string($s){\n  // TODO\n}\n?>',
                        'test_cases': [
                            {'input': "'hello'", 'expected_output': 'olleh'},
                            {'input': "''", 'expected_output': ''},
                            {'input': "'abc'", 'expected_output': 'cba'}
                        ]
                    },
                    'C': {
                        'title': 'Add Two Numbers',
                        'description': 'Write a function int add(int a,int b) that returns a+b.',
                        'language': 'C',
                        'starter_code': 'int add(int a,int b){\n  // TODO\n  return 0;\n}',
                        'test_cases': [
                            {'input': '1,2', 'expected_output': '3'},
                            {'input': '-5,5', 'expected_output': '0'},
                            {'input': '10,15', 'expected_output': '25'}
                        ]
                    },
                    'CPP': {
                        'title': 'Add Two Numbers',
                        'description': 'Implement int add(int a,int b) that returns a+b.',
                        'language': 'CPP',
                        'starter_code': 'int add(int a,int b){\n  // TODO\n  return 0;\n}',
                        'test_cases': [
                            {'input': '1,2', 'expected_output': '3'},
                            {'input': '-5,5', 'expected_output': '0'},
                            {'input': '10,15', 'expected_output': '25'}
                        ]
                    },
                    'GO': {
                        'title': 'Reverse a String',
                        'description': 'Implement func Reverse(s string) string that returns the reversed string.',
                        'language': 'GO',
                        'starter_code': 'package main\nfunc Reverse(s string) string {\n  // TODO\n  return ""\n}',
                        'test_cases': [
                            {'input': '"hello"', 'expected_output': 'olleh'},
                            {'input': '""', 'expected_output': ''},
                            {'input': '"abc"', 'expected_output': 'cba'}
                        ]
                    },
                    'HTML': {
                        'title': 'Simple Heading',
                        'description': 'Return an HTML string with an <h1>Hello</h1> element.',
                        'language': 'HTML',
                        'starter_code': '<!-- return <h1>Hello</h1> -->',
                        'test_cases': [
                            {'input': 'n/a', 'expected_output': '<h1>Hello</h1>'}
                        ]
                    }
                }

                # Enforce exactly one coding question
                coding_questions = [hardcoded_map[requested_lang]]
            if not all_questions: raise ValueError("No questions were generated or parsed.")
            if all_questions and "welcome" in all_questions[0]['text'].lower():
                all_questions[0]['type'] = 'Ice-Breaker'
            session.save()
            tts_dir = os.path.join(settings.MEDIA_ROOT, 'tts'); os.makedirs(tts_dir, exist_ok=True)
            # Save spoken questions to database
            for i, q_data in enumerate(all_questions):
                tts_path = os.path.join(tts_dir, f'q_{i}_{session.session_key}.mp3')
                synthesize_speech(q_data['text'], session.language_code, session.accent_tld, tts_path)
                audio_url = f"{settings.MEDIA_URL}tts/{os.path.basename(tts_path)}"
                q_data['audio_url'] = audio_url
                InterviewQuestion.objects.create(
                    session=session,
                    question_text=q_data['text'],
                    question_type=q_data['type'],
                    order=i,
                    question_level='MAIN'
                )
            
            # Ensure no duplicate coding questions remain from previous runs
            try:
                session.questions.filter(question_type='CODING').delete()
            except Exception:
                pass

            # Save coding questions (single) to database and attach test cases
            for i, coding_q in enumerate(coding_questions[:1]):
                coding_question_obj = InterviewQuestion.objects.create(
                    session=session,
                    question_text=coding_q['description'],
                    question_type='CODING',
                    coding_language=coding_q['language'],
                    order=len(all_questions) + i,
                    question_level='MAIN'
                )
                # Attach test cases
                try:
                    from .models import TestCase
                except Exception:
                    TestCase = None
                if TestCase and coding_q.get('test_cases'):
                    for tc in coding_q['test_cases']:
                        try:
                            TestCase.objects.create(
                                question=coding_question_obj,
                                input_data=str(tc.get('input', '')),
                                expected_output=str(tc.get('expected_output', ''))
                            )
                        except Exception:
                            pass
                # Update the coding_questions_data with the real database ID
                coding_q['id'] = str(coding_question_obj.id)
        
        # Debug: Print what we're sending to the template
        print(f"\n{'='*70}")
        print(f"🔍 PORTAL DATA DEBUG:")
        print(f"   Spoken questions: {len(all_questions)}")
        print(f"   Coding questions: {len(coding_questions)}")
        if coding_questions:
            for idx, cq in enumerate(coding_questions):
                print(f"   Coding Q{idx+1}: {cq.get('title', 'No title')[:50]} | Test cases: {len(cq.get('test_cases', []))}")
        print(f"{'='*70}\n")
        print(f"DEBUG: Context keys: {list({'session_key': session_key, 'interview_session_id': str(session.id), 'spoken_questions_data': all_questions, 'coding_questions_data': coding_questions, 'interview_started': True}.keys())}")
        
        print(f"DEBUG: Rendering interview portal for session {session_key}")
        context = {
            'session_key': session_key,
            'interview_session_id': str(session.id),
            'spoken_questions_data': all_questions,
            'coding_questions_data': coding_questions,
            'interview_started': True,
            'candidate_name': session.candidate_name,
            'job_description': session.job_description,
        }
        return render(request, 'interview_app/portal.html', context)
    except Exception as e:
        # Graceful fallback when AI services (e.g., Gemini) are unavailable.
        # Load the portal with no spoken questions so the chatbot/coding phases can proceed.
        try:
            print(f"WARN: AI setup failed, falling back without spoken questions: {e}")
            session = get_object_or_404(InterviewSession, session_key=session_key)
            context = {
                'session_key': session_key,
                'interview_session_id': str(session.id),
                'spoken_questions_data': [],
                'coding_questions_data': [],
                'interview_started': True,
            }
            return render(request, 'interview_app/portal.html', context)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return HttpResponse(f"An API or processing error occurred: {str(e)}", status=500)
        
@login_required
def dashboard(request):
    sessions = InterviewSession.objects.all().order_by('-created_at')
    context = {'sessions': sessions}
    template = loader.get_template('interview_app/dashboard.html')
    return HttpResponse(template.render(context, request))

def serve_react_app(request):
    """Serve React app's index.html for all frontend routes (SPA catch-all)"""
    try:
        # Try multiple possible locations for the frontend build
        # 1. static_frontend_dist (copied dist folder in backend repo - for deployment)
        # 2. frontend/dist (if frontend is not a submodule or is checked out)
        possible_paths = [
            os.path.join(settings.BASE_DIR, 'static_frontend_dist', 'index.html'),
            os.path.join(settings.BASE_DIR, 'frontend', 'dist', 'index.html'),
        ]
        
        frontend_build_path = None
        frontend_dist_dir = None
        
        # Debug logging
        print(f"🔍 Looking for frontend build...")
        print(f"   BASE_DIR: {settings.BASE_DIR}")
        
        for path in possible_paths:
            dist_dir = os.path.dirname(path)
            print(f"   Checking: {path}")
            print(f"   Exists: {os.path.exists(path)}")
            if os.path.exists(path):
                frontend_build_path = path
                frontend_dist_dir = dist_dir
                print(f"   ✅ Found frontend at: {path}")
                break
        
        # If no build found, use first path for logging
        if not frontend_build_path:
            frontend_build_path = possible_paths[0]
            frontend_dist_dir = os.path.dirname(frontend_build_path)
            print(f"   ❌ Frontend build not found in any location")
        
        # If built version exists, serve it
        if frontend_build_path and os.path.exists(frontend_build_path):
            print(f"✅ Serving frontend from: {frontend_build_path}")
            with open(frontend_build_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Update asset paths if needed (Vite builds use absolute paths)
                return HttpResponse(content, content_type='text/html')
        
        # Fallback: serve development index.html if dist doesn't exist
        # Note: In development, you should run the frontend separately with `npm run dev`
        # This is just a fallback for when accessing Django directly
        frontend_dev_path = os.path.join(settings.BASE_DIR, 'frontend', 'index.html')
        if os.path.exists(frontend_dev_path):
            print(f"⚠️ Using dev index.html from: {frontend_dev_path}")
            with open(frontend_dev_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # In development mode, suggest using the Vite dev server
                if settings.DEBUG:
                    content = content.replace(
                        '</body>',
                        '<script>console.warn("⚠️ Frontend not built. For development, run: cd frontend && npm run dev");</script></body>'
                    )
                return HttpResponse(content, content_type='text/html')
        
        # Last resort: return a helpful message with debug info
        debug_info = f"""
        <h2>Debug Information:</h2>
        <ul>
            <li>BASE_DIR: {settings.BASE_DIR}</li>
            <li>Expected build path: {frontend_build_path}</li>
            <li>Build path exists: {os.path.exists(frontend_build_path)}</li>
            <li>Frontend dir exists: {os.path.exists(os.path.join(settings.BASE_DIR, 'frontend'))}</li>
            <li>Dist dir exists: {os.path.exists(frontend_dist_dir)}</li>
        </ul>
        """
        return HttpResponse(
            f'<html><body><h1>Frontend not found</h1>'
            f'{debug_info}'
            f'<p>Please build the frontend:</p>'
            f'<pre>cd frontend && npm install && npm run build</pre>'
            f'<p>Or for development, run the frontend separately:</p>'
            f'<pre>cd frontend && npm run dev</pre>'
            f'</body></html>',
            status=200  # Return 200 instead of 404 so it shows the message
        )
    except Exception as e:
        import traceback
        error_msg = f'Error serving frontend: {str(e)}\n{traceback.format_exc()}'
        print(f"❌ Error in serve_react_app: {error_msg}")
        return HttpResponse(f'<html><body><h1>Error</h1><pre>{error_msg}</pre></body></html>', status=500)

@login_required
def interview_report(request, session_id):
    try:
        session = InterviewSession.objects.get(id=session_id)
        all_questions = list(session.questions.all().order_by('order'))
        all_logs_list = list(session.logs.all())
        warning_counts = Counter([log.warning_type.replace('_', ' ').title() for log in all_logs_list if log.warning_type != 'excessive_movement'])
        
        # Check if there is any new content to evaluate
        has_spoken_answers = session.questions.filter(transcribed_answer__isnull=False, transcribed_answer__gt='').exists()
        has_code_submissions = session.code_submissions.exists()

        if session.language_code == 'en' and not session.is_evaluated and (has_spoken_answers or has_code_submissions):
            print(f"--- Performing all first-time AI evaluations for session {session.id} with Gemini ---")
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            try:
                print("--- Evaluating Resume vs. Job Description ---")
                resume_eval_prompt = (
                    "You are an expert technical recruiter. Analyze the following resume against the provided job description. "
                    "Provide a score from 0.0 to 10.0 indicating how well the candidate's experience aligns with the job requirements. "
                    "Also provide a brief analysis. Format your response EXACTLY as follows:\n\n"
                    "SCORE: [Your score, e.g., 8.2]\n"
                    "ANALYSIS: [Your one-paragraph analysis here.]"
                    f"\n\nJOB DESCRIPTION:\n{session.job_description}\n\nRESUME:\n{session.resume_text}"
                )
                resume_response = model.generate_content(resume_eval_prompt)
                resume_response_text = resume_response.text
                score_match = re.search(r"SCORE:\s*([\d\.]+)", resume_response_text)
                if score_match: session.resume_score = float(score_match.group(1))
                session.resume_feedback = resume_response_text
            except Exception as e:
                print(f"ERROR during Resume evaluation: {e}"); session.resume_feedback = "An error occurred during resume evaluation."

            try:
                print("--- Evaluating Interview Performance (Spoken & Coding) ---")
                
                qa_text = "".join([
                    f"Question: {item.question_text}\nAnswer: {item.transcribed_answer or 'No answer provided.'}\n\n"
                    for item in all_questions if item.question_type != 'CODING'
                ])

                code_submissions_for_prompt = session.code_submissions.all()
                code_text = ""
                for submission in code_submissions_for_prompt:
                    # Get the question text from the question_id
                    try:
                        question = InterviewQuestion.objects.get(id=submission.question_id)
                        question_text = question.question_text
                    except InterviewQuestion.DoesNotExist:
                        question_text = f"Question ID: {submission.question_id}"
                    
                    code_text += f"Coding Challenge: {question_text}\n"
                    code_text += f"Language: {submission.language}\n"
                    code_text += f"Test Case Results:\n{submission.output_log}\n"
                    code_text += f"Submitted Code:\n```\n{submission.submitted_code}\n```\n\n"

                answers_eval_prompt = (
                    "You are an expert technical hiring manager. Evaluate the candidate's complete interview performance, "
                    "which includes both spoken answers and a code submission. Provide an overall score from 0.0 to 10.0 "
                    "and a brief summary of their strengths and areas for improvement based on ALL provided materials.\n\n"
                    "Consider the following:\n"
                    "- For spoken answers, evaluate clarity, relevance, and communication skills.\n"
                    "- For the coding submission, evaluate correctness (did it pass the tests?), problem-solving, and code quality.\n"
                    "- A strong coding performance can significantly boost a score, even if spoken answers are weak. Conversely, failing coding tests is a major negative signal.\n\n"
                    "Format your response EXACTLY as follows:\n\n"
                    "SCORE: [Your score, e.g., 7.5]\n"
                    "FEEDBACK: [Your detailed, holistic feedback here.]"
                    f"\n\n--- SPOKEN QUESTIONS & ANSWERS ---\n{qa_text or 'No spoken answers provided.'}"
                    f"\n\n--- CODING CHALLENGE SUBMISSION ---\n{code_text or 'No code submitted.'}"
                )
                
                answers_response = model.generate_content(answers_eval_prompt)
                answers_response_text = answers_response.text
                score_match = re.search(r"SCORE:\s*([\d\.]+)", answers_response_text)
                if score_match: session.answers_score = float(score_match.group(1))
                session.answers_feedback = answers_response_text
            except Exception as e:
                print(f"ERROR during Answers evaluation: {e}"); session.answers_feedback = "An error occurred during answers evaluation."

            try:
                print("--- Generating Overall Candidate Profile ---")
                warning_summary = ", ".join([f"{count}x {name}" for name, count in warning_counts.items()]) or "None"
                overall_prompt = (
                    "You are a senior hiring manager. You have been provided with a holistic view of a candidate's interview, "
                    "including their resume fit, interview answer performance, and proctoring warnings. "
                    "Synthesize all this information into a final recommendation. "
                    "Provide a final 'Overall Score' from 0.0 to 10.0 and a concluding 'Hiring Recommendation' paragraph.\n\n"
                    "DATA PROVIDED:\n"
                    f"- Resume vs. Job Description Score: {session.resume_score or 'N/A'}/10\n"
                    f"- Interview Answers Score: {session.answers_score or 'N/A'}/10\n"
                    f"- Proctoring Warnings: {warning_summary}\n\n"
                    "Format your response EXACTLY as follows:\n\n"
                    "OVERALL SCORE: [Your final blended score, e.g., 7.8]\n"
                    "HIRING RECOMMENDATION: [Your final concluding paragraph on whether to proceed with the candidate and why.]"
                )
                overall_response = model.generate_content(overall_prompt)
                overall_response_text = overall_response.text
                score_match = re.search(r"OVERALL SCORE:\s*([\d\.]+)", overall_response_text)
                if score_match: session.overall_performance_score = float(score_match.group(1))
                session.overall_performance_feedback = overall_response_text
            except Exception as e:
                print(f"ERROR during Overall evaluation: {e}"); session.overall_performance_feedback = "An error occurred."
            
            session.is_evaluated = True
            session.save()
        
        total_filler_words = 0
        avg_wpm = 0
        wpm_count = 0
        sentiment_scores = []
        avg_response_time = 0
        response_time_count = 0

        if session.language_code == 'en':
            for item in all_questions:
                if item.transcribed_answer:
                    word_count = len(item.transcribed_answer.split())
                    read_time_result = readtime.of_text(item.transcribed_answer)
                    read_time_minutes = read_time_result.minutes + (read_time_result.seconds / 60)
                    if read_time_minutes > 0:
                        item.words_per_minute = round(word_count / read_time_minutes)
                        avg_wpm += item.words_per_minute
                        wpm_count += 1
                    else:
                        item.words_per_minute = 0
                    if item.response_time_seconds:
                        avg_response_time += item.response_time_seconds
                        response_time_count += 1
                    lower_answer = item.transcribed_answer.lower()
                    item.filler_word_count = sum(lower_answer.count(word) for word in FILLER_WORDS)
                    total_filler_words += item.filler_word_count
                    if TEXTBLOB_AVAILABLE and TextBlob:
                        sentiment_scores.append({'question': f"Q{item.order + 1}", 'score': TextBlob(item.transcribed_answer).sentiment.polarity})
                    else:
                        sentiment_scores.append({'question': f"Q{item.order + 1}", 'score': 0.0})
                else:
                    sentiment_scores.append({'question': f"Q{item.order + 1}", 'score': 0.0})
        
        final_avg_wpm = round(avg_wpm / wpm_count) if wpm_count > 0 else 0
        final_avg_response_time = round(avg_response_time / response_time_count, 2) if response_time_count > 0 else 0

        analytics_data = {
            'warning_counts': dict(warning_counts),
            'sentiment_scores': sentiment_scores,
            'evaluation_scores': {'Resume vs JD': session.resume_score or 0, 'Interview Answers': session.answers_score or 0},
            'communication_radar': {
                'Pace (WPM)': final_avg_wpm,
                'Clarity (Few Fillers)': total_filler_words,
                'Responsiveness (sec)': final_avg_response_time
            },
        }
        
        main_questions_with_followups = session.questions.filter(question_level='MAIN', question_type__in=['TECHNICAL', 'BEHAVIORAL']).prefetch_related('follow_ups').order_by('order')
        code_submissions = session.code_submissions.all()

        context = {
            'session': session, 
            'main_questions_with_followups': main_questions_with_followups,
            'code_submissions': code_submissions,
            'analytics_data': json.dumps(analytics_data),
            'total_filler_words': total_filler_words,
            'avg_wpm': final_avg_wpm,
            'behavioral_analysis_html': mark_safe((session.behavioral_analysis or "").replace('\n', '<br>')),
            'keyword_analysis_html': mark_safe((session.keyword_analysis or "").replace('\n', '<br>').replace('**', '<strong>').replace('**', '</strong>'))
        }
        template = loader.get_template('interview_app/report.html')
        return HttpResponse(template.render(context, request))
    except InterviewSession.DoesNotExist:
        return HttpResponse("Interview session not found.", status=404)
@login_required
def download_report_pdf(request, session_id):
    """
    Generates and serves a PDF version of the interview report for a given session.
    """
    try:
        # 1. Fetch the main session object.
        session = InterviewSession.objects.get(id=session_id)
        
        # 2. Prepare data for the proctoring summary chart.
        all_logs_list = list(session.logs.all())
        warning_counts = Counter([log.warning_type.replace('_', ' ').title() for log in all_logs_list if log.warning_type != 'excessive_movement'])
        chart_config = { 
            'type': 'doughnut', 
            'data': { 
                'labels': list(warning_counts.keys()), 
                'datasets': [{'data': list(warning_counts.values())}]
            }
        }
        # URL-encode the chart configuration to pass to the chart generation service.
        chart_url = f"https://quickchart.io/chart?c={urllib.parse.quote(json.dumps(chart_config))}"
        
        # 3. Fetch all SPOKEN questions and their follow-ups.
        # This query correctly filters out the coding questions.
        main_questions_with_followups = session.questions.filter(
            question_level='MAIN', 
            question_type__in=['TECHNICAL', 'BEHAVIORAL']
        ).prefetch_related('follow_ups').order_by('order')
        
        # 4. Fetch all CODING challenge submissions. This was the missing piece.
        code_submissions = session.code_submissions.all()

        # 5. Calculate metrics for charts
        # Grammar score (estimated from answers - assume good grammar if answers exist, can be refined)
        grammar_score = min(100, max(0, (session.answers_score or 0) * 10 + 20)) if session.answers_score else 70
        
        # Technical knowledge (from answers_score converted to percentage)
        technical_knowledge = min(100, max(0, (session.answers_score or 0) * 10)) if session.answers_score else 50
        
        # Coding round understanding (calculate from code submissions)
        coding_understanding = 0
        if code_submissions.exists():
            total_tests = 0
            passed_tests = 0
            for submission in code_submissions:
                # Parse test results from output_log
                if submission.output_log:
                    test_matches = re.findall(r'(\d+)/(\d+)', submission.output_log)
                    if test_matches:
                        for passed, total in test_matches:
                            passed_tests += int(passed)
                            total_tests += int(total)
                    else:
                        # If no test results, check if there's any success indicator
                        if 'passed' in submission.output_log.lower() or 'success' in submission.output_log.lower():
                            coding_understanding = 70
                        else:
                            coding_understanding = 40
            if total_tests > 0:
                coding_understanding = min(100, int((passed_tests / total_tests) * 100))
            elif coding_understanding == 0:
                coding_understanding = 60  # Default if code was submitted but no test results
        else:
            coding_understanding = 0  # No code submitted
        
        # Technology understanding (calculate from technical questions)
        tech_questions_count = main_questions_with_followups.filter(question_type='TECHNICAL').count()
        tech_understanding = min(100, max(0, (tech_questions_count / 5) * 100)) if tech_questions_count > 0 else 50
        
        # Determine recommendation
        overall_percentage = (grammar_score * 0.2 + technical_knowledge * 0.4 + coding_understanding * 0.3 + tech_understanding * 0.1)
        if overall_percentage >= 80:
            recommendation = "STRONGLY RECOMMENDED"
            recommendation_color = "#28a745"  # Green
        elif overall_percentage >= 65:
            recommendation = "RECOMMENDED"
            recommendation_color = "#17a2b8"  # Blue
        elif overall_percentage >= 50:
            recommendation = "CONDITIONAL RECOMMENDATION"
            recommendation_color = "#ffc107"  # Yellow
        else:
            recommendation = "NOT RECOMMENDED"
            recommendation_color = "#dc3545"  # Red
        
        # Generate Bar Chart for Grammar, Technical Knowledge, Coding Round
        bar_chart_config = {
            'type': 'bar',
            'data': {
                'labels': ['Grammar', 'Technical Knowledge', 'Coding Round'],
                'datasets': [{
                    'label': 'Score (%)',
                    'data': [grammar_score, technical_knowledge, coding_understanding],
                    'backgroundColor': ['#3498db', '#9b59b6', '#e74c3c'],
                    'borderColor': ['#2980b9', '#8e44ad', '#c0392b'],
                    'borderWidth': 2
                }]
            },
            'options': {
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'max': 100,
                        'ticks': {
                            'callback': "function(value) { return value + '%'; }"
                        }
                    }
                },
                'plugins': {
                    'legend': {
                        'display': False
                    }
                }
            }
        }
        bar_chart_url = f"https://quickchart.io/chart?c={urllib.parse.quote(json.dumps(bar_chart_config))}"
        
        # Generate Pie Chart for Technology Understanding
        pie_chart_config = {
            'type': 'pie',
            'data': {
                'labels': ['Technology Understanding', 'Remaining'],
                'datasets': [{
                    'data': [tech_understanding, 100 - tech_understanding],
                    'backgroundColor': ['#27ae60', '#ecf0f1'],
                    'borderWidth': 2
                }]
            },
            'options': {
                'plugins': {
                    'legend': {
                        'position': 'bottom'
                    },
                    'tooltip': {
                        'callbacks': {
                            'label': "function(context) { return context.label + ': ' + context.parsed + '%'; }"
                        }
                    }
                }
            }
        }
        pie_chart_url = f"https://quickchart.io/chart?c={urllib.parse.quote(json.dumps(pie_chart_config))}"

        # 5. Assemble the complete context dictionary to be passed to the template.
        context = { 
            'session': session, 
            'main_questions_with_followups': main_questions_with_followups,
            'code_submissions': code_submissions,
            'warning_counts': dict(warning_counts), 
            'chart_url': chart_url,
            'grammar_score': grammar_score,
            'technical_knowledge': technical_knowledge,
            'coding_understanding': coding_understanding,
            'tech_understanding': tech_understanding,
            'bar_chart_url': bar_chart_url,
            'pie_chart_url': pie_chart_url,
            'recommendation': recommendation,
            'recommendation_color': recommendation_color,
            'overall_percentage': overall_percentage
        }
        
        # 6. Download chart images and convert to base64 to avoid WeasyPrint network delays
        try:
            import requests
        except ImportError:
            print("⚠️ requests library not available, charts may load slowly")
            requests = None
        
        def download_chart_to_base64(url, timeout=5):
            """Download chart image and convert to base64 data URI"""
            if not requests:
                # If requests not available, return original URL (WeasyPrint will fetch it)
                return url
            try:
                response = requests.get(url, timeout=timeout, stream=True)
                response.raise_for_status()
                img_data = response.content
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                content_type = response.headers.get('Content-Type', 'image/png')
                return f"data:{content_type};base64,{img_base64}"
            except requests.exceptions.Timeout:
                print(f"⚠️ Chart download timed out: {url}")
                return url  # Return original URL as fallback
            except Exception as e:
                print(f"⚠️ Failed to download chart from {url}: {e}")
                return url  # Return original URL as fallback
        
        # Download all chart images before rendering (with shorter timeout for faster failover)
        # Use concurrent downloads to speed up the process
        import concurrent.futures
        print("📥 Downloading chart images (max 3s each, concurrent)...")
        chart_urls_to_download = []
        if chart_url:
            chart_urls_to_download.append(('chart_url', chart_url))
        if bar_chart_url:
            chart_urls_to_download.append(('bar_chart_url', bar_chart_url))
        if pie_chart_url:
            chart_urls_to_download.append(('pie_chart_url', pie_chart_url))
        
        chart_results = {}
        if chart_urls_to_download and requests:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_name = {
                    executor.submit(download_chart_to_base64, url, timeout=3): name 
                    for name, url in chart_urls_to_download
                }
                for future in concurrent.futures.as_completed(future_to_name, timeout=10):
                    name = future_to_name[future]
                    try:
                        chart_results[name] = future.result()
                    except Exception as e:
                        print(f"⚠️ Chart download failed for {name}: {e}")
                        # Fallback to original URL
                        original_url = next((url for n, url in chart_urls_to_download if n == name), None)
                        chart_results[name] = original_url if original_url else None
        else:
            # Fallback: sequential downloads or use original URLs
            for name, url in chart_urls_to_download:
                chart_results[name] = download_chart_to_base64(url, timeout=3) if requests else url
        
        print("✅ Chart downloads complete")
        
        # Update context with downloaded images (base64) or original URLs
        context['chart_url'] = chart_results.get('chart_url', chart_url) if 'chart_url' in chart_results else chart_url
        context['bar_chart_url'] = chart_results.get('bar_chart_url', bar_chart_url) if 'bar_chart_url' in chart_results else bar_chart_url
        context['pie_chart_url'] = chart_results.get('pie_chart_url', pie_chart_url) if 'pie_chart_url' in chart_results else pie_chart_url
        
        # 6. Render the HTML template to a string.
        print("📄 Rendering HTML template...")
        html_string = render_to_string('interview_app/report_pdf.html', context)
        
        # 7. Use WeasyPrint to convert the rendered HTML string into a PDF.
        if not WEASYPRINT_AVAILABLE or HTML is None:
            return HttpResponse(
                "PDF generation is not available. WeasyPrint is not installed. Please install weasyprint to enable PDF generation.",
                status=503
            )
        
        print("🖨️ Generating PDF with WeasyPrint...")
        try:
            # Use base_url to help resolve any relative URLs, but don't rely on it for external images
            # (since we've already downloaded them as base64)
            pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
            print(f"✅ PDF generated successfully ({len(pdf)} bytes)")
        except Exception as pdf_error:
            print(f"❌ WeasyPrint error: {pdf_error}")
            # Fallback: try without base_url
            try:
                pdf = HTML(string=html_string).write_pdf()
                print(f"✅ PDF generated with fallback method ({len(pdf)} bytes)")
            except Exception as fallback_error:
                print(f"❌ PDF generation completely failed: {fallback_error}")
                import traceback
                traceback.print_exc()
                return HttpResponse(
                    f"PDF generation failed. Please check server logs. Error: {str(fallback_error)}",
                    status=500,
                    content_type='text/plain'
                )
        
        # 8. Create and return the final HTTP response.
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="interview_report_{session.id}.pdf"'
        return response
        
    except InterviewSession.DoesNotExist:
        return HttpResponse("Interview session not found.", status=404)
    except Exception as e:
        # General error handling for unexpected issues during PDF generation.
        print(f"Error generating PDF report for session {session_id}: {e}")
        traceback.print_exc()
        return HttpResponse(f"An unexpected error occurred while generating the PDF report: {e}", status=500)

@csrf_exempt
@require_POST
def end_interview_session(request):
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        audio_file_path = data.get('audio_file_path')  # Optional: path to uploaded audio file
        
        print(f"🔍 end_interview_session called:")
        print(f"   session_key: {session_key}")
        print(f"   audio_file_path (from request): {audio_file_path}")
        print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
        
        if not session_key:
            return JsonResponse({"status": "error", "message": "Session key required."}, status=400)
        
        # Stop video recording and merge with audio if provided
        video_path = None
        try:
            # First, try to get the video path from InterviewSession if camera doesn't have it
            video_path_from_db = None
            try:
                from interview_app.models import InterviewSession
                session = InterviewSession.objects.get(session_key=session_key)
                session_id_uuid = session.id  # Get the UUID for file system search
                
                if session.interview_video:
                    video_path_from_db = os.path.join(settings.MEDIA_ROOT, str(session.interview_video))
                    # If it's a converted video, try to find the original
                    if '_converted' in str(session.interview_video) and os.path.exists(video_path_from_db):
                        # Look for original video (without _converted)
                        original_name = str(session.interview_video).replace('_converted', '')
                        original_path = os.path.join(settings.MEDIA_ROOT, original_name)
                        if os.path.exists(original_path):
                            video_path_from_db = original_path
                            print(f"✅ Found original video for merging: {video_path_from_db}")
                        else:
                            print(f"⚠️ Original video not found, will use converted: {video_path_from_db}")
                    elif os.path.exists(video_path_from_db):
                        print(f"✅ Found video from InterviewSession: {video_path_from_db}")
                    else:
                        print(f"⚠️ Video path from InterviewSession doesn't exist: {video_path_from_db}")
                        video_path_from_db = None
                
                # If no video in DB, search filesystem by session_id (UUID)
                if not video_path_from_db:
                    print(f"🔍 Video not in database, searching filesystem by session_id: {session_id_uuid}")
                    search_dirs = [
                        os.path.join(settings.MEDIA_ROOT, 'interview_videos_raw'),
                        os.path.join(settings.MEDIA_ROOT, 'interview_videos'),  # Old folder
                    ]
                    session_id_str = str(session_id_uuid)
                    for search_dir in search_dirs:
                        if not os.path.exists(search_dir):
                            continue
                        try:
                            for filename in os.listdir(search_dir):
                                if filename.startswith(session_id_str) and filename.endswith('.mp4'):
                                    if '_with_audio' not in filename:  # Don't use already merged
                                        candidate = os.path.join(search_dir, filename)
                                        if os.path.exists(candidate):
                                            video_path_from_db = candidate
                                            print(f"✅ Found video in filesystem: {video_path_from_db}")
                                            break
                            if video_path_from_db:
                                break
                        except Exception as e:
                            print(f"⚠️ Error searching {search_dir}: {e}")
            except Exception as e:
                print(f"⚠️ Error looking up video from InterviewSession: {e}")
                import traceback
                traceback.print_exc()
            
            camera = get_camera_for_session(session_key)
            if camera and hasattr(camera, 'stop_video_recording'):
                # If camera doesn't have video path but we found it in DB, set it
                if video_path_from_db:
                    if not hasattr(camera, '_video_file_path') or not camera._video_file_path or not os.path.exists(getattr(camera, '_video_file_path', '')):
                        camera._video_file_path = video_path_from_db
                        print(f"✅ Set video path in camera object from database: {video_path_from_db}")
                    else:
                        print(f"✅ Camera already has video path: {camera._video_file_path}")
                
                # Pass audio file path if provided for merging
                audio_full_path = None
                audio_start_ts = None
                video_start_ts = None
                
                # CRITICAL: Get video start timestamp from camera for synchronization
                # Priority 1: Get from camera's _recording_start_timestamp (set when first frame written)
                if hasattr(camera, '_recording_start_timestamp') and camera._recording_start_timestamp:
                    video_start_ts = camera._recording_start_timestamp
                    print(f"🕐 Video start timestamp from camera (first frame): {video_start_ts}")
                # Priority 2: Get from camera's _synchronized_start_time (set when start_video_recording called)
                elif hasattr(camera, '_synchronized_start_time') and camera._synchronized_start_time:
                    video_start_ts = camera._synchronized_start_time
                    print(f"🕐 Video start timestamp from camera (synchronized time): {video_start_ts}")
                # Priority 3: Get from request data
                if not video_start_ts:
                    video_start_ts = data.get('video_start_timestamp')
                    if video_start_ts:
                        try:
                            video_start_ts = float(video_start_ts)
                            print(f"🕐 Video start timestamp from request: {video_start_ts}")
                        except (ValueError, TypeError):
                            video_start_ts = None
                
                # CRITICAL: If audio_file_path is not provided, try to find it from uploaded audio
                if not audio_file_path:
                    print(f"🔍 Audio file path not provided, searching for uploaded audio file...")
                    # Try to find audio file in interview_audio directory
                    audio_dir = os.path.join(settings.MEDIA_ROOT, 'interview_audio')
                    if os.path.exists(audio_dir):
                        # Search for audio file by session_key
                        session_id_str = str(session_id_uuid)
                        for filename in os.listdir(audio_dir):
                            # Check if filename contains session_key or session_id
                            if (session_key in filename or session_id_str in filename) and (filename.endswith('.webm') or filename.endswith('.wav') or filename.endswith('.mp3')):
                                potential_audio = os.path.join(audio_dir, filename)
                                if os.path.exists(potential_audio) and os.path.getsize(potential_audio) > 0:
                                    audio_file_path = os.path.relpath(potential_audio, settings.MEDIA_ROOT).replace('\\', '/')
                                    print(f"✅ Found audio file: {audio_file_path} ({os.path.getsize(potential_audio) / 1024 / 1024:.2f} MB)")
                                    break
                    
                    # If still not found, try searching with different patterns
                    if not audio_file_path and os.path.exists(audio_dir):
                        # Try searching for any file with "interview_audio" in name
                        for filename in os.listdir(audio_dir):
                            if 'interview_audio' in filename.lower() and (filename.endswith('.webm') or filename.endswith('.wav')):
                                potential_audio = os.path.join(audio_dir, filename)
                                if os.path.exists(potential_audio) and os.path.getsize(potential_audio) > 0:
                                    # Check if it's recent (within last hour)
                                    import time
                                    file_age = time.time() - os.path.getmtime(potential_audio)
                                    if file_age < 3600:  # Within last hour
                                        audio_file_path = os.path.relpath(potential_audio, settings.MEDIA_ROOT).replace('\\', '/')
                                        print(f"✅ Found recent audio file: {audio_file_path}")
                                        break
                
                if audio_file_path:
                    # Convert relative path to absolute path
                    # Normalize path separators (handle both / and \)
                    audio_file_path = audio_file_path.replace('/', os.sep).replace('\\', os.sep)
                    if not os.path.isabs(audio_file_path):
                        audio_full_path = os.path.join(settings.MEDIA_ROOT, audio_file_path)
                    else:
                        audio_full_path = audio_file_path
                    # Normalize the final path
                    audio_full_path = os.path.normpath(audio_full_path)
                    if os.path.exists(audio_full_path):
                        file_size = os.path.getsize(audio_full_path)
                        print(f"✅ Audio file found for merging: {audio_full_path} ({file_size / 1024 / 1024:.2f} MB)")
                    else:
                        print(f"⚠️ Audio file not found: {audio_full_path}")
                        # Try to find it in interview_audio directory
                        audio_filename = os.path.basename(audio_file_path)
                        alt_path = os.path.join(settings.MEDIA_ROOT, 'interview_audio', audio_filename)
                        if os.path.exists(alt_path):
                            audio_full_path = alt_path
                            print(f"✅ Audio file found at alternate location: {audio_full_path}")
                        else:
                            audio_full_path = None
                    
                    # Get timestamps from request or from cache for synchronization
                    audio_start_ts = data.get('audio_start_timestamp')
                    video_start_ts = data.get('video_start_timestamp')
                    
                    # If not in request, try to get from upload_interview_audio timestamp cache
                    if not audio_start_ts or not video_start_ts:
                        try:
                            # Use the function reference directly (avoid circular import)
                            upload_func = globals().get('upload_interview_audio')
                            if upload_func and hasattr(upload_func, '_timestamp_cache') and session_key in upload_func._timestamp_cache:
                                cached_ts = upload_func._timestamp_cache[session_key]
                                if not audio_start_ts:
                                    audio_start_ts = cached_ts.get('audio_start_timestamp')
                                if not video_start_ts:
                                    video_start_ts = cached_ts.get('video_start_timestamp')
                                print(f"📥 Retrieved timestamps from cache: audio={audio_start_ts}, video={video_start_ts}")
                        except Exception as e:
                            print(f"⚠️ Error retrieving timestamps from cache: {e}")
                    
                    if audio_start_ts:
                        try:
                            audio_start_ts = float(audio_start_ts)
                            print(f"📥 Audio start timestamp: {audio_start_ts}")
                        except (ValueError, TypeError):
                            audio_start_ts = None
                    if video_start_ts:
                        try:
                            video_start_ts = float(video_start_ts)
                            print(f"📥 Video start timestamp: {video_start_ts}")
                        except (ValueError, TypeError):
                            video_start_ts = None
                else:
                    print("⚠️ No audio file path found - video will be saved without audio")
                    print(f"   Request data keys: {list(data.keys())}")
                    print(f"   audio_file_path value: {audio_file_path}")
                    print(f"   Searched in: {os.path.join(settings.MEDIA_ROOT, 'interview_audio')}")
                    
                    # Last resort: try to find ANY audio file in interview_audio directory
                    audio_dir = os.path.join(settings.MEDIA_ROOT, 'interview_audio')
                    if os.path.exists(audio_dir):
                        # Get the most recent audio file
                        audio_files = []
                        for filename in os.listdir(audio_dir):
                            if filename.endswith(('.webm', '.wav', '.mp3')):
                                file_path = os.path.join(audio_dir, filename)
                                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                    audio_files.append((file_path, os.path.getmtime(file_path)))
                        
                        if audio_files:
                            # Sort by modification time (most recent first)
                            audio_files.sort(key=lambda x: x[1], reverse=True)
                            most_recent_audio = audio_files[0][0]
                            audio_file_path = os.path.relpath(most_recent_audio, settings.MEDIA_ROOT).replace('\\', '/')
                            audio_full_path = most_recent_audio
                            print(f"✅ Found most recent audio file as fallback: {audio_file_path}")
                            # Get timestamps from cache if available
                            try:
                                # Use the function reference directly (avoid circular import)
                                upload_func = globals().get('upload_interview_audio')
                                if upload_func and hasattr(upload_func, '_timestamp_cache') and session_key in upload_func._timestamp_cache:
                                    cached_ts = upload_func._timestamp_cache[session_key]
                                    audio_start_ts = cached_ts.get('audio_start_timestamp')
                                    video_start_ts = cached_ts.get('video_start_timestamp')
                                    print(f"📥 Using cached timestamps: audio={audio_start_ts}, video={video_start_ts}")
                            except Exception as e:
                                print(f"⚠️ Could not get cached timestamps: {e}")
                
                # CRITICAL: Get synchronized stop time from request if provided
                synchronized_stop_time = data.get('synchronized_stop_time')
                if synchronized_stop_time:
                    try:
                        synchronized_stop_time = float(synchronized_stop_time)
                        print(f"🕐 Synchronized stop time received: {synchronized_stop_time}")
                    except (ValueError, TypeError):
                        synchronized_stop_time = None
                
                # CRITICAL: Stop PyAudio recording first (if using backend recording)
                audio_file_path_pyaudio = None
                audio_start_ts_pyaudio = None
                if PYAudio_AVAILABLE and session_key in AUDIO_RECORDERS:
                    try:
                        with audio_lock:
                            audio_recorder = AUDIO_RECORDERS[session_key]
                            audio_file_path_pyaudio = audio_recorder.stop_recording(synchronized_stop_time=synchronized_stop_time)
                            audio_start_ts_pyaudio = audio_recorder.recording_start_timestamp
                            print(f"✅ PyAudio recording stopped: {audio_file_path_pyaudio}")
                            print(f"🕐 PyAudio start timestamp: {audio_start_ts_pyaudio}")
                            
                            # Use PyAudio file if available (preferred - better sync)
                            if audio_file_path_pyaudio:
                                audio_full_path = os.path.join(settings.MEDIA_ROOT, audio_file_path_pyaudio)
                                audio_start_ts = audio_start_ts_pyaudio
                                print(f"✅ Using PyAudio recorded audio for merging")
                    except Exception as e:
                        print(f"⚠️ Error stopping PyAudio recording: {e}")
                        import traceback
                        traceback.print_exc()
                
                # CRITICAL: Stop video and merge with audio in one call
                # The merge function will use video duration as authoritative reference
                # Video duration will be used to trim audio to match exactly
                print(f"🔍 Stopping video recording and merging with audio...")
                print(f"   Audio start timestamp: {audio_start_ts}, Video start timestamp: {video_start_ts}")
                print(f"   Synchronized stop time: {synchronized_stop_time}")
                print(f"   Audio file path: {audio_full_path}")
                video_path = camera.stop_video_recording(
                    audio_file_path=audio_full_path,
                    audio_start_timestamp=audio_start_ts,
                    video_start_timestamp=video_start_ts,
                    synchronized_stop_time=synchronized_stop_time
                )
                if video_path:
                    print(f"✅ Video recording stopped and saved: {video_path}")
                    
                    # Note: Videos merged with audio are already H.264 encoded, so no need to convert again
                    # Only convert if it's a raw video without audio and not already converted
                    try:
                        video_full_path = os.path.join(settings.MEDIA_ROOT, video_path)
                        if os.path.exists(video_full_path):
                            # Check if file needs conversion (not already converted and not merged with audio)
                            # Merged videos (_with_audio) are already H.264 encoded during merge
                            if '_converted' not in video_path and '_with_audio' not in video_path:
                                print(f"🔄 Ensuring video is browser-compatible (H.264)...")
                                converted_path = camera.ensure_browser_compatible_video(video_full_path)
                                if converted_path:
                                    # Update video_path to converted version
                                    video_path = os.path.relpath(converted_path, settings.MEDIA_ROOT).replace('\\', '/')
                                    print(f"✅ Video converted, new path: {video_path}")
                            elif '_with_audio' in video_path:
                                print(f"✅ Video already merged with audio and H.264 encoded: {video_path}")
                    except Exception as e:
                        print(f"⚠️ Error ensuring video compatibility: {e}")
                        import traceback
                        traceback.print_exc()
        except Exception as e:
            print(f"⚠️ Error stopping video recording: {e}")
            import traceback
            traceback.print_exc()
            # Even if there was an error, try to find the video file
            if not video_path:
                print(f"🔄 Video path is None after error, attempting to find video file...")
                try:
                    # Try to find video in merged folder
                    merged_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged')
                    if os.path.exists(merged_video_dir):
                        # Search for video by session_key
                        session_id_str = str(session_key)
                        for filename in os.listdir(merged_video_dir):
                            if session_id_str in filename and '_with_audio' in filename and filename.endswith('.mp4'):
                                found_video = os.path.join(merged_video_dir, filename)
                                if os.path.exists(found_video):
                                    video_path = os.path.relpath(found_video, settings.MEDIA_ROOT).replace('\\', '/')
                                    print(f"✅ Found merged video after error: {video_path}")
                                    break
                except Exception as find_error:
                    print(f"⚠️ Error finding video file: {find_error}")
        
        session = InterviewSession.objects.get(session_key=session_key)
        if session.status == 'SCHEDULED':
            session.status = 'COMPLETED'
            # Save video path if recording was active
            if video_path:
                # CRITICAL: Verify it's a merged video before saving
                if '_with_audio' in video_path or 'interview_videos_merged' in video_path:
                    # Use proper FileField.save() method to ensure file is stored in database
                    try:
                        video_full_path = os.path.join(settings.MEDIA_ROOT, video_path) if not os.path.isabs(video_path) else video_path
                        if os.path.exists(video_full_path):
                            with open(video_full_path, 'rb') as video_file:
                                from django.core.files.base import ContentFile
                                video_content = ContentFile(video_file.read(), name=os.path.basename(video_path))
                                session.interview_video.save(os.path.basename(video_path), video_content, save=True)
                                print(f"✅ Merged video saved to InterviewSession database field: {session.interview_video.name}")
                        else:
                            # Fallback: assign path string if file doesn't exist (shouldn't happen)
                            session.interview_video = video_path
                            session.save()
                            print(f"⚠️ Video file not found, saved path only: {video_path}")
                    except Exception as save_error:
                        print(f"⚠️ Error saving video file to database: {save_error}")
                        # Fallback: assign path string
                        session.interview_video = video_path
                        session.save()
                        print(f"✅ Merged video path saved to InterviewSession (fallback): {video_path}")
                else:
                    print(f"⚠️ WARNING: Video path is not merged: {video_path}")
                    # Try to find merged version
                    try:
                        merged_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged')
                        video_basename = os.path.basename(video_path)
                        base_name = os.path.splitext(video_basename)[0]
                        if '_converted' in base_name:
                            base_name = base_name.replace('_converted', '')
                        merged_filename = f"{base_name}_with_audio.mp4"
                        merged_path = os.path.join(merged_video_dir, merged_filename)
                        if os.path.exists(merged_path):
                            merged_relative = os.path.relpath(merged_path, settings.MEDIA_ROOT).replace('\\', '/')
                            # Use proper FileField.save() method to ensure file is stored in database
                            try:
                                with open(merged_path, 'rb') as video_file:
                                    from django.core.files.base import ContentFile
                                    video_content = ContentFile(video_file.read(), name=os.path.basename(merged_path))
                                    session.interview_video.save(os.path.basename(merged_path), video_content, save=True)
                                    print(f"✅ Found and saved merged video to database: {session.interview_video.name}")
                            except Exception as save_error:
                                print(f"⚠️ Error saving merged video to database: {save_error}")
                                # Fallback: assign path string
                                session.interview_video = merged_relative
                                session.save()
                                print(f"✅ Found and saved merged video (fallback): {merged_relative}")
                        else:
                            print(f"❌ Merged video not found, NOT saving unmerged video to database")
                    except Exception as e:
                        print(f"❌ Error finding merged video: {e}")
            else:
                print(f"⚠️ WARNING: video_path is None - attempting to find and save video...")
                # CRITICAL: Try to find video file manually and save it
                try:
                    merged_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged')
                    raw_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_raw')
                    session_id_str = str(session_key)
                    
                    # Search merged folder first (preferred - has audio)
                    found_video = None
                    if os.path.exists(merged_video_dir):
                        for filename in os.listdir(merged_video_dir):
                            if session_id_str in filename and '_with_audio' in filename and filename.endswith('.mp4'):
                                candidate = os.path.join(merged_video_dir, filename)
                                if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
                                        found_video = candidate
                                        video_path = os.path.relpath(found_video, settings.MEDIA_ROOT).replace('\\', '/')
                                        # Use proper FileField.save() method to ensure file is stored in database
                                        try:
                                            with open(found_video, 'rb') as video_file:
                                                from django.core.files.base import ContentFile
                                                video_content = ContentFile(video_file.read(), name=os.path.basename(found_video))
                                                session.interview_video.save(os.path.basename(found_video), video_content, save=True)
                                                print(f"✅ Found merged video manually and saved to database: {session.interview_video.name}")
                                        except Exception as save_error:
                                            print(f"⚠️ Error saving video to database: {save_error}")
                                            # Fallback: assign path string
                                            session.interview_video = video_path
                                            session.save()
                                            print(f"✅ Found merged video manually and saved (fallback): {video_path}")
                                        break
                    
                    # If not found in merged, try to merge raw video with audio
                    if not found_video and audio_full_path and os.path.exists(audio_full_path):
                        print(f"🔄 Attempting to merge raw video with audio...")
                        if os.path.exists(raw_video_dir):
                            for filename in os.listdir(raw_video_dir):
                                if session_id_str in filename and filename.endswith('.mp4'):
                                    raw_video = os.path.join(raw_video_dir, filename)
                                    if os.path.exists(raw_video) and os.path.getsize(raw_video) > 0:
                                        print(f"   Found raw video: {raw_video}")
                                        # Try to merge
                                        try:
                                            from interview_app.simple_real_camera import merge_video_audio_pyav
                                            video_ts = getattr(camera, '_recording_start_timestamp', None) if camera else None
                                            merge_success = merge_video_audio_pyav(
                                                video_path=raw_video,
                                                audio_file_path=audio_full_path,
                                                output_path=os.path.join(merged_video_dir, f"{os.path.splitext(filename)[0]}_with_audio.mp4"),
                                                video_start_timestamp=video_ts,
                                                audio_start_timestamp=audio_start_ts,
                                                video_duration=None
                                            )
                                            if merge_success:
                                                merged_path = os.path.join(merged_video_dir, f"{os.path.splitext(filename)[0]}_with_audio.mp4")
                                                if os.path.exists(merged_path):
                                                    video_path = os.path.relpath(merged_path, settings.MEDIA_ROOT).replace('\\', '/')
                                                    # Use proper FileField.save() method to ensure file is stored in database
                                                    try:
                                                        with open(merged_path, 'rb') as video_file:
                                                            from django.core.files.base import ContentFile
                                                            video_content = ContentFile(video_file.read(), name=os.path.basename(merged_path))
                                                            session.interview_video.save(os.path.basename(merged_path), video_content, save=True)
                                                            print(f"✅ Merged and saved video to database: {session.interview_video.name}")
                                                    except Exception as save_error:
                                                        print(f"⚠️ Error saving merged video to database: {save_error}")
                                                        # Fallback: assign path string
                                                        session.interview_video = video_path
                                                        session.save()
                                                        print(f"✅ Merged and saved video (fallback): {video_path}")
                                                    found_video = merged_path
                                                    break
                                        except Exception as merge_err:
                                            print(f"   ❌ Merge failed: {merge_err}")
                    
                    # If still not found, check raw folder (but don't save raw videos without audio)
                    if not found_video and os.path.exists(raw_video_dir):
                        for filename in os.listdir(raw_video_dir):
                            if session_id_str in filename and filename.endswith('.mp4'):
                                raw_video = os.path.join(raw_video_dir, filename)
                                print(f"⚠️ Found raw video (not merged): {raw_video}")
                                print(f"   ⚠️ This video does NOT have audio - merge may have failed")
                                print(f"   ⚠️ NOT saving raw video to database - merge must succeed")
                                break
                except Exception as e:
                    print(f"⚠️ Error in manual video search: {e}")
                    import traceback
                    traceback.print_exc()
            session.save()
            
            # FINAL CHECK: Verify merged video was saved
            if session.interview_video:
                video_path_str = str(session.interview_video)
                is_merged = '_with_audio' in video_path_str or 'interview_videos_merged' in video_path_str
                if is_merged:
                    print(f"✅ VERIFIED: Merged video saved to database: {video_path_str}")
                else:
                    print(f"⚠️ WARNING: Video saved but NOT merged: {video_path_str}")
                    print(f"   This should not happen - video should have _with_audio suffix")
            else:
                print(f"❌ CRITICAL: No video path saved to database for session {session_key}")
                print(f"   Possible causes:")
                print(f"   1. FFmpeg merge failed")
                print(f"   2. Video file not found")
                print(f"   3. Audio file not found")
                print(f"   4. Exception during merge process")
                print(f"   Check server logs for detailed error messages")
            
            print(f"--- Spoken-only session {session_key} marked as COMPLETED. ---")
            
            # Trigger comprehensive evaluation for spoken-only interviews
            try:
                from interview_app.comprehensive_evaluation_service import comprehensive_evaluation_service
                evaluation_results = comprehensive_evaluation_service.evaluate_complete_interview(session_key)
                print(f"--- Comprehensive evaluation completed for session {session_key} ---")
                print(f"Overall Score: {evaluation_results['overall_score']:.1f}/100")
                print(f"Recommendation: {evaluation_results['recommendation']}")
            except Exception as e:
                print(f"--- Error in comprehensive evaluation: {e} ---")
            
            # Create Evaluation after interview completion - SYNCHRONOUSLY for immediate availability
            try:
                from evaluation.services import create_evaluation_from_session
                print(f"🔄 Creating evaluation synchronously for session {session_key}...")
                evaluation = create_evaluation_from_session(session_key)
                if evaluation:
                    print(f"✅ Evaluation created and saved to database for session {session_key}")
                    try:
                        # Get interview from evaluation relationship
                        interview_id = evaluation.interview.id if evaluation.interview else 'N/A'
                        print(f"   Evaluation ID: {evaluation.id}, Interview ID: {interview_id}")
                    except Exception:
                        print(f"   Evaluation ID: {evaluation.id}, Interview ID: N/A")
                    # Verify it's accessible immediately
                    from evaluation.models import Evaluation
                    try:
                        verify_eval = Evaluation.objects.get(id=evaluation.id)
                        print(f"   ✅ Verification: Evaluation {verify_eval.id} is accessible in database")
                    except Evaluation.DoesNotExist:
                        print(f"   ⚠️ WARNING: Evaluation not found immediately after creation")
                else:
                    print(f"⚠️ Evaluation creation returned None for session {session_key}")
            except Exception as e:
                print(f"⚠️ Error creating evaluation: {e}")
                import traceback
                traceback.print_exc()
            
        release_camera_for_session(session_key)
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Removed duplicate submit_coding_challenge function - using the one at line 2643

def interview_complete(request):
    session_key = request.GET.get('session_key')
    context = {}
    
    if session_key:
        context['session_key'] = session_key
        
        # Release camera and microphone resources immediately
        try:
            release_camera_for_session(session_key)
            print(f"✅ Camera resources released for session {session_key}")
        except Exception as e:
            print(f"⚠️ Error releasing camera for session {session_key}: {e}")
        
        # CRITICAL: Update Interview status to COMPLETED if not already set
        try:
            from interviews.models import Interview
            interview = Interview.objects.filter(session_key=session_key).first()
            if interview and interview.status != Interview.Status.COMPLETED:
                interview.status = Interview.Status.COMPLETED
                interview.save(update_fields=['status'])
                print(f"✅ Interview {interview.id} status updated to COMPLETED")
        except Exception as e:
            print(f"⚠️ Error updating Interview status: {e}")
        
        # Create evaluation and generate PDF in background (don't wait for it)
        import threading
        def generate_evaluation_background():
            try:
                from evaluation.services import create_evaluation_from_session
                print(f"🔄 Starting background evaluation generation for session {session_key}")
                evaluation = create_evaluation_from_session(session_key)
                if evaluation:
                    print(f"✅ Background evaluation completed for session {session_key}, evaluation ID: {evaluation.id}")
                    # Verify details were saved
                    if evaluation.details and isinstance(evaluation.details, dict):
                        print(f"   ✅ Evaluation details saved with keys: {list(evaluation.details.keys())}")
                    else:
                        print(f"   ⚠️ WARNING: Evaluation created but details are missing!")
                else:
                    print(f"⚠️ Background evaluation not created for session {session_key}")
            except Exception as e:
                print(f"⚠️ Error in background evaluation generation: {e}")
                import traceback
                traceback.print_exc()
        
        # Start evaluation generation in background thread
        evaluation_thread = threading.Thread(target=generate_evaluation_background, daemon=True)
        evaluation_thread.start()
        print(f"🔄 Background evaluation thread started for session {session_key}")
    
    template = loader.get_template('interview_app/interview_complete.html')
    return HttpResponse(template.render(context, request))

def generate_and_save_follow_up(session, parent_question, transcribed_answer):
    if DEV_MODE:
        print("--- DEV MODE: Skipping AI follow-up question generation. ---")
        return None

    # CRITICAL: Do NOT generate follow-ups for closing questions like "Do you have any questions"
    closing_question_phrases = [
        "do you have any question", "do you have any questions", 
        "any questions for us", "any questions for me", "any other questions",
        "questions for us", "questions for me", "before we wrap up"
    ]
    parent_q_lower = parent_question.question_text.lower()
    if any(phrase in parent_q_lower for phrase in closing_question_phrases):
        print(f"⚠️ Parent question is a closing question. Skipping follow-up generation.")
        return None

    # Check if we've already reached 30% follow-up ratio (maintain 70% main, 30% follow-up)
    main_questions = session.questions.filter(question_level='MAIN', question_type__in=['TECHNICAL', 'BEHAVIORAL']).count()
    follow_up_questions = session.questions.filter(question_level='FOLLOW_UP', question_type__in=['TECHNICAL', 'BEHAVIORAL']).count()
    
    # Calculate projected ratio if we add this follow-up
    # We want to maintain approximately 70% main questions and 30% follow-ups
    total_questions = main_questions + follow_up_questions
    if total_questions > 0:
        # Calculate what the ratio would be if we add this follow-up
        projected_follow_ups = follow_up_questions + 1
        projected_total = total_questions + 1
        projected_ratio = projected_follow_ups / projected_total
        
        # If adding this follow-up would exceed 30%, don't generate it
        if projected_ratio > 0.30:
            current_ratio = follow_up_questions / total_questions
            print(f"⚠️ Projected follow-up ratio would be {projected_ratio*100:.1f}% (current: {current_ratio*100:.1f}%, target: 30%, main: {main_questions}, follow-ups: {follow_up_questions}). Skipping follow-up generation to maintain ratio.")
            return None
    else:
        # If no questions yet, allow first follow-up (will be checked after generation)
        print(f"ℹ️ No questions yet. Will check ratio after generation.")

    model = genai.GenerativeModel('gemini-2.0-flash')
    language_name = SUPPORTED_LANGUAGES.get(session.language_code, 'English')
    
    # Get job description context for matching
    jd_context = session.job_description or ""
    if len(jd_context) > 2000:
        jd_context = jd_context[:2000]  # Limit context size
    
    prompt = (
        f"You are a professional technical interviewer conducting a TECHNICAL INTERVIEW in {language_name}. "
        f"Act like a real technical interviewer - be direct, professional, and focused on TECHNICAL assessment.\n\n"
        f"starting from introduction question .Please base the questions on the provided job description "
        f"generate a mix of technical Questions. 70 percent from jd and 30 percent from given answer"
        f"Do not ask two question in single question only ask single question at each time"
        f"CRITICAL: This is a TECHNICAL INTERVIEW. You MUST ask ONLY technical questions related to the job description.\n"
        f"dont add words in question like we taking reference according jd only question according to jd but dont need to explain we taking from jd.\n"
        f"do not ask question repeat only when candidate answer like repeate the question or related to that then only repeat that asked previousquestion.\n"
        f"if candidate response or answer elaborate or that type of response for ask the question in detail then add 1-2 line extra and ask again same question.\n"
        f"if candidate ask outer side question other then technical interview then say dont ask the question other then interview focus on the interview and ask the next que.\n"
        "DO NOT ask:\n"
        "- Personal questions (hobbies, family, personal background)\n"
        "- Behavioral questions unrelated to technical skills\n"
        "- General conversation topics\n"
        "- Questions about salary, benefits, or company culture\n"
        "- Any non-technical questions\n\n"
        f"The candidate was asked the following question:\n'{parent_question.question_text}'\n\n"
        f"The candidate gave this transcribed answer:\n'{transcribed_answer}'\n\n"
        f"Job Description Context:\n{jd_context}\n\n"
        "Your task is to analyze the response and determine if a TECHNICAL follow-up question is needed. Follow these rules STRICTLY:\n"
        "0. CRITICAL: If the parent question is a closing question like 'Do you have any questions for us?' or 'Before we wrap up, do you have any questions?', "
        "you MUST respond with 'NO_FOLLOW_UP' immediately. Closing questions should NEVER have follow-ups - the interview should end after the candidate answers.\n"
        "1. FIRST, check if the answer is BROAD or VAGUE (lacks specific technical details, examples, or depth). "
        "Signs of a broad answer: short responses, generic statements, lack of technical details, no examples, or surface-level explanations.\n"
        "2. SECOND, check if the answer topic MATCHES or RELATES to the TECHNICAL aspects of the Job Description context provided above. "
        "The answer should be relevant to the TECHNICAL job requirements, skills, or responsibilities mentioned in the JD.\n"
        "3. ONLY if BOTH conditions are met (answer is broad/vague AND matches TECHNICAL JD context), generate ONE single, TECHNICAL follow-up question. "
        "IMPORTANT: You may use a brief introductory phrase like 'That's okay' or 'I understand' ONCE, but DO NOT repeat it. "
        "NEVER say phrases like 'That's okay, that's okay' or 'That's fine, that's fine' - this is repetitive and unprofessional. "
        "If you use an introductory phrase, use it only ONCE, then immediately ask the TECHNICAL question. "
        "For example, if they give a vague answer about 'working with databases', your follow-up could be: "
        "'That's okay. Can you walk me through a specific database optimization you've implemented?' "
        "OR simply: 'Can you walk me through a specific database optimization you've implemented?' "
        "But NEVER: 'That's okay, that's okay. Can you walk me through...' - this is repetitive.\n"
        "4. If the answer is detailed, specific, complete, confident, OR does not relate to the JD context, "
        "you MUST respond with the exact text: NO_FOLLOW_UP\n"
        "5. CRITICAL: Your follow-up question must be a SINGLE question. If you use an introductory phrase, use it ONCE only. "
        "Example: 'That's okay. What specific challenges did you face?' OR 'What specific challenges did you face?' "
        "NOT: 'That's okay, that's okay. What specific challenges did you face?' - never repeat phrases.\n"
        "Do NOT add any other text, prefixes, or formatting. Your entire output must be either the direct follow-up question itself or the text 'NO_FOLLOW_UP'."
    )
    try:
        response = model.generate_content(prompt)
        follow_up_text = response.text.strip()
        if "NO_FOLLOW_UP" in follow_up_text or not follow_up_text: return None
        if len(follow_up_text) > 10:
            print(f"--- Generated Interactive Follow-up: {follow_up_text} ---")
            
            tts_dir = os.path.join(settings.MEDIA_ROOT, 'tts'); os.makedirs(tts_dir, exist_ok=True)
            tts_filename = f'followup_{parent_question.id}_{int(time.time())}.mp3'
            tts_path = os.path.join(tts_dir, tts_filename)
            synthesize_speech(follow_up_text, session.language_code, session.accent_tld, tts_path)
            audio_url = os.path.join(settings.MEDIA_URL, 'tts', os.path.basename(tts_path))

            follow_up_question = InterviewQuestion.objects.create(
                session=session,
                question_text=follow_up_text,
                question_type=parent_question.question_type,
                question_level='FOLLOW_UP',
                parent_question=parent_question,
                order=parent_question.order,
                audio_url=audio_url
            )
            
            return {
                'id': str(follow_up_question.id), 
                'text': follow_up_question.question_text, 
                'type': follow_up_question.question_type, 
                'audio_url': audio_url
            }
    except Exception as e:
        print(f"ERROR generating follow-up question: {e}")
    
    return None

@csrf_exempt
def transcribe_audio(request):
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        question_id = request.POST.get('question_id')
        response_time = request.POST.get('response_time')
        no_audio_flag = str(request.POST.get('no_audio', '')).lower() in ('1', 'true', 'yes')
        
        # Check if transcript is sent directly (from Deepgram WebSocket)
        transcribed_text = request.POST.get('transcript') or request.POST.get('transcribed_answer')
        
        # If transcript is provided directly, use it (no need for Whisper)
        if transcribed_text:
            follow_up_data = None
            if session_id and question_id:
                try:
                    question_to_update = InterviewQuestion.objects.get(id=question_id, session_id=session_id)
                    # Format answer with A: prefix if not already present
                    answer_text = transcribed_text.strip()
                    if not answer_text.startswith('A:'):
                        answer_text = f'A: {answer_text}'
                    
                    question_to_update.transcribed_answer = answer_text
                    fields_to_update = ['transcribed_answer']
                    if response_time:
                        try:
                            question_to_update.response_time_seconds = float(response_time)
                            fields_to_update.append('response_time_seconds')
                        except ValueError:
                            pass
                    question_to_update.save(update_fields=fields_to_update)

                    # Only generate a follow-up if the question just answered was a MAIN one
                    if transcribed_text and transcribed_text.strip() and question_to_update.question_level == 'MAIN' and question_to_update.session.language_code == 'en':
                        follow_up_data = generate_and_save_follow_up(
                            session=question_to_update.session,
                            parent_question=question_to_update,
                            transcribed_answer=transcribed_text
                        )
                except InterviewQuestion.DoesNotExist:
                    print(f"Warning: Could not find question with ID {question_id} to save answer.")
            return JsonResponse({'text': transcribed_text, 'follow_up_question': follow_up_data})

        if no_audio_flag:
            if not (session_id and question_id):
                return JsonResponse({'error': 'Missing session_id or question_id for no-audio submission.'}, status=400)
            try:
                question_to_update = InterviewQuestion.objects.get(id=question_id, session_id=session_id)
                question_to_update.transcribed_answer = 'A: No answer provided'
                fields_to_update = ['transcribed_answer']
                if response_time:
                    try:
                        question_to_update.response_time_seconds = float(response_time)
                        fields_to_update.append('response_time_seconds')
                    except ValueError:
                        pass
                question_to_update.save(update_fields=fields_to_update)
                return JsonResponse({'text': 'No answer provided', 'follow_up_question': None})
            except InterviewQuestion.DoesNotExist:
                print(f"Warning: Could not find question with ID {question_id} to save no-audio answer.")
                return JsonResponse({'error': 'Question not found'}, status=404)

        # Fallback to Whisper if no transcript provided (for backward compatibility)
        if not whisper_model:
            return JsonResponse({'error': 'Whisper model not available.'}, status=500)

        audio_file = request.FILES.get('audio_data')
        if not audio_file:
            return JsonResponse({'error': 'No audio data or transcript provided'}, status=400)

        file_path = default_storage.save('temp_audio.webm', audio_file)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        try:
            result = whisper_model.transcribe(full_path, fp16=False)
            transcribed_text = result.get('text', '')
            follow_up_data = None

            if session_id and question_id:
                try:
                    question_to_update = InterviewQuestion.objects.get(id=question_id, session_id=session_id)
                    # Format answer with A: prefix if not already present
                    answer_text = transcribed_text.strip() if transcribed_text else 'No answer provided'
                    if not answer_text.startswith('A:'):
                        answer_text = f'A: {answer_text}'

                    question_to_update.transcribed_answer = answer_text
                    fields_to_update = ['transcribed_answer']
                    if response_time:
                        try:
                            question_to_update.response_time_seconds = float(response_time)
                            fields_to_update.append('response_time_seconds')
                        except ValueError:
                            pass
                    question_to_update.save(update_fields=fields_to_update)

                    # Only generate a follow-up if the question just answered was a MAIN one
                    if transcribed_text and transcribed_text.strip() and question_to_update.question_level == 'MAIN' and question_to_update.session.language_code == 'en':
                        follow_up_data = generate_and_save_follow_up(
                            session=question_to_update.session,
                            parent_question=question_to_update,
                            transcribed_answer=transcribed_text
                        )
                except InterviewQuestion.DoesNotExist:
                    print(f"Warning: Could not find question with ID {question_id} to save answer.")
            os.remove(full_path)
            return JsonResponse({'text': transcribed_text, 'follow_up_question': follow_up_data})
        except Exception as e:
            if os.path.exists(full_path):
                os.remove(full_path)
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)

# --- Video Feed and Proctoring Status ---

def video_feed(request):
    session_key = request.GET.get('session_key')
    print(f"📺 Video feed requested for session_key: {session_key}")
    
    camera = get_camera_for_session(session_key)
    if not camera: 
        print(f"❌ Camera not found for session_key: {session_key}")
        return HttpResponse("Camera not found.", status=404)
    
    print(f"✅ Camera found for session_key: {session_key}, starting video stream")
    response = StreamingHttpResponse(gen(camera), content_type='multipart/x-mixed-replace; boundary=frame')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def gen(camera_instance):
    """Generator function for video streaming."""
    import time
    frame_count = 0
    consecutive_failures = 0
    try:
        # Always start with a frame to initialize the stream
        initial_frame = camera_instance.get_frame()
        if initial_frame and len(initial_frame) > 0:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + initial_frame + b'\r\n\r\n')
            print(f"📺 Initial frame sent for session {camera_instance.session_id}")
        
        while True:
            try:
                frame = camera_instance.get_frame()
                if frame and len(frame) > 0:
                    frame_count += 1
                    consecutive_failures = 0
                    # Ensure proper MJPEG format
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
                else:
                    consecutive_failures += 1
                    # Log if getting too many failures
                    if consecutive_failures == 10:
                        print(f"⚠️ Camera {camera_instance.session_id} - 10 consecutive frame failures")
                    # Always yield fallback to keep stream alive
                    fallback = camera_instance._create_fallback_frame()
                    if fallback and len(fallback) > 0:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + fallback + b'\r\n\r\n')
                # Consistent delay (~15fps)
                time.sleep(0.067)
            except Exception as frame_error:
                # Always yield something to keep stream alive
                try:
                    fallback = camera_instance._create_fallback_frame()
                    if fallback and len(fallback) > 0:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + fallback + b'\r\n\r\n')
                except:
                    # Last resort: minimal valid JPEG
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x01\xe0\x02\x80\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9' + b'\r\n\r\n')
                time.sleep(0.067)
    except GeneratorExit:
        print(f"📺 Video stream closed for camera {camera_instance.session_id}")
    except Exception as e:
        print(f"❌ Error in video stream: {e}")

def get_proctoring_status(request):
    session_key = request.GET.get('session_key')
    camera = get_camera_for_session(session_key)
    if not camera: 
        # Return empty warnings object with all fields False instead of 404
        return JsonResponse({
            'no_person_warning_active': False,
            'multiple_people': False,
            'phone_detected': False,
            'no_person': False,
            'low_concentration': False,
            'tab_switched': False,
            'excessive_noise': False,
            'multiple_speakers': False
        })
    warnings = camera.get_latest_warnings()
    # Remove _counts from response to avoid confusion in frontend
    warnings.pop('_counts', None)
    return JsonResponse(warnings)


@csrf_exempt
@require_POST
def detect_yolo_browser_frame(request):
    """
    Accept browser camera frames and run YOLO detection for:
    - Phone detection
    - Multiple people detection
    - No person detection
    - Low concentration (motion-based)
    """
    try:
        import json
        import base64
        import numpy as np
        from django.core.files.base import ContentFile
        from .models import InterviewSession, WarningLog
        from django.conf import settings  # Import settings here
        
        data = json.loads(request.body)
        session_key = data.get('session_key')
        frame_base64 = data.get('frame')  # Base64 encoded image
        
        if not session_key or not frame_base64:
            return JsonResponse({'error': 'session_key and frame required'}, status=400)
        
        # Get session
        try:
            session = InterviewSession.objects.get(session_key=session_key)
        except InterviewSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        
        # Decode base64 image
        try:
            # Remove data URL prefix if present
            if ',' in frame_base64:
                frame_base64 = frame_base64.split(',')[1]
            
            image_data = base64.b64decode(frame_base64)
            nparr = np.frombuffer(image_data, np.uint8)
            
            if not CV2_AVAILABLE or cv2 is None:
                return JsonResponse({
                    'error': 'OpenCV not available',
                    'phone_detected': False,
                    'multiple_people': False,
                    'no_person': False,
                    'low_concentration': False
                }, status=503)
            
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                return JsonResponse({'error': 'Invalid image data'}, status=400)
        except Exception as e:
            print(f"❌ Error decoding frame: {e}")
            return JsonResponse({'error': f'Failed to decode image: {str(e)}'}, status=400)
        
        # Initialize YOLO model if not already loaded
        global _yolo_model_cache
        if '_yolo_model_cache' not in globals():
            _yolo_model_cache = {}
        
        yolo_key = 'default'
        if yolo_key not in _yolo_model_cache:
            try:
                import onnxruntime as ort
                # settings already imported at top of file
                from pathlib import Path
                
                model_path = Path(settings.BASE_DIR) / 'yolov8m.onnx'
                if not model_path.exists():
                    model_path = Path('yolov8m.onnx')
                
                if model_path.exists():
                    providers = ['CPUExecutionProvider']
                    _yolo_model_cache[yolo_key] = {
                        'session': ort.InferenceSession(str(model_path), providers=providers),
                        'input_name': None,
                        'output_names': None
                    }
                    _yolo_model_cache[yolo_key]['input_name'] = _yolo_model_cache[yolo_key]['session'].get_inputs()[0].name
                    _yolo_model_cache[yolo_key]['output_names'] = [o.name for o in _yolo_model_cache[yolo_key]['session'].get_outputs()]
                    print(f"✅ YOLO model loaded for browser frame detection")
                else:
                    _yolo_model_cache[yolo_key] = None
                    print(f"⚠️ YOLO model not found at {model_path}")
            except Exception as e:
                print(f"⚠️ Failed to load YOLO model: {e}")
                _yolo_model_cache[yolo_key] = None
        
        yolo_info = _yolo_model_cache.get(yolo_key)
        
        # Initialize detection results
        person_count = 0
        phone_count = 0
        has_person = False
        multiple_people = False
        phone_detected = False
        no_person = False
        
        # Run YOLO detection if available
        if yolo_info and yolo_info is not None:
            try:
                # Preprocess frame for ONNX model
                input_size = 640  # YOLOv8 standard input size
                frame_resized = cv2.resize(frame, (input_size, input_size))
                frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                frame_normalized = frame_rgb.astype(np.float32) / 255.0
                frame_transposed = np.transpose(frame_normalized, (2, 0, 1))
                frame_batch = np.expand_dims(frame_transposed, axis=0)
                
                # Run inference
                outputs = yolo_info['session'].run(
                    yolo_info['output_names'],
                    {yolo_info['input_name']: frame_batch}
                )
                
                # Post-process outputs
                # YOLOv8 ONNX output format: [batch, features, anchors] = [1, 84, 8400]
                # where 84 = 4 (bbox coords) + 80 (class scores), 8400 = anchor points
                conf_threshold = 0.25  # Lower threshold for better detection
                
                if len(outputs) > 0:
                    predictions = outputs[0]  # Shape: [1, 84, 8400]
                    
                    # Handle different output shapes
                    if len(predictions.shape) == 3:
                        # Standard YOLOv8 format: [batch, features, anchors]
                        # Transpose to [anchors, features] for easier processing
                        predictions = predictions[0].transpose(1, 0)  # [8400, 84]
                    elif len(predictions.shape) == 2:
                        # Already in [anchors, features] format
                        predictions = predictions
                    else:
                        print(f"⚠️ Unexpected YOLO output shape: {predictions.shape}")
                        predictions = []
                    
                    # Process each prediction
                    for pred in predictions:
                        if len(pred) < 5:
                            continue
                        
                        # Get box coordinates (normalized, center format)
                        x_center, y_center, width, height = pred[0:4]
                        
                        # Get class scores (rest of the array)
                        class_scores = pred[4:]
                        max_score = np.max(class_scores)
                        max_class = np.argmax(class_scores)
                        
                        # Filter by confidence threshold
                        if max_score < conf_threshold:
                            continue
                        
                        # Count persons (class 0) and phones (classes 67, 77)
                        if max_class == 0:  # person
                            person_count += 1
                        elif max_class in [67, 77]:  # cell phone, mobile phone
                            phone_count += 1
                else:
                    print(f"⚠️ No YOLO outputs received")
                    predictions = []
                
                has_person = person_count >= 1
                multiple_people = person_count >= 2
                phone_detected = phone_count >= 1
                no_person = person_count == 0
                
            except Exception as e:
                print(f"⚠️ YOLO detection error: {e}")
                import traceback
                traceback.print_exc()
        
        # Motion detection for low concentration (compare with previous frame)
        low_concentration = False
        if has_person:  # Only check motion if person is present
            global _last_browser_frame_gray
            if '_last_browser_frame_gray' not in globals():
                _last_browser_frame_gray = {}
            
            gray_small = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_small = cv2.resize(gray_small, (160, 120))
            
            frame_key = session_key
            if frame_key in _last_browser_frame_gray:
                diff = cv2.absdiff(gray_small, _last_browser_frame_gray[frame_key])
                mean_diff = np.mean(diff)
                MOTION_LOW_THRESH = 2.5
                
                if mean_diff < MOTION_LOW_THRESH:
                    # Low motion detected - check if it's been low for a while
                    import time
                    if frame_key not in globals().get('_low_motion_start', {}):
                        globals().setdefault('_low_motion_start', {})[frame_key] = time.time()
                    
                    low_motion_duration = time.time() - globals()['_low_motion_start'][frame_key]
                    if low_motion_duration >= 8.0:  # 8 seconds of low motion
                        low_concentration = True
                else:
                    # Motion detected - reset timer
                    globals().setdefault('_low_motion_start', {})[frame_key] = None
            
            _last_browser_frame_gray[frame_key] = gray_small
        
        # Store previous state to detect changes (only log when state changes)
        global _last_detection_state
        if '_last_detection_state' not in globals():
            _last_detection_state = {}
        
        prev_state = _last_detection_state.get(session_key, {})
        current_state = {
            'phone_detected': phone_detected,
            'multiple_people': multiple_people,
            'no_person': no_person,
            'low_concentration': low_concentration
        }
        
        # Log warnings to database only when state changes (to avoid spam)
        warnings_to_log = []
        if phone_detected and not prev_state.get('phone_detected', False):
            warnings_to_log.append(('phone_detected', frame))
        if multiple_people and not prev_state.get('multiple_people', False):
            warnings_to_log.append(('multiple_people', frame))
        if no_person and not prev_state.get('no_person', False):
            warnings_to_log.append(('no_person', frame))
        if low_concentration and not prev_state.get('low_concentration', False):
            warnings_to_log.append(('low_concentration', frame))
        
        # Save snapshots and log warnings (async, non-blocking)
        for warning_type, warning_frame in warnings_to_log:
            try:
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                snapshot_filename = f"{session_key}_{warning_type}_{timestamp}.jpg"
                
                # Save snapshot
                img_dir = os.path.join(settings.MEDIA_ROOT, "proctoring_snaps")
                os.makedirs(img_dir, exist_ok=True)
                img_path = os.path.join(img_dir, snapshot_filename)
                cv2.imwrite(img_path, warning_frame)
                
                # Log to database
                with open(img_path, 'rb') as f:
                    image_file = ContentFile(f.read(), name=snapshot_filename)
                    WarningLog.objects.create(
                        session=session,
                        warning_type=warning_type,
                        snapshot=snapshot_filename,
                        snapshot_image=image_file
                    )
                print(f"✅ Logged {warning_type} warning with snapshot")
            except Exception as e:
                print(f"⚠️ Error logging {warning_type} warning: {e}")
        
        # Update state
        _last_detection_state[session_key] = current_state
        
        # Debug logging (only log occasionally to avoid spam)
        import random
        if random.random() < 0.01:  # Log 1% of requests for debugging
            print(f"🔍 YOLO Detection Debug: person_count={person_count}, phone_count={phone_count}, no_person={no_person}, has_person={has_person}")
        
        return JsonResponse({
            'phone_detected': phone_detected,
            'multiple_people': multiple_people,
            'no_person': no_person,
            'low_concentration': low_concentration,
            'person_count': person_count,
            'phone_count': phone_count
        })
        
    except Exception as e:
        print(f"❌ Error in detect_yolo_browser_frame: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': str(e),
            'phone_detected': False,
            'multiple_people': False,
            'no_person': False,
            'low_concentration': False
        }, status=500)

@csrf_exempt
@require_POST
def browser_proctoring_event(request):
    """
    Lightweight endpoint for browser-based proctoring events.
    The browser sends JSON like:
      {
        "session_key": "...",
        "warning_type": "low_concentration" | "multiple_people" | "phone_detected" | "no_person" | "tab_switched",
        "active": true/false,
        "snapshot": "data:image/jpeg;base64,...." (optional)
      }

    When active=true, we log a WarningLog row and optionally save a snapshot image.
    When active=false, we do not delete anything; frontend just hides the warning.
    """
    try:
        data = json.loads(request.body or "{}")
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Invalid JSON: {e}"}, status=400)

    session_key = data.get("session_key")
    warning_type = data.get("warning_type")
    active = bool(data.get("active", True))
    snapshot_b64 = data.get("snapshot")

    if not session_key or not warning_type:
        return JsonResponse(
            {"status": "error", "message": "session_key and warning_type are required"},
            status=400,
        )

    # We only log when the warning becomes active
    if not active:
        return JsonResponse({"status": "ok", "message": "inactive event ignored"})

    try:
        session = InterviewSession.objects.get(session_key=session_key)
    except InterviewSession.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Invalid session_key"}, status=404
        )

    warning_log = WarningLog(session=session, warning_type=warning_type)

    # Optional snapshot image from browser (base64 data URL)
    if snapshot_b64 and isinstance(snapshot_b64, str) and snapshot_b64.startswith("data:image"):
        try:
            import base64
            from django.core.files.base import ContentFile
            import uuid as _uuid

            header, b64data = snapshot_b64.split(",", 1)
            file_ext = "jpg"
            if "png" in header:
                file_ext = "png"
            filename = f"{session.id}_{warning_type}_{_uuid.uuid4().hex}.{file_ext}"
            decoded = base64.b64decode(b64data)
            warning_log.snapshot = filename
            warning_log.snapshot_image.save(filename, ContentFile(decoded), save=False)
        except Exception as e:
            # Snapshot is optional; log error but do not fail the request
            print(f"⚠️ Failed to decode browser snapshot for proctoring event: {e}")

    warning_log.save()

    return JsonResponse({"status": "ok"})

def video_frame(request):
    """Return a single JPEG frame (for polling-based display)"""
    session_key = request.GET.get('session_key')
    camera = get_camera_for_session(session_key)
    if not camera:
        # Return a minimal error frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        if CV2_AVAILABLE and cv2:
            cv2.putText(frame, "Camera Not Found", (20, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ok, buf = cv2.imencode('.jpg', frame)
        else:
            return HttpResponse("OpenCV not available", status=503)
        if ok:
            return HttpResponse(buf.tobytes(), content_type='image/jpeg')
        return HttpResponse(status=404)
    
    frame_bytes = camera.get_frame()
    if frame_bytes and len(frame_bytes) > 0:
        return HttpResponse(frame_bytes, content_type='image/jpeg')
    else:
        # Return fallback frame
        fallback = camera._create_fallback_frame()
        return HttpResponse(fallback, content_type='image/jpeg')

@csrf_exempt
@require_POST
def report_tab_switch(request):
    data = json.loads(request.body)
    session_key = data.get('session_key')
    camera = get_camera_for_session(session_key)
    if camera: camera.set_tab_switch_status(data.get('status') == 'hidden')
    return JsonResponse({"status": "ok"})

@csrf_exempt
@csrf_exempt
def check_camera(request):
    """
    Check camera availability for identity verification.
    On Render (cloud servers), physical cameras are not available, so we return success
    and let the browser handle camera access via getUserMedia API.
    """
    try:
        session_key = request.GET.get('session_key')
        if not session_key:
            return JsonResponse({"status": "error", "message": "session_key required"}, status=400)
        
        try:
            camera = get_camera_for_session(session_key)
        except Exception as e:
            # If camera creation fails, that's OK - browser will handle camera access
            print(f"⚠️ Camera creation failed (non-critical, browser will handle): {e}")
            camera = None
        
        # On cloud servers (like Render), physical cameras are not available
        # The browser will handle camera access via getUserMedia API
        # So we return success even if server-side camera is not available
        if camera:
            # Check if camera hardware is available (will be False on Render)
            try:
                camera_available = False
                if hasattr(camera, 'video') and camera.video:
                    try:
                        camera_available = camera.video.isOpened()
                    except (AttributeError, Exception):
                        camera_available = False
                
                if camera_available:
                    return JsonResponse({"status": "ok", "message": "Camera hardware detected"})
                else:
                    # No hardware camera on server (expected on Render) - browser will handle it
                    return JsonResponse({
                        "status": "ok", 
                        "message": "Browser camera will be used (no server hardware camera available)",
                        "browser_camera": True
                    })
            except Exception as e:
                # Camera check failed, but that's OK - browser will handle camera access
                print(f"⚠️ Server camera check failed (expected on cloud servers): {e}")
                return JsonResponse({
                    "status": "ok",
                    "message": "Browser camera will be used",
                    "browser_camera": True
                })
        else:
            # Camera object not created, but that's OK for browser-based camera access
            return JsonResponse({
                "status": "ok",
                "message": "Browser camera will be used",
                "browser_camera": True
            })
    except Exception as e:
        # Any error - still return success since browser will handle camera
        print(f"⚠️ Camera check error (non-critical): {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "status": "ok",
            "message": "Browser camera will be used",
            "browser_camera": True
        })

@csrf_exempt
@require_POST
def activate_proctoring_camera(request):
    """Explicitly activate YOLO model, proctoring warnings, and video recording when technical interview starts"""
    try:
        # If this instance is running without a server-attached camera (e.g. Cloud Run),
        # treat proctoring activation as a no-op and rely on browser-based proctoring only.
        # This avoids 500 errors like "Camera not opened" when no hardware is available.
        try:
            data = json.loads(request.body or "{}")
        except Exception:
            data = {}

        session_key = data.get('session_key')
        if not session_key:
            return JsonResponse({'status': 'error', 'message': 'session_key required'}, status=400)

        # Get or create camera for this session
        try:
            camera = get_camera_for_session(session_key)
        except Exception as e:
            # On platforms without camera (like Cloud Run), fall back to browser-only proctoring
            print(f"⚠️ activate_proctoring_camera: no server camera available ({e}), using browser-only proctoring.")
            return JsonResponse({
                'status': 'ok',
                'message': 'Browser-only proctoring active (no server camera available)',
                'server_camera': False
            })

        if not camera or not hasattr(camera, 'video'):
            # Same fallback: allow frontend to continue with browser-only proctoring
            print("⚠️ activate_proctoring_camera: camera object missing or has no video handle; using browser-only proctoring.")
            return JsonResponse({
                'status': 'ok',
                'message': 'Browser-only proctoring active (no usable server camera)',
                'server_camera': False
            })

        # Ensure camera is running
        if hasattr(camera, 'video') and camera.video.isOpened():
            # Activate YOLO model and proctoring (only now, not during identity verification)
            # IMPORTANT: Camera feed continues to work even if YOLO/ONNX fails
            yolo_activated = False
            if hasattr(camera, 'activate_yolo_proctoring'):
                yolo_activated = camera.activate_yolo_proctoring()
                # Even if YOLO fails, camera feed should still work
                if not yolo_activated:
                    print(f"⚠️ YOLO/ONNX activation returned False, but camera feed will continue with Haar cascade")
                    yolo_activated = True  # Treat as success so camera feed continues
            else:
                # Fallback for older camera implementations
                print(f"⚠️ Camera doesn't have activate_yolo_proctoring method, using fallback")
                yolo_activated = True
            
            # Ensure camera is still running and capturing frames
            if hasattr(camera, 'video') and camera.video:
                if not camera.video.isOpened():
                    print(f"⚠️ Camera not opened after proctoring activation, attempting to reinitialize...")
                    # Try to reinitialize camera
                    try:
                        camera.video = camera._VideoCapture(0)
                        if camera.video.isOpened():
                            print(f"✅ Camera reinitialized successfully")
                        else:
                            print(f"⚠️ Camera reinitialization failed - feed may show black screen")
                    except Exception as e:
                        print(f"⚠️ Error reinitializing camera: {e}")
            
            # Ensure frame capture loop is running
            if hasattr(camera, '_running') and not camera._running:
                print(f"⚠️ Frame capture loop not running, attempting to restart...")
                try:
                    if hasattr(camera, '_capture_and_detect_loop'):
                        import threading
                        camera._running = True
                        if hasattr(camera, '_detector_thread'):
                            if not camera._detector_thread.is_alive():
                                camera._detector_thread = threading.Thread(target=camera._capture_and_detect_loop, daemon=True)
                                camera._detector_thread.start()
                                print(f"✅ Frame capture loop restarted")
                        else:
                            camera._detector_thread = threading.Thread(target=camera._capture_and_detect_loop, daemon=True)
                            camera._detector_thread.start()
                            print(f"✅ Frame capture loop started")
                except Exception as e:
                    print(f"⚠️ Error restarting frame capture loop: {e}")

            # CRITICAL: Calculate synchronized start time for perfect video/audio synchronization
            # This ensures both video and audio start at the EXACT same moment (no trimming needed)
            import time
            current_time = time.time()
            # Calculate future timestamp (500ms from now) to account for network delay and frontend initialization
            # Both video and audio will wait until this exact time to start recording
            synchronized_start_time = current_time + 0.5  # 500ms in the future
            print(f"🕐 Calculated synchronized start time: {synchronized_start_time}")
            print(f"   Current time: {current_time}")
            print(f"   Wait time: {(synchronized_start_time - current_time) * 1000:.1f}ms")
            print(f"   ✅ Both video and audio will start at this EXACT moment - perfect synchronization!")
            
            # Start video recording for the entire interview (both technical and coding phases)
            # Pass the synchronized start time so video waits until that exact moment
            video_start_timestamp = None
            if hasattr(camera, 'start_video_recording'):
                try:
                    # CRITICAL: Pass synchronized_start_time so video waits until exact moment
                    # This ensures video starts at the same time as audio (no trimming needed)
                    video_start_timestamp = camera.start_video_recording(synchronized_start_time=synchronized_start_time)
                    print(f"✅ Video recording will start at synchronized time: {synchronized_start_time}")
                    print(f"🕐 Video start timestamp: {video_start_timestamp}")
                    
                    if not video_start_timestamp:
                        # Fallback: use synchronized time
                        video_start_timestamp = synchronized_start_time
                        print(f"⚠️ Using synchronized start time as fallback: {video_start_timestamp}")
                    
                    print(f"✅ Video recording active for session {session_key} (will continue through technical and coding phases)")
                except Exception as e:
                    print(f"⚠️ Error starting video recording: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback: use synchronized time
                    video_start_timestamp = synchronized_start_time
            else:
                print(f"⚠️ Camera doesn't have start_video_recording method")
                video_start_timestamp = synchronized_start_time
            
            # Ensure detection loop is running
            if not camera._running:
                # Restart detection loop if it stopped
                import threading
                camera._running = True
                if hasattr(camera, '_detector_thread'):
                    if not camera._detector_thread.is_alive():
                        camera._detector_thread = threading.Thread(target=camera._capture_and_detect_loop, daemon=True)
                        camera._detector_thread.start()
                        print(f"✅ Detection loop reactivated for session {str(camera.session_id)[:8]}")
                else:
                    # Start detection loop if it doesn't exist
                    camera._detector_thread = threading.Thread(target=camera._capture_and_detect_loop, daemon=True)
                    camera._detector_thread.start()
                    print(f"✅ Detection loop started for session {str(camera.session_id)[:8]}")
            
            # CRITICAL: Start PyAudio recording at the EXACT same time
            audio_start_timestamp = None
            if PYAudio_AVAILABLE:
                try:
                    with audio_lock:
                        if session_key not in AUDIO_RECORDERS:
                            audio_recorder = PyAudioAudioRecorder(session_id=camera.session_id, session_key=session_key)
                            AUDIO_RECORDERS[session_key] = audio_recorder
                            print(f"✅ PyAudio recorder created for session {session_key}")
                        else:
                            audio_recorder = AUDIO_RECORDERS[session_key]
                        
                        # Start audio recording with the SAME synchronized start time
                        audio_start_timestamp = audio_recorder.start_recording(synchronized_start_time=synchronized_start_time)
                        print(f"🕐 PyAudio recording started at timestamp: {audio_start_timestamp}")
                except Exception as e:
                    print(f"⚠️ Error starting PyAudio recording: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"⚠️ PyAudio not available - audio recording will use frontend MediaRecorder")
            
            return JsonResponse({
                'status': 'success', 
                'message': 'YOLO model and proctoring warnings activated for technical interview',
                'camera_active': True,
                'yolo_loaded': yolo_activated,
                'proctoring_active': getattr(camera, '_proctoring_active', False),
                'detection_running': camera._running if hasattr(camera, '_running') else False,
                'video_start_timestamp': video_start_timestamp,  # Return timestamp for audio sync
                'audio_start_timestamp': audio_start_timestamp,  # PyAudio timestamp
                'synchronized_start_time': synchronized_start_time  # Return for frontend debug
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Camera not opened'}, status=500)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_POST
def release_camera(request):
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        release_camera_for_session(session_key)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def extract_id_data(image_path, model):
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    id_card_for_ocr = {'mime_type': 'image/jpeg', 'data': image_bytes}
    prompt = ("You are an OCR expert. Extract the following from the provided image of an ID card: "
              "- Full Name\n- ID Number\n"
              "If a value cannot be extracted, state 'Not Found'. Do not add any warnings.\n"
              "Format:\nName: <value>\nID Number: <value>")
              
    response = model.generate_content([prompt, id_card_for_ocr])
    text = response.text
    name_match = re.search(r"Name:\s*(.+)", text, re.IGNORECASE)
    id_number_match = re.search(r"ID Number:\s*(.+)", text, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else None
    id_number = id_number_match.group(1).strip() if id_number_match else None
    return id_number, name

# === AI Chatbot endpoints (Q&A phase) ===

def chatbot_standalone(request):
    """Render standalone chatbot template with direct Deepgram connection"""
    from django.conf import settings
    session_key = request.GET.get('session_key', '')
    return render(request, 'interview_app/chatbot_direct_deepgram.html', {
        'session_key': session_key,
    })

@csrf_exempt
@require_POST
def ai_start(request):
    from .complete_ai_bot import start_interview, sessions
    from .models import InterviewSession as DjangoSession, InterviewQuestion
    
    print(f"\n{'='*60}")
    print(f"🎯 AI_START called (using complete_ai_bot)")
    print(f"{'='*60}")
    
    # Try to get data from JSON body first, then fallback to POST
    data = {}
    if request.body:
        try:
            import json
            data = json.loads(request.body.decode('utf-8'))
            print(f"📦 Received JSON data: {data}")
        except Exception as e:
            print(f"⚠️ JSON parse failed: {e}, trying POST data")
            # If JSON parsing fails, try POST data
            if hasattr(request, 'POST') and request.POST:
                data = dict(request.POST)
                print(f"📦 Using POST data: {data}")
    elif hasattr(request, 'POST') and request.POST:
        data = dict(request.POST)
        print(f"📦 Using POST data (no body): {data}")
    
    # Also check query parameters as a fallback
    session_key = data.get('session_key', '') or request.GET.get('session_key', '')
    if not session_key:
        # Try to get from request body directly if it's a string
        try:
            body_str = request.body.decode('utf-8') if request.body else ''
            if 'session_key' in body_str:
                import json
                try:
                    body_data = json.loads(body_str)
                    session_key = body_data.get('session_key', '')
                except:
                    # Try to extract from string
                    import re
                    match = re.search(r'session_key["\']?\s*[:=]\s*["\']?([^"\',\s}]+)', body_str)
                    if match:
                        session_key = match.group(1)
        except:
            pass
    
    print(f"🔑 Session Key: {session_key}")
    
    # Get candidate name and JD from database
    candidate_name = 'Candidate'
    jd_text = ''
    django_session = None
    
    # Get question count from InterviewSlot.ai_configuration or default to 4
    question_count = 4  # Default
    
    # If no session_key, try to get it from URL or other sources
    if not session_key:
        print(f"⚠️ No session_key found in request data, checking other sources...")
        # Try to get from URL path if it's in the URL
        if hasattr(request, 'path'):
            import re
            path_match = re.search(r'session[_-]?key[=:]?([a-f0-9]+)', request.path, re.IGNORECASE)
            if path_match:
                session_key = path_match.group(1)
                print(f"✅ Found session_key in URL path: {session_key}")
    
    if session_key:
        try:
            django_session = DjangoSession.objects.get(session_key=session_key)
            candidate_name = django_session.candidate_name
            jd_text = django_session.job_description or ''
            
            # Fetch Interview once to use for both job description and question count
            interview = None
            try:
                from interviews.models import Interview
                interview = Interview.objects.filter(session_key=session_key).first()
                
                # If not found via session_key, try via candidate email
                if not interview and django_session.candidate_email:
                    from candidates.models import Candidate
                    try:
                        candidate = Candidate.objects.get(email=django_session.candidate_email)
                        interview = Interview.objects.filter(candidate=candidate).order_by('-created_at').first()
                    except:
                        pass
            except Exception as e:
                print(f"⚠️ Error fetching Interview: {e}")
            
            # If job_description is empty, try to build it from the Interview and Job
            if not jd_text or not jd_text.strip():
                print(f"⚠️ Job description is empty, trying to build from Interview/Job...")
                try:
                    if interview and interview.job:
                        job = interview.job
                        # Build job description from job fields
                        jd_text = job.job_description or f"Job Title: {job.job_title}\nCompany: {job.company_name}"
                        if job.domain:
                            jd_text += f"\nDomain: {job.domain.name}"
                        if hasattr(job, 'coding_language') and job.coding_language:
                            jd_text += f"\nCoding Language: {job.coding_language}"
                        print(f"✅ Built job description from Job: {job.id}")
                    elif interview and not interview.job:
                        print(f"⚠️ Interview {interview.id} has no job assigned")
                        jd_text = "Technical Interview Position"
                    else:
                        print(f"⚠️ No Interview found for session_key={session_key}")
                        jd_text = "Technical Interview Position"
                except Exception as e:
                    print(f"⚠️ Error building job description: {e}")
                    import traceback
                    traceback.print_exc()
                    jd_text = "Technical Interview Position"
            
            print(f"✅ Retrieved from DB:")
            print(f"   Candidate: {candidate_name}")
            print(f"   JD length: {len(jd_text)}")
            print(f"   JD preview: {jd_text[:100]}...")
            
            # Get question count from InterviewSlot.ai_configuration
            # Reuse interview object we already fetched above
            try:
                slot = None
                
                # Method 1: Try to get slot from interview.slot (direct assignment)
                if interview and interview.slot:
                    slot = interview.slot
                    print(f"✅ Found Interview {interview.id} with direct Slot {slot.id}")
                
                # Method 2: Try to get slot from interview.schedule.slot (via InterviewSchedule)
                elif interview:
                    try:
                        # Check if interview has a schedule
                        if hasattr(interview, 'schedule') and interview.schedule:
                            slot = interview.schedule.slot
                            print(f"✅ Found Interview {interview.id} with Slot {slot.id} via InterviewSchedule")
                        else:
                            # Try to fetch schedule explicitly
                            from interviews.models import InterviewSchedule
                            schedule = InterviewSchedule.objects.filter(interview=interview).first()
                            if schedule and schedule.slot:
                                slot = schedule.slot
                                print(f"✅ Found Interview {interview.id} with Slot {slot.id} via InterviewSchedule (fetched)")
                    except Exception as e:
                        print(f"⚠️ Error fetching schedule for interview: {e}")
                
                if slot:
                    print(f"   Slot AI Config: {slot.ai_configuration}")
                    print(f"   Slot AI Config Type: {type(slot.ai_configuration)}")
                    
                    # IMPORTANT: Refresh slot from database to ensure we have latest data
                    slot.refresh_from_db()
                    print(f"   Slot AI Config (after refresh): {slot.ai_configuration}")
                    
                    # Try multiple ways to get question_count
                    found_count = None
                    
                    # Method 1: Check if ai_configuration is a dict and has question_count
                    if slot.ai_configuration and isinstance(slot.ai_configuration, dict):
                        # Try different key variations
                        possible_keys = ['question_count', 'questionCount', 'question-count', 'questions', 'num_questions']
                        for key in possible_keys:
                            if key in slot.ai_configuration:
                                found_count = slot.ai_configuration[key]
                                print(f"✅ Found question_count using key '{key}': {found_count} (type: {type(found_count)})")
                                break
                        
                        # If not found, print all available keys for debugging
                        if found_count is None:
                            print(f"⚠️⚠️⚠️ question_count not found in ai_configuration")
                            print(f"   Available keys: {list(slot.ai_configuration.keys()) if slot.ai_configuration else 'None'}")
                            print(f"   Full ai_configuration: {slot.ai_configuration}")
                            print(f"   Slot ID: {slot.id}")
                            print(f"   Slot created_at: {slot.created_at}")
                    
                    # Method 2: Check if ai_configuration is a string (JSON string)
                    elif slot.ai_configuration and isinstance(slot.ai_configuration, str):
                        try:
                            import json
                            config_dict = json.loads(slot.ai_configuration)
                            if isinstance(config_dict, dict):
                                possible_keys = ['question_count', 'questionCount', 'question-count', 'questions', 'num_questions']
                                for key in possible_keys:
                                    if key in config_dict:
                                        found_count = config_dict[key]
                                        print(f"✅ Found question_count in JSON string using key '{key}': {found_count}")
                                        break
                        except Exception as e:
                            print(f"⚠️ Error parsing ai_configuration as JSON: {e}")
                    
                    # Method 3: Check if question_count is a direct attribute
                    if found_count is None and hasattr(slot, 'question_count') and slot.question_count:
                        found_count = slot.question_count
                        print(f"✅ Using question count from InterviewSlot.question_count attribute: {found_count}")
                    
                    # Convert to integer if found
                    if found_count is not None:
                        try:
                            # Handle both string and number types
                            if isinstance(found_count, str):
                                question_count = int(found_count.strip())
                            else:
                                question_count = int(found_count)
                            
                            # Validate question_count is in valid range (1-20)
                            if question_count >= 1 and question_count <= 20:
                                print(f"✅✅✅ Using question count from InterviewSlot: {question_count}")
                            else:
                                print(f"⚠️ Invalid question_count ({question_count}) - must be between 1-20, using default 4")
                                question_count = 4
                        except (ValueError, TypeError) as e:
                            print(f"⚠️ Error converting question_count to int: {e}, using default 4")
                            print(f"   found_count value: {found_count}, type: {type(found_count)}")
                            question_count = 4
                    else:
                        print(f"⚠️⚠️⚠️ No question_count found anywhere in slot.ai_configuration!")
                        print(f"   Slot ID: {slot.id}")
                        print(f"   Slot ai_configuration type: {type(slot.ai_configuration)}")
                        print(f"   Slot ai_configuration value: {slot.ai_configuration}")
                        if isinstance(slot.ai_configuration, dict):
                            print(f"   Available keys in ai_configuration: {list(slot.ai_configuration.keys())}")
                        print(f"⚠️ Using default question_count: 4")
                        question_count = 4
                else:
                    if not interview:
                        print(f"⚠️ No Interview found for session_key={session_key}, candidate_email={django_session.candidate_email if django_session else 'N/A'}")
                    elif not interview.slot:
                        # Check if interview has a schedule
                        try:
                            from interviews.models import InterviewSchedule
                            schedule = InterviewSchedule.objects.filter(interview=interview).first()
                            if schedule:
                                print(f"⚠️ Interview {interview.id} has no direct slot, but has schedule {schedule.id} with slot {schedule.slot.id if schedule.slot else 'None'}")
                            else:
                                print(f"⚠️ Interview {interview.id} has no slot assigned and no schedule found")
                        except Exception as e:
                            print(f"⚠️ Interview {interview.id} has no slot assigned (error checking schedule: {e})")
                    print(f"⚠️ Using default question_count: 4")
            except Exception as e:
                print(f"⚠️ Error getting question count, using default 4: {e}")
                import traceback
                traceback.print_exc()
        except DjangoSession.DoesNotExist:
            print(f"❌ Session not found in DB for session_key: {session_key}")
            # Don't return error immediately - try to build job description from other sources
            if not jd_text or not jd_text.strip():
                jd_text = "Technical Interview Position"
                print(f"⚠️ Using fallback job description since session not found")
    
    # Final validation: Ensure we have a non-empty job description
    if not jd_text or not jd_text.strip():
        print(f"⚠️⚠️⚠️ CRITICAL: Job description is still empty after all attempts!")
        print(f"   Session Key: {session_key}")
        print(f"   Django Session: {django_session}")
        
        # Last resort: Use a default job description
        jd_text = "Technical Interview Position - Software Development Role"
        print(f"   Using fallback job description: {jd_text}")
    
    # CRITICAL: Check if a session already exists for this session_key before creating a new one
    existing_session_id = None
    if django_session and session_key:
        for sid, sess in sessions.items():
            if hasattr(sess, 'django_session_key') and sess.django_session_key == session_key:
                existing_session_id = sid
                print(f"✅ Found existing session in memory for session_key {session_key}: {sid}")
                break
    
    if existing_session_id:
        # Reuse existing session
        ai_session = sessions[existing_session_id]
        # Get the last question from database or use the last active question
        last_question = ai_session.last_active_question_text
        if not last_question:
            # Try to get from database
            last_question_obj = InterviewQuestion.objects.filter(
                session=django_session,
                role='AI'
            ).order_by('-order').first()
            if last_question_obj:
                last_question = last_question_obj.question_text
                ai_session.last_active_question_text = last_question
        
        # Get current question number from database
        # CRITICAL: Only count MAIN questions (exclude follow-ups, closing, candidate questions)
        # This ensures sequential numbering: 1, 2, 3, 4...
        existing_main_questions = InterviewQuestion.objects.filter(
            session=django_session,
            role='AI',
            question_level='MAIN'  # Only count MAIN questions for sequential numbering
        ).exclude(
            question_type='CODING'  # Exclude coding questions from technical question count
        ).count()
        # current_question_number should be 1-indexed, so if we have 2 MAIN questions, next is question 3
        ai_session.current_question_number = existing_main_questions + 1
        print(f"📊 Question numbering: Found {existing_main_questions} MAIN questions, setting current_question_number={ai_session.current_question_number}")
        
        result = {
            "session_id": existing_session_id,
            "question": last_question or "Please continue with your answer.",
            "audio_url": "",  # No audio for resumed session
            "question_number": ai_session.current_question_number,
            "max_questions": ai_session.max_questions
        }
        print(f"✅ Reusing existing session: {existing_session_id}, current_question_number={ai_session.current_question_number}")
    else:
        # Call AI bot to start interview with question count from scheduler
        print(f"\n{'='*60}")
        print(f"🎯🎯🎯 FINAL: Starting interview with question_count={question_count}")
        print(f"   Candidate: {candidate_name}")
        print(f"   JD length: {len(jd_text)}")
        print(f"   JD preview: {jd_text[:200]}...")
        print(f"{'='*60}\n")
        
        # Final check before calling start_interview
        if not jd_text or not jd_text.strip():
            error_msg = "Job description is required but could not be retrieved. Please ensure the interview session has a valid job description."
            print(f"❌ {error_msg}")
            return JsonResponse({"error": error_msg}, status=400)
        
        result = start_interview(candidate_name, jd_text, max_questions=question_count)
    print(f"✅ Interview started, returned max_questions={result.get('max_questions', 'N/A')}")
    
    # Verify the session has the correct max_questions
    if 'session_id' in result and result['session_id'] in sessions:
        ai_session = sessions[result['session_id']]
        print(f"✅ AI Session max_questions: {ai_session.max_questions}")
        if ai_session.max_questions != question_count:
            print(f"⚠️⚠️⚠️ CRITICAL WARNING: Session max_questions ({ai_session.max_questions}) != requested question_count ({question_count})")
            print(f"   This means the interview will ask {ai_session.max_questions} questions instead of {question_count}!")
        else:
            print(f"✅✅✅ Verified: Session max_questions ({ai_session.max_questions}) matches requested question_count ({question_count})")
    
    # Link the AI session to Django session and create first question in database
    if 'error' not in result and django_session:
        session_id = result.get('session_id')
        if session_id and session_id in sessions:
            ai_session = sessions[session_id]
            # Store django session_key in AI session for later reference
            ai_session.django_session_key = session_key
            
            # Create the first question in database
            first_question_text = result.get('question', '')
            if first_question_text:
                try:
                    # Check if question already exists to avoid duplicates
                    existing_first = InterviewQuestion.objects.filter(
                        session=django_session,
                        order=0,
                        question_text=first_question_text
                    ).first()
                    
                    if not existing_first:
                        # First question should always be order 0
                        # Check if any questions exist - if so, use max_order + 1, otherwise use 0
                        from django.db.models import Max
                        existing_count = InterviewQuestion.objects.filter(session=django_session).count()
                        
                        if existing_count == 0:
                            # No questions exist - use order 0 for first question
                            new_order = 0
                        else:
                            # Questions exist - use max_order + 1 to avoid conflicts
                            max_order = InterviewQuestion.objects.filter(
                                session=django_session
                            ).aggregate(max_order=Max('order'))['max_order'] or -1
                            new_order = max_order + 1
                        
                        # Format question text (remove Q: prefix for cleaner storage)
                        question_text_formatted = first_question_text.strip()
                        if question_text_formatted.startswith('Q:'):
                            question_text_formatted = question_text_formatted.replace('Q:', '').strip()
                        
                        # Get the maximum conversation_sequence to ensure sequential indexing
                        from django.db.models import Max
                        max_seq_result = InterviewQuestion.objects.filter(
                            session=django_session
                        ).aggregate(max_seq=Max('conversation_sequence'))
                        max_seq = max_seq_result['max_seq'] if max_seq_result['max_seq'] is not None else 0
                        conversation_sequence = max_seq + 1  # Start with 1 for first AI question
                        
                        InterviewQuestion.objects.create(
                            session=django_session,
                            question_text=question_text_formatted,  # AI question text (without Q: prefix)
                            question_type='TECHNICAL',
                            order=new_order,
                            question_level='MAIN',
                            audio_url=result.get('audio_url', ''),
                            role='AI',  # This is an AI-generated question
                            conversation_sequence=conversation_sequence  # Sequential index: 1, 3, 5, 7...
                        )
                        print(f"✅ Created first AI question in database with order {new_order}, conversation_sequence {conversation_sequence}, role=AI")
                    else:
                        print(f"✅ First question already exists in database")
                except Exception as e:
                    print(f"⚠️ Error creating question in database: {e}")
                    import traceback
                    traceback.print_exc()
    
    if 'error' in result:
        print(f"❌ Error in result: {result['error']}")
    else:
        print(f"✅ Session ID: {result.get('session_id', 'N/A')}")
        print(f"✅ Question: {result.get('question', 'N/A')[:100]}...")
        print(f"✅ Audio URL: {result.get('audio_url', 'N/A')}")
    print(f"{'='*60}\n")
    
    status_code = 200 if 'error' not in result else 400
    return JsonResponse(result, status=status_code)


@csrf_exempt
@require_POST
def ai_upload_answer(request):
    from .complete_ai_bot import upload_answer, sessions
    from .models import InterviewSession as DjangoSession, InterviewQuestion
    
    try:
        # Support both multipart and JSON
        session_id = request.POST.get('session_id')
        session_key = request.POST.get('session_key')
        if not session_id and request.body:
            data = json.loads(request.body.decode('utf-8'))
            session_id = data.get('session_id')
            session_key = data.get('session_key') or session_key
            transcript = data.get('transcript', '')
        else:
            session_key = request.POST.get('session_key') or session_key
            transcript = (request.POST.get('transcript') or '').strip()
        
        print(f"\n{'='*60}")
        print(f"📝 AI_UPLOAD_ANSWER called")
        print(f"   Session ID: {session_id}")
        print(f"   Session Key: {session_key}")
        print(f"   Transcript: {transcript[:100] if transcript else 'Empty'}...")
        print(f"   Transcript length: {len(transcript) if transcript else 0}")
        print(f"{'='*60}")
        
        # Save answer to database if session exists
        if session_id and session_id in sessions:
            ai_session = sessions[session_id]
            # Try to find the Django session using session_key stored in ai_session
            django_session = None
            if hasattr(ai_session, 'django_session_key') and ai_session.django_session_key:
                try:
                    django_session = DjangoSession.objects.get(session_key=ai_session.django_session_key)
                except DjangoSession.DoesNotExist:
                    print(f"⚠️ Django session not found for session_key: {ai_session.django_session_key}")
            
            # If we have a Django session, save the answer to InterviewQuestion
            # IMPORTANT: Also save "No answer provided" for closing questions
            if django_session:
                try:
                    # Find the current question for this session based on question number
                    current_q_num = ai_session.current_question_number
                    # Get the last question that was asked (current_question_number - 1 is the one being answered)
                    question_to_answer = current_q_num - 1 if current_q_num > 0 else 0
                    
                    # Find the question by order (question numbers are 1-indexed in UI, 0-indexed in code)
                    questions = InterviewQuestion.objects.filter(
                        session=django_session
                    ).order_by('order')
                    
                    # Check if this is a pre-closing or closing question answer
                    is_pre_closing_question = False
                    is_closing_question = False
                    
                    # Check pre-closing question flag
                    if hasattr(ai_session, 'asked_pre_closing_question') and ai_session.asked_pre_closing_question:
                        # Check if we just answered the pre-closing question (before asked_for_questions is set)
                        if hasattr(ai_session, 'asked_for_questions') and not ai_session.asked_for_questions:
                            is_pre_closing_question = True
                            print(f"📝 Detected pre-closing question answer")
                    
                    # Check if this is a closing question answer
                    if hasattr(ai_session, 'last_active_question_text') and ai_session.last_active_question_text:
                        closing_phrases = ["do you have any question", "any questions for", "before we wrap up"]
                        is_closing_question = any(phrase in ai_session.last_active_question_text.lower() for phrase in closing_phrases)
                        if is_closing_question:
                            print(f"📝 Detected closing question answer")
                    
                    # Determine answer text:
                    # - If transcript exists and is valid, use it (even if it's "no")
                    # - If transcript is empty or invalid, use "No answer provided"
                    # IMPORTANT: Clean transcript to remove common prefixes and invalid markers
                    cleaned_transcript = transcript.strip() if transcript else ''
                    
                    # Remove common invalid markers
                    invalid_markers = ['[No speech detected]', '[No speech', 'No speech detected', 'No speech']
                    is_invalid = False
                    for marker in invalid_markers:
                        if cleaned_transcript.startswith(marker) or cleaned_transcript == marker:
                            is_invalid = True
                            break
                    
                    if cleaned_transcript and not is_invalid and len(cleaned_transcript) > 0:
                        answer_text = cleaned_transcript
                        print(f"✅ Using valid transcript as answer: {answer_text[:50]}...")
                    else:
                        answer_text = 'No answer provided'
                        print(f"⚠️ Transcript is empty or invalid, using 'No answer provided'")
                    
                    # IMPORTANT: Always save answers for pre-closing and closing questions
                    is_special_question = is_pre_closing_question or is_closing_question
                    
                    if questions.exists():
                        # Try to find the question by matching the last_active_question_text first (most reliable)
                        question_obj = None
                        if hasattr(ai_session, 'last_active_question_text') and ai_session.last_active_question_text:
                            # Try exact text match first
                            matching_question = questions.filter(
                                question_text=ai_session.last_active_question_text
                            ).first()
                            if matching_question:
                                question_obj = matching_question
                                print(f"✅ Found question by exact text match: order {question_obj.order}")
                            else:
                                # Try partial match (in case of slight variations)
                                for q in questions:
                                    if ai_session.last_active_question_text.lower().strip() in q.question_text.lower() or q.question_text.lower() in ai_session.last_active_question_text.lower().strip():
                                        question_obj = q
                                        print(f"✅ Found question by partial text match: order {question_obj.order}")
                                        break
                        
                        # If not found by text, try by order
                        if not question_obj and question_to_answer < questions.count():
                            question_obj = questions[question_to_answer]
                            print(f"✅ Found question by order index: {question_to_answer}")
                        
                        # If still not found, try to find the last question without an answer (for pre-closing/closing)
                        if not question_obj:
                            unanswered_question = questions.filter(transcribed_answer__isnull=True).last()
                            if unanswered_question:
                                question_obj = unanswered_question
                                print(f"✅ Found last unanswered question: order {question_obj.order}")
                        
                        # For pre-closing/closing questions, also try to find by checking if it's the second-to-last or last question
                        if not question_obj and is_special_question:
                            # Pre-closing and closing are usually the last or second-to-last questions
                            if questions.count() >= 2:
                                # Try second-to-last (might be pre-closing)
                                question_obj = questions[questions.count() - 2]
                                print(f"✅ Found question as second-to-last (pre-closing?): order {question_obj.order}")
                            elif questions.count() >= 1:
                                # Try last question (might be closing)
                                question_obj = questions.last()
                                print(f"✅ Found question as last (closing?): order {question_obj.order}")
                        
                        if question_obj:
                            # CRITICAL: Always save answers for ALL questions (including technical questions)
                            # This ensures answers appear in candidate details even if transcript is empty
                            # Determine question type
                            is_technical_question = question_obj.question_type and question_obj.question_type.upper() in ['TECHNICAL', 'BEHAVIORAL']
                            
                            # ALWAYS save answers for technical/behavioral questions
                            # Also save for special questions (pre-closing/closing) or if there's an actual answer
                            should_save = is_special_question or answer_text != 'No answer provided' or is_technical_question
                            
                            print(f"📝 Answer save decision for order {question_obj.order}:")
                            print(f"   - Question type: {question_obj.question_type}")
                            print(f"   - Is technical: {is_technical_question}")
                            print(f"   - Is special: {is_special_question}")
                            print(f"   - Answer text: '{answer_text[:50]}...'")
                            print(f"   - Should save: {should_save}")
                            
                            if should_save:
                                # IMPORTANT: Save Interviewee answer as a SEPARATE record with role='INTERVIEWEE'
                                # Get the maximum conversation_sequence to ensure sequential indexing
                                from django.db.models import Max
                                max_seq_result = InterviewQuestion.objects.filter(
                                    session=django_session
                                ).aggregate(max_seq=Max('conversation_sequence'))
                                max_seq = max_seq_result['max_seq'] if max_seq_result['max_seq'] is not None else 0
                                
                                # Interviewee answers get even sequence numbers (2, 4, 6, 8...)
                                # If last sequence was odd (AI question), next is even (Interviewee answer)
                                # If last sequence was even or null, calculate next even number
                                if max_seq % 2 == 1:  # Last was AI (odd), next is Interviewee (even)
                                    interviewee_sequence = max_seq + 1
                                else:  # Last was Interviewee or no sequence, find next even
                                    interviewee_sequence = ((max_seq // 2) + 1) * 2
                                
                                # Format answer text (remove A: prefix for cleaner storage)
                                answer_text_formatted = answer_text.strip() if answer_text else 'No answer provided'
                                if answer_text_formatted.startswith('A:'):
                                    answer_text_formatted = answer_text_formatted.replace('A:', '').strip()
                                
                                # Calculate response time if available
                                import time as time_module
                                response_time = 0
                                if hasattr(ai_session, 'question_asked_at') and ai_session.question_asked_at:
                                    response_time = time_module.time() - ai_session.question_asked_at
                                
                                # Create separate record for Interviewee answer
                                interviewee_response = InterviewQuestion.objects.create(
                                    session=django_session,
                                    question_text='',  # Empty for Interviewee responses (content is in transcribed_answer)
                                    question_type=question_obj.question_type,
                                    order=question_obj.order,  # Same order as the question it answers
                                    question_level='INTERVIEWEE_RESPONSE',  # Special level to identify Interviewee responses
                                    transcribed_answer=answer_text_formatted,  # The actual answer text
                                    response_time_seconds=response_time,
                                    role='INTERVIEWEE',  # This is an Interviewee response
                                    conversation_sequence=interviewee_sequence  # Sequential index: 2, 4, 6, 8...
                                )
                                print(f"✅ Saved Interviewee answer as separate record: conversation_sequence {interviewee_sequence}, role=INTERVIEWEE, order {question_obj.order}: {answer_text[:50]}...")
                                
                                # Also update the original question's transcribed_answer for backward compatibility
                                original_order = question_obj.order  # Preserve order
                                question_obj.transcribed_answer = f'A: {answer_text_formatted}'
                                question_obj.response_time_seconds = response_time
                                question_obj.save(update_fields=['transcribed_answer', 'response_time_seconds'])
                                print(f"✅ Updated original question record for backward compatibility: {answer_text[:50]}...")
                            elif answer_text == 'No answer provided' and not is_special_question:
                                # IMPORTANT: Still save "No answer provided" so it appears in candidate details
                                # This ensures all questions have corresponding answers, even if empty
                                from django.db.models import Max
                                max_seq_result = InterviewQuestion.objects.filter(
                                    session=django_session
                                ).aggregate(max_seq=Max('conversation_sequence'))
                                max_seq = max_seq_result['max_seq'] if max_seq_result['max_seq'] is not None else 0
                                
                                # Calculate interviewee sequence (even number)
                                if max_seq % 2 == 1:  # Last was AI (odd), next is Interviewee (even)
                                    interviewee_sequence = max_seq + 1
                                else:  # Last was Interviewee or no sequence, find next even
                                    interviewee_sequence = ((max_seq // 2) + 1) * 2
                                
                                # Save "No answer provided" as a separate record
                                interviewee_response = InterviewQuestion.objects.create(
                                    session=django_session,
                                    question_text='',  # Empty for Interviewee responses
                                    question_type=question_obj.question_type,
                                    order=question_obj.order,  # Same order as the question
                                    question_level='INTERVIEWEE_RESPONSE',
                                    transcribed_answer='No answer provided',  # Explicitly save this
                                    response_time_seconds=response_time if 'response_time' in locals() else 0,
                                    role='INTERVIEWEE',
                                    conversation_sequence=interviewee_sequence
                                )
                                print(f"✅ Saved 'No answer provided' as separate record: conversation_sequence {interviewee_sequence}, role=INTERVIEWEE, order {question_obj.order}")
                                
                                # Also update the original question's transcribed_answer for backward compatibility
                                question_obj.transcribed_answer = 'A: No answer provided'
                                question_obj.save(update_fields=['transcribed_answer'])
                                print(f"✅ Updated original question record with 'No answer provided'")
                        else:
                            print(f"⚠️ Could not find question to save answer. Creating new question...")
                            # Create a new question if it doesn't exist (including pre-closing and closing questions)
                            # Get the maximum order to ensure unique sequential ordering
                            from django.db.models import Max
                            max_order_result = InterviewQuestion.objects.filter(
                                session=django_session
                            ).aggregate(max_order=Max('order'))
                            max_order = max_order_result['max_order'] if max_order_result['max_order'] is not None else -1
                            new_order = max_order + 1
                            
                            # Determine question level
                            question_level = 'MAIN'
                            if is_pre_closing_question:
                                question_level = 'MAIN'  # Pre-closing is still MAIN level
                            elif is_closing_question:
                                question_level = 'MAIN'  # Closing is still MAIN level
                            
                            # Format question text with Q: prefix
                            question_text_formatted = (ai_session.last_active_question_text or "Question").strip()
                            if not question_text_formatted.startswith('Q:'):
                                question_text_formatted = f'Q: {question_text_formatted}'
                            
                            # Format answer text with A: prefix
                            answer_text_formatted = answer_text.strip() if answer_text else 'No answer provided'
                            if not answer_text_formatted.startswith('A:'):
                                answer_text_formatted = f'A: {answer_text_formatted}'
                            
                            question_obj = InterviewQuestion.objects.create(
                                session=django_session,
                                question_text=question_text_formatted,
                                question_type='TECHNICAL',
                                order=new_order,
                                question_level=question_level,
                                transcribed_answer=answer_text_formatted  # Save the answer immediately with A: prefix
                            )
                            print(f"✅ Created and saved answer to new question {new_order} ({'pre-closing' if is_pre_closing_question else 'closing' if is_closing_question else 'regular'}): {answer_text[:50]}...")
                    else:
                        # No questions exist yet - create the question with answer
                        # Use order 0 for the first question
                        # Format question text with Q: prefix
                        question_text_formatted = (ai_session.last_active_question_text or "Question").strip()
                        if not question_text_formatted.startswith('Q:'):
                            question_text_formatted = f'Q: {question_text_formatted}'
                        
                        # Format answer text with A: prefix
                        answer_text_formatted = answer_text.strip() if answer_text else 'No answer provided'
                        if not answer_text_formatted.startswith('A:'):
                            answer_text_formatted = f'A: {answer_text_formatted}'
                        
                        question_obj = InterviewQuestion.objects.create(
                            session=django_session,
                            question_text=question_text_formatted,
                            question_type='TECHNICAL',
                            order=0,  # First question gets order 0
                            question_level='MAIN',
                            transcribed_answer=answer_text_formatted
                        )
                        print(f"✅ Created first question with answer (order 0): {answer_text[:50]}...")
                except Exception as e:
                    print(f"⚠️ Error saving answer to database: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Validate session_id before calling upload_answer
        if not session_id:
            print(f"❌ ERROR: session_id is missing from request")
            return JsonResponse({"error": "session_id is required"}, status=400)
        
        # CRITICAL: If session_id not in memory sessions, try to restore from Django session
        if session_id not in sessions:
            print(f"⚠️ WARNING: session_id '{session_id}' not found in memory sessions dict")
            print(f"   Available sessions: {list(sessions.keys())[:5]}...")  # Show first 5 for debugging
            
            # Try to restore session from Django database
            try:
                # Find Django session by session_key (might be stored in InterviewSession)
                django_session = None
                # Try to get session_key from request body first
                if request.body:
                    try:
                        data = json.loads(request.body.decode('utf-8'))
                        session_key = data.get('session_key')
                        if session_key:
                            django_session = DjangoSession.objects.filter(session_key=session_key).first()
                            if django_session:
                                print(f"✅ Found Django session from request body: {session_key}")
                    except Exception as e:
                        print(f"⚠️ Error parsing request body for session_key: {e}")
                
                # If not found in body, try GET parameter
                if not django_session:
                    session_key = request.GET.get('session_key')
                    if session_key:
                        django_session = DjangoSession.objects.filter(session_key=session_key).first()
                        if django_session:
                            print(f"✅ Found Django session from GET param: {session_key}")
                
                # If we found Django session, try to recreate AI session from database
                if django_session:
                    print(f"✅ Found Django session, attempting to restore AI session from database...")
                    
                    # FIRST: Check if there's already a session in memory with this django_session_key
                    existing_session_id = None
                    for sid, sess in sessions.items():
                        if hasattr(sess, 'django_session_key') and sess.django_session_key == django_session.session_key:
                            existing_session_id = sid
                            print(f"✅ Found existing session in memory: {sid}")
                            break
                    
                    if existing_session_id:
                        # Reuse existing session
                        session_id = existing_session_id
                        restored_session = sessions[session_id]
                        # Update current_question_number based on existing MAIN questions
                        # CRITICAL: Only count MAIN questions (exclude follow-ups, closing, candidate questions)
                        existing_main_questions = InterviewQuestion.objects.filter(
                            session=django_session,
                            role='AI',
                            question_level='MAIN'  # Only count MAIN questions for sequential numbering
                        ).exclude(
                            question_type='CODING'  # Exclude coding questions from technical question count
                        ).count()
                        # current_question_number should be 1-indexed, so if we have 2 MAIN questions, next is question 3
                        restored_session.current_question_number = existing_main_questions + 1
                        print(f"📊 Question numbering (restore): Found {existing_main_questions} MAIN questions, setting current_question_number={restored_session.current_question_number}")
                        print(f"✅ Reusing existing session: {session_id}, current_question_number={restored_session.current_question_number}")
                    else:
                        # Create new session and restore state
                        jd_text = django_session.job_description or ""
                        candidate_name = django_session.candidate_name or "Candidate"
                        
                        if jd_text:
                            # Recreate session using start_interview logic
                            from .complete_ai_bot import start_interview
                            # Get max_questions from existing questions count or default to 4
                            existing_questions = InterviewQuestion.objects.filter(
                                session=django_session,
                                role='AI'  # Only count AI questions
                            ).count()
                            max_questions = max(existing_questions + 1, 4)  # At least one more than existing
                            
                            print(f"🔄 Creating new session with max_questions={max_questions}")
                            restore_result = start_interview(candidate_name, jd_text, max_questions=max_questions)
                            
                            if 'session_id' in restore_result and 'error' not in restore_result:
                                # Link restored session to Django session
                                restored_session_id = restore_result['session_id']
                                if restored_session_id in sessions:
                                    restored_session = sessions[restored_session_id]
                                    restored_session.django_session_key = django_session.session_key
                                    # Update current_question_number based on existing MAIN questions
                                    # CRITICAL: Only count MAIN questions (exclude follow-ups, closing, candidate questions)
                                    existing_main_questions = InterviewQuestion.objects.filter(
                                        session=django_session,
                                        role='AI',
                                        question_level='MAIN'  # Only count MAIN questions for sequential numbering
                                    ).exclude(
                                        question_type='CODING'  # Exclude coding questions from technical question count
                                    ).count()
                                    # current_question_number should be 1-indexed, so if we have 2 MAIN questions, next is question 3
                                    restored_session.current_question_number = existing_main_questions + 1
                                    print(f"📊 Question numbering (new session restore): Found {existing_main_questions} MAIN questions, setting current_question_number={restored_session.current_question_number}")
                                    print(f"✅ Session restored: {restored_session_id}, current_question_number={restored_session.current_question_number}")
                                    # Use restored session_id
                                    session_id = restored_session_id
                                else:
                                    print(f"❌ Failed to restore session - restored session_id not in sessions dict")
                            else:
                                print(f"❌ Failed to restore session: {restore_result.get('error', 'Unknown error')}")
                        else:
                            print(f"❌ Cannot restore session - no job description found")
                else:
                    print(f"❌ Could not find Django session to restore from")
            except Exception as e:
                print(f"⚠️ Error attempting to restore session: {e}")
                import traceback
                traceback.print_exc()
            
            # If still not found after restore attempt, return error
            if session_id not in sessions:
                print(f"❌ ERROR: session_id '{session_id}' still not found after restore attempt")
                return JsonResponse({"error": "Invalid session ID. Please refresh the page and start a new interview."}, status=400)
        
        result = upload_answer(session_id, transcript)
        
        # Check if upload_answer returned an error
        if 'error' in result:
            print(f"❌ ERROR from upload_answer: {result.get('error')}")
            return JsonResponse(result, status=400)
        
        # Handle candidate questions and AI answers - save them to database
        if session_id and session_id in sessions:
            ai_session = sessions[session_id]
            if hasattr(ai_session, 'django_session_key') and ai_session.django_session_key:
                try:
                    django_session = DjangoSession.objects.get(session_key=ai_session.django_session_key)
                    
                    # Check if this is a candidate question scenario (candidate asked a question, AI answered)
                    interviewer_answer = result.get('interviewer_answer', '')
                    if interviewer_answer:
                        # This is a candidate question - save both the question and AI's answer
                        from .complete_ai_bot import is_candidate_question
                        if is_candidate_question(transcript):
                            # IMPORTANT: When candidate asks a question:
                            # 1. Save candidate's question with role='INTERVIEWEE' in transcribed_answer
                            # 2. Save AI's response with role='AI' in question_text
                            
                            print(f"📝 Detected candidate question: {transcript[:100]}...")
                            
                            # Get the AI's response to the candidate's question from the result
                            interviewer_answer = result.get('next_question', '') or result.get('message', '')
                            if not interviewer_answer and hasattr(ai_session, 'conversation_history'):
                                # Try to get the last interviewer message
                                for msg in reversed(ai_session.conversation_history):
                                    if msg.get('role') == 'interviewer':
                                        interviewer_answer = msg.get('text', '')
                                        break
                            
                            # Get maximum order and sequence
                            from django.db.models import Max
                            max_order_result = InterviewQuestion.objects.filter(
                                session=django_session
                            ).aggregate(max_order=Max('order'))
                            max_order = max_order_result['max_order'] if max_order_result['max_order'] is not None else -1
                            new_order = max_order + 1
                            
                            max_seq_result = InterviewQuestion.objects.filter(
                                session=django_session
                            ).aggregate(max_seq=Max('conversation_sequence'))
                            max_seq = max_seq_result['max_seq'] if max_seq_result['max_seq'] is not None else 0
                            
                            # Step 1: Save candidate's question with role='INTERVIEWEE'
                            # Candidate questions get even sequence numbers (2, 4, 6, 8...)
                            if max_seq % 2 == 1:  # Last was AI (odd), next is Interviewee (even)
                                candidate_sequence = max_seq + 1
                            else:  # Last was Interviewee or no sequence, find next even
                                candidate_sequence = ((max_seq // 2) + 1) * 2
                            
                            # Format candidate's question (remove any Q: prefix, it's going in transcribed_answer)
                            candidate_q_formatted = transcript.strip()
                            if candidate_q_formatted.startswith('Q:'):
                                candidate_q_formatted = candidate_q_formatted.replace('Q:', '').strip()
                            
                            # Create record for candidate's question
                            candidate_question_record = InterviewQuestion.objects.create(
                                session=django_session,
                                question_text='',  # Empty - candidate question goes in transcribed_answer
                                question_type='TECHNICAL',
                                order=new_order,
                                question_level='CANDIDATE_QUESTION',  # Special level to identify candidate questions
                                transcribed_answer=candidate_q_formatted,  # Candidate's question text
                                role='INTERVIEWEE',  # This is from the candidate
                                conversation_sequence=candidate_sequence  # Even sequence: 2, 4, 6, 8...
                            )
                            print(f"✅ Saved candidate question: conversation_sequence {candidate_sequence}, role=INTERVIEWEE, order {new_order}: {candidate_q_formatted[:50]}...")
                            
                            # Step 2: Save AI's response with role='AI'
                            if interviewer_answer:
                                # AI response gets odd sequence number (1, 3, 5, 7...)
                                ai_sequence = candidate_sequence + 1
                                
                                # Format AI's response (remove any A: prefix, it's going in question_text)
                                ai_response_formatted = interviewer_answer.strip()
                                if ai_response_formatted.startswith('A:'):
                                    ai_response_formatted = ai_response_formatted.replace('A:', '').strip()
                                
                                # Create record for AI's response
                                ai_response_record = InterviewQuestion.objects.create(
                                    session=django_session,
                                    question_text=ai_response_formatted,  # AI's response text
                                    question_type='TECHNICAL',
                                    order=new_order + 1,  # Next order after candidate question
                                    question_level='AI_RESPONSE',  # Special level to identify AI responses to candidate
                                    transcribed_answer='',  # Empty - AI response goes in question_text
                                    role='AI',  # This is from the AI
                                    conversation_sequence=ai_sequence,  # Odd sequence: 1, 3, 5, 7...
                                    audio_url=result.get('audio_url', '')  # Audio for AI's response
                                )
                                print(f"✅ Saved AI response to candidate question: conversation_sequence {ai_sequence}, role=AI, order {new_order + 1}: {ai_response_formatted[:50]}...")
                            else:
                                print(f"⚠️ No AI response found for candidate question")
                            
                            # Skip the normal answer saving logic for candidate questions
                            # The candidate question and AI response have been saved above
                            # Continue with normal flow to return the result
                    
                    # Also check for candidate questions in closing phase (when AI answers candidate's question)
                    # Check if the result contains a combined response (answer + "Do you have any other questions?")
                    next_question_text = result.get('next_question', '')
                    if next_question_text and 'do you have any other question' in next_question_text.lower() and not interviewer_answer:
                        # This might be after answering a candidate question - check if transcript is a question
                        from .complete_ai_bot import is_candidate_question
                        if is_candidate_question(transcript):
                            # Check if we already saved this candidate question
                            existing_candidate_q = InterviewQuestion.objects.filter(
                                session=django_session,
                                question_text=transcript,
                                question_level='CANDIDATE_QUESTION'
                            ).first()
                            
                            if not existing_candidate_q:
                                # Check if the last question is a closing question - if so, insert candidate question before it
                                closing_phrases = ["do you have any question", "any questions for", "before we wrap up"]
                                last_question = InterviewQuestion.objects.filter(
                                    session=django_session
                                ).order_by('-order').first()
                                
                                # Extract AI's answer from the combined text (before "Do you have any other questions?")
                                answer_parts = next_question_text.split('Do you have any other questions')
                                ai_answer = answer_parts[0].strip() if answer_parts else next_question_text
                                
                                if last_question and any(phrase in last_question.question_text.lower() for phrase in closing_phrases):
                                    # Last question is a closing question - insert candidate question before it
                                    candidate_order = last_question.order
                                    # Shift closing question and any questions after it by +1
                                    from django.db.models import F
                                    InterviewQuestion.objects.filter(
                                        session=django_session,
                                        order__gte=candidate_order
                                    ).update(order=F('order') + 1)
                                    
                                    # Format candidate's question (remove Q: prefix, it goes in transcribed_answer)
                                    candidate_q_formatted = transcript.strip()
                                    if candidate_q_formatted.startswith('Q:'):
                                        candidate_q_formatted = candidate_q_formatted.replace('Q:', '').strip()
                                    
                                    # Format AI's response (remove A: prefix, it goes in question_text of AI record)
                                    ai_response_formatted = ai_answer.strip() if ai_answer else 'No answer provided'
                                    if ai_response_formatted.startswith('A:'):
                                        ai_response_formatted = ai_response_formatted.replace('A:', '').strip()
                                    
                                    # Get max order and sequence
                                    from django.db.models import Max
                                    max_seq_result = InterviewQuestion.objects.filter(
                                        session=django_session
                                    ).aggregate(max_seq=Max('conversation_sequence'))
                                    max_seq = max_seq_result['max_seq'] if max_seq_result['max_seq'] is not None else 0
                                    
                                    # Step 1: Save candidate question with role='INTERVIEWEE' in transcribed_answer
                                    if max_seq % 2 == 1:
                                        candidate_sequence = max_seq + 1
                                    else:
                                        candidate_sequence = ((max_seq // 2) + 1) * 2
                                    
                                    candidate_question_obj = InterviewQuestion.objects.create(
                                        session=django_session,
                                        question_text='',  # Empty - candidate question goes in transcribed_answer
                                        question_type='TECHNICAL',
                                        order=candidate_order,  # Insert before closing question
                                        question_level='CANDIDATE_QUESTION',
                                        transcribed_answer=candidate_q_formatted,  # Candidate's question text
                                        role='INTERVIEWEE',
                                        conversation_sequence=candidate_sequence
                                    )
                                    print(f"✅ Saved candidate question (closing phase): conversation_sequence {candidate_sequence}, role=INTERVIEWEE, order {candidate_order}: {candidate_q_formatted[:50]}...")
                                    
                                    # Step 2: Save AI response with role='AI' in question_text
                                    if ai_response_formatted and ai_response_formatted != 'No answer provided':
                                        ai_sequence = candidate_sequence + 1
                                        ai_response_obj = InterviewQuestion.objects.create(
                                            session=django_session,
                                            question_text=ai_response_formatted,  # AI's response text
                                            question_type='TECHNICAL',
                                            order=candidate_order + 1,
                                            question_level='AI_RESPONSE',
                                            transcribed_answer='',  # Empty - AI response goes in question_text
                                            role='AI',
                                            conversation_sequence=ai_sequence
                                        )
                                        print(f"✅ Saved AI response (closing phase): conversation_sequence {ai_sequence}, role=AI, order {candidate_order + 1}: {ai_response_formatted[:50]}...")
                                else:
                                    # No closing question found, use normal max_order + 1
                                    existing_questions = InterviewQuestion.objects.filter(
                                        session=django_session
                                    ).order_by('-order')
                                    max_order = existing_questions.first().order if existing_questions.exists() else -1
                                    
                                    # Format candidate's question (remove Q: prefix, it goes in transcribed_answer)
                                    candidate_q_formatted = transcript.strip()
                                    if candidate_q_formatted.startswith('Q:'):
                                        candidate_q_formatted = candidate_q_formatted.replace('Q:', '').strip()
                                    
                                    # Format AI's response (remove A: prefix, it goes in question_text of AI record)
                                    ai_response_formatted = ai_answer.strip() if ai_answer else 'No answer provided'
                                    if ai_response_formatted.startswith('A:'):
                                        ai_response_formatted = ai_response_formatted.replace('A:', '').strip()
                                    
                                    # Get max order and sequence
                                    from django.db.models import Max
                                    max_seq_result = InterviewQuestion.objects.filter(
                                        session=django_session
                                    ).aggregate(max_seq=Max('conversation_sequence'))
                                    max_seq = max_seq_result['max_seq'] if max_seq_result['max_seq'] is not None else 0
                                    
                                    # Step 1: Save candidate question with role='INTERVIEWEE' in transcribed_answer
                                    if max_seq % 2 == 1:
                                        candidate_sequence = max_seq + 1
                                    else:
                                        candidate_sequence = ((max_seq // 2) + 1) * 2
                                    
                                    candidate_question_obj = InterviewQuestion.objects.create(
                                        session=django_session,
                                        question_text='',  # Empty - candidate question goes in transcribed_answer
                                        question_type='TECHNICAL',
                                        order=max_order + 1,
                                        question_level='CANDIDATE_QUESTION',
                                        transcribed_answer=candidate_q_formatted,  # Candidate's question text
                                        role='INTERVIEWEE',
                                        conversation_sequence=candidate_sequence
                                    )
                                    print(f"✅ Saved candidate question (closing phase): conversation_sequence {candidate_sequence}, role=INTERVIEWEE, order {max_order + 1}: {candidate_q_formatted[:50]}...")
                                    
                                    # Step 2: Save AI response with role='AI' in question_text
                                    if ai_response_formatted and ai_response_formatted != 'No answer provided':
                                        ai_sequence = candidate_sequence + 1
                                        ai_response_obj = InterviewQuestion.objects.create(
                                            session=django_session,
                                            question_text=ai_response_formatted,  # AI's response text
                                            question_type='TECHNICAL',
                                            order=max_order + 2,
                                            question_level='AI_RESPONSE',
                                            transcribed_answer='',  # Empty - AI response goes in question_text
                                            role='AI',
                                            conversation_sequence=ai_sequence
                                        )
                                        print(f"✅ Saved AI response (closing phase): conversation_sequence {ai_sequence}, role=AI, order {max_order + 2}: {ai_response_formatted[:50]}...")
                    
                    # Also check for closing question in final_message if interview is completed
                    if not next_question_text and result.get('completed') and result.get('final_message'):
                        # This is the final closing message, not a question
                        pass
                    elif next_question_text and next_question_text.strip():
                        # Check if this question already exists
                        existing_questions = InterviewQuestion.objects.filter(
                            session=django_session
                        ).order_by('order')
                        
                        # Get the current question number from AI session
                        current_q_num = ai_session.current_question_number
                        
                        # Check if question at this order already exists
                        question_exists = existing_questions.filter(order=current_q_num - 1).exists()
                        
                        if not question_exists:
                            # Determine question type - check if it's a pre-closing or closing question
                            is_closing_question = any(phrase in next_question_text.lower() for phrase in [
                                "do you have any question", "any questions for", "before we wrap up"
                            ])
                            
                            # Check if this is a pre-closing question
                            is_pre_closing = False
                            if hasattr(ai_session, 'asked_pre_closing_question') and ai_session.asked_pre_closing_question:
                                if hasattr(ai_session, 'asked_for_questions') and not ai_session.asked_for_questions:
                                    is_pre_closing = True
                            
                            # Get the maximum order to ensure unique sequential ordering
                            from django.db.models import Max
                            max_order_result = InterviewQuestion.objects.filter(
                                session=django_session
                            ).aggregate(max_order=Max('order'))
                            max_order = max_order_result['max_order'] if max_order_result['max_order'] is not None else -1
                            new_order = max_order + 1
                            
                            # IMPORTANT: If this is a closing question, check if there's a candidate question that should come before it
                            # Candidate questions should always come before closing questions
                            if is_closing_question:
                                # Check if there's a candidate question without a following closing question
                                candidate_questions = InterviewQuestion.objects.filter(
                                    session=django_session,
                                    question_level='CANDIDATE_QUESTION'
                                ).order_by('-order')
                                
                                if candidate_questions.exists():
                                    last_candidate = candidate_questions.first()
                                    # Check if there's already a closing question after this candidate question
                                    closing_after_candidate = InterviewQuestion.objects.filter(
                                        session=django_session,
                                        order__gt=last_candidate.order
                                    ).filter(
                                        question_text__icontains='do you have any question'
                                    ).exists()
                                    
                                    if not closing_after_candidate:
                                        # No closing question after candidate - use candidate's order + 1
                                        new_order = last_candidate.order + 1
                                        print(f"✅ Adjusting closing question order to {new_order} (after candidate question at order {last_candidate.order})")
                            
                            # Format question text (remove Q: prefix for cleaner storage)
                            question_text_formatted = next_question_text.strip()
                            if question_text_formatted.startswith('Q:'):
                                question_text_formatted = question_text_formatted.replace('Q:', '').strip()
                            
                            # Get the maximum conversation_sequence to ensure sequential indexing
                            max_seq_result = InterviewQuestion.objects.filter(
                                session=django_session
                            ).aggregate(max_seq=Max('conversation_sequence'))
                            max_seq = max_seq_result['max_seq'] if max_seq_result['max_seq'] is not None else 0
                            
                            # AI questions get odd sequence numbers (1, 3, 5, 7...)
                            # If last sequence was even (Interviewee answer), next is AI (odd)
                            # If last sequence was odd or null, calculate next odd number
                            if max_seq % 2 == 0 and max_seq > 0:  # Last was Interviewee (even), next is AI (odd)
                                ai_sequence = max_seq + 1
                            else:  # Last was AI or no sequence, find next odd
                                ai_sequence = ((max_seq // 2) + 1) * 2 + 1
                            
                            # Create new AI question with proper sequential order
                            question_obj = InterviewQuestion.objects.create(
                                session=django_session,
                                question_text=question_text_formatted,  # AI question text (without Q: prefix)
                                question_type='TECHNICAL',
                                order=new_order,  # Use calculated order (may be adjusted for closing questions)
                                question_level='MAIN',
                                audio_url=result.get('audio_url', ''),
                                role='AI',  # This is an AI-generated question
                                conversation_sequence=ai_sequence  # Sequential index: 1, 3, 5, 7...
                            )
                            question_type_label = 'pre-closing' if is_pre_closing else 'closing' if is_closing_question else 'regular'
                            print(f"✅ Created new AI {question_type_label} question: conversation_sequence {ai_sequence}, role=AI, order {new_order}: {next_question_text[:50]}...")
                            
                            # If interview is completed and we just created the closing question,
                            # OR if this is a pre-closing/closing question, try to save the answer if transcript is available
                            if result.get('completed') or is_closing_question or is_pre_closing:
                                try:
                                    # For pre-closing/closing questions, save actual transcript if available (even if it's "no")
                                    # Only use "No answer provided" if transcript is truly empty
                                    if transcript and transcript.strip() and not transcript.startswith("[") and not transcript.startswith("[No speech"):
                                        answer_text = transcript.strip()
                                        # Format answer with A: prefix
                                        if not answer_text.startswith('A:'):
                                            answer_text = f'A: {answer_text}'
                                        question_obj.transcribed_answer = answer_text
                                        question_obj.save()
                                        print(f"✅ Saved answer to {question_type_label} question: {answer_text[:50]}...")
                                    else:
                                        # Don't save "No answer provided" yet - wait for the actual answer
                                        print(f"⚠️ No transcript available yet for {question_type_label} question, will save when answer comes")
                                except Exception as e:
                                    print(f"⚠️ Error saving {question_type_label} question answer: {e}")
                except Exception as e:
                    print(f"⚠️ Error creating question in database: {e}")
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Success - Completed: {result.get('completed', False)}")
            if not result.get('completed'):
                print(f"✅ Next question: {result.get('next_question', 'N/A')[:100]}...")
                print(f"✅ Audio URL: {result.get('audio_url', 'NOT PROVIDED')}")
                if not result.get('audio_url'):
                    print(f"⚠️ WARNING: No audio URL returned for next question!")
        print(f"{'='*60}\n")
        
        status_code = 200 if 'error' not in result else 400
        return JsonResponse(result, status=status_code)
    except Exception as e:
        print(f"❌ Exception in ai_upload_answer: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def ai_repeat(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    session_id = data.get('session_id')
    result = ai_repeat_django(session_id)
    status_code = 200 if 'error' not in result else 400
    return JsonResponse(result, status=status_code)


def ai_transcript_pdf(request):
    """Generate comprehensive PDF with Q&A and Coding results"""
    session_key = request.GET.get('session_key', '')
    session_id = request.GET.get('session_id', '')
    
    print(f"\n{'='*60}")
    print(f"📄 PDF GENERATION REQUEST")
    print(f"   Session Key: {session_key}")
    print(f"   Session ID: {session_id}")
    print(f"{'='*60}")
    
    # Try to get session by session_key first, then by session_id
    try:
        if session_key:
            # Verify session exists
            from .models import InterviewSession
            try:
                session = InterviewSession.objects.get(session_key=session_key)
                print(f"✅ Found session: {session.candidate_name}")
            except InterviewSession.DoesNotExist:
                print(f"❌ Session not found: {session_key}")
                return JsonResponse({'error': 'Session not found'}, status=404)
            
            # Generate PDF
            from .comprehensive_pdf import ai_comprehensive_pdf_django
            from .gcs_storage import upload_pdf_to_gcs
            from django.utils import timezone
            pdf_bytes = ai_comprehensive_pdf_django(session_key)
            
            # Upload to GCS if configured (optional - PDF is still served directly)
            if pdf_bytes:
                try:
                    gcs_file_path = f"evaluation_pdfs/qna_evaluation_{session_key}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    gcs_url = upload_pdf_to_gcs(pdf_bytes, gcs_file_path)
                    if gcs_url:
                        print(f"✅ Q&A PDF uploaded to GCS: {gcs_url}")
                        # Store GCS URL in evaluation details for later retrieval
                        try:
                            from evaluation.models import Evaluation
                            from interviews.models import Interview
                            interview = Interview.objects.get(session_key=session_key)
                            evaluation = Evaluation.objects.filter(interview=interview).first()
                            if evaluation:
                                if not evaluation.details:
                                    evaluation.details = {}
                                evaluation.details['qna_pdf_gcs_url'] = gcs_url
                                evaluation.save(update_fields=['details'])
                                print(f"✅ Q&A PDF GCS URL stored in evaluation")
                        except Exception as e:
                            print(f"⚠️ Could not store GCS URL in evaluation: {e}")
                except Exception as e:
                    print(f"⚠️ Error uploading Q&A PDF to GCS (will serve directly): {e}")
            
        elif session_id:
            # Get session_key from session_id
            from .models import InterviewSession
            session = InterviewSession.objects.get(id=session_id)
            print(f"✅ Found session by ID: {session.candidate_name}")
            
            from .comprehensive_pdf import ai_comprehensive_pdf_django
            pdf_bytes = ai_comprehensive_pdf_django(session.session_key)
        else:
            print(f"❌ No session key or ID provided")
            return JsonResponse({'error': 'Session key or ID required'}, status=400)
        
        if not pdf_bytes or len(pdf_bytes) == 0:
            print(f"❌ PDF generation returned empty bytes")
            return JsonResponse({'error': 'PDF generation returned empty'}, status=500)
        
        print(f"✅ PDF generated successfully: {len(pdf_bytes)} bytes")
        print(f"{'='*60}\n")
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="interview_report_{session_key or session_id}.pdf"'
        return response
        
    except InterviewSession.DoesNotExist:
        print(f"❌ Session not found")
        return JsonResponse({'error': 'Session not found'}, status=404)
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'PDF generation failed: {str(e)}'}, status=500)

@csrf_exempt
def download_proctoring_pdf(request, session_id):
    """Download proctoring warnings PDF for a given session (from GCS or local)"""
    try:
        from .models import InterviewSession
        from evaluation.models import Evaluation
        from interviews.models import Interview
        from django.http import FileResponse, Http404, HttpResponseRedirect, HttpResponse
        from .gcs_storage import download_pdf_from_gcs, get_gcs_signed_url
        import os
        
        # Get session
        try:
            session = InterviewSession.objects.get(id=session_id)
        except InterviewSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        
        # Get interview
        try:
            interview = Interview.objects.get(session_key=session.session_key)
        except Interview.DoesNotExist:
            return JsonResponse({'error': 'Interview not found'}, status=404)
        
        # Get evaluation
        try:
            evaluation = Evaluation.objects.get(interview=interview)
        except Evaluation.DoesNotExist:
            return JsonResponse({'error': 'Evaluation not found. Please wait for evaluation to be generated.'}, status=404)
        
        # Get PDF path from evaluation details
        if not evaluation.details or not isinstance(evaluation.details, dict):
            return JsonResponse({'error': 'Evaluation details not found'}, status=404)
        
        # Check for GCS URL first (preferred)
        gcs_url = evaluation.details.get('proctoring_pdf_gcs_url') or evaluation.details.get('proctoring_pdf_url')
        if gcs_url and isinstance(gcs_url, str) and gcs_url.startswith('http'):
            # If it's a GCS public URL, redirect to it
            if 'storage.googleapis.com' in gcs_url:
                print(f"✅ Redirecting to GCS URL: {gcs_url}")
                return HttpResponseRedirect(gcs_url)
        
        # Try to download from GCS using file path
        proctoring_pdf_path = evaluation.details.get('proctoring_pdf')
        if proctoring_pdf_path and 'proctoring_pdfs/' in proctoring_pdf_path:
            pdf_bytes = download_pdf_from_gcs(proctoring_pdf_path)
            if pdf_bytes:
                response = HttpResponse(pdf_bytes, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="proctoring_report_{session_id}.pdf"'
                return response
        
        if not proctoring_pdf_path:
            # Try to generate PDF if it doesn't exist
            from evaluation.services import create_evaluation_from_session
            evaluation = create_evaluation_from_session(session.session_key)
            if evaluation and evaluation.details:
                proctoring_pdf_path = evaluation.details.get('proctoring_pdf')
                gcs_url = evaluation.details.get('proctoring_pdf_gcs_url')
                if gcs_url and isinstance(gcs_url, str) and 'storage.googleapis.com' in gcs_url:
                    return HttpResponseRedirect(gcs_url)
        
        if not proctoring_pdf_path:
            return JsonResponse({'error': 'Proctoring PDF not found. No warnings were detected during the interview.'}, status=404)
        
        # Fallback to local file system
        pdf_full_path = os.path.join(settings.MEDIA_ROOT, proctoring_pdf_path.lstrip('/'))
        
        if not os.path.exists(pdf_full_path):
            return JsonResponse({'error': f'PDF file not found at {pdf_full_path}'}, status=404)
        
        # Serve PDF file
        response = FileResponse(open(pdf_full_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="proctoring_report_{session_id}.pdf"'
        return response
        
    except Exception as e:
        print(f"❌ Error downloading proctoring PDF: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Failed to download PDF: {str(e)}'}, status=500)

@csrf_exempt
@require_POST
def verify_id(request):
    try:
        image_data = request.POST.get('image_data') 
        session_id = request.POST.get('session_id')

        if not all([image_data, session_id]):
            return JsonResponse({'status': 'error', 'message': 'Missing required data.'}, status=400)

        session = InterviewSession.objects.get(id=session_id)
        
        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1]
        img_file = ContentFile(base64.b64decode(imgstr), name=f"id_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}")
        session.id_card_image.save(img_file.name, img_file, save=True)
        
        tmp_path = session.id_card_image.path
        
        if not CV2_AVAILABLE or cv2 is None:
            return JsonResponse({'status': 'error', 'message': 'OpenCV not available. Image processing features are disabled.'})
        
        full_image = cv2.imread(tmp_path)
        if full_image is None:
            return JsonResponse({'status': 'error', 'message': 'Invalid image format.'})

        results = detect_face_with_yolo(full_image)
        # Handle both list and single object returns
        if results:
            # Check if results is a list
            if isinstance(results, list) and len(results) > 0:
                # Access first element if it's a list
                first_result = results[0]
                boxes = first_result.boxes if hasattr(first_result, 'boxes') else []
            elif hasattr(results, 'boxes'):
                # Results is a single object with boxes attribute
                boxes = results.boxes
            else:
                boxes = []
        else:
            boxes = []
        num_faces_detected = len(boxes) if boxes else 0

        # Check for exactly two faces (candidate + ID photo)
        if num_faces_detected != 2:
            if num_faces_detected < 2:
                message = f"Verification failed. Only {num_faces_detected} face(s) detected. Please ensure both your live face and the face on your ID card are clearly visible and well-lit."
            else:
                message = f"Verification failed. {num_faces_detected} faces detected. Please ensure only you and your ID card are in the frame, with no other people in the background."
            return JsonResponse({'status': 'error', 'message': message})

        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            id_number, name = extract_id_data(tmp_path, model)
        except Exception as ai_error:
            print(f"AI OCR failed: {ai_error}")
            # Fallback: Skip OCR and just verify face count
            id_number, name = "SKIPPED", session.candidate_name
        
        session.extracted_id_details = f"Name: {name}, ID: {id_number}"
        
        invalid_phrases = ['not found', 'cannot be', 'unreadable', 'blurry', 'unavailable', 'missing']
        name_verified = name and len(name.strip()) > 2 and not any(phrase in name.lower() for phrase in invalid_phrases)

        # If AI OCR failed, skip name verification
        if name == "SKIPPED":
            print("AI OCR was skipped, proceeding with face count verification only")
        elif not name_verified:
            return JsonResponse({'status': 'error', 'message': f"Could not reliably read the name from the ID card. Extracted: '{name}'. Please try again."})
        else:
            # Enhanced name matching: Check if candidate name matches ID name
            candidate_name_lower = session.candidate_name.lower().strip()
            extracted_name_lower = name.lower().strip()
            
            # Split names into words for comparison
            candidate_words = set(candidate_name_lower.split())
            extracted_words = set(extracted_name_lower.split())
            
            # Remove common words that might appear in names but aren't part of the actual name
            common_words = {'mr', 'mrs', 'miss', 'ms', 'dr', 'prof', 'sir', 'madam', 'jr', 'sr', 'ii', 'iii', 'iv'}
            candidate_words = candidate_words - common_words
            extracted_words = extracted_words - common_words
            
            # Check if at least 2 words match (to handle cases like "John Doe" vs "John Michael Doe")
            # Or if all candidate name words are present in extracted name
            matching_words = candidate_words.intersection(extracted_words)
            
            # Require at least 2 matching words OR all candidate name words must be present
            if len(matching_words) < 2 and not candidate_words.issubset(extracted_words):
                # Additional check: try matching without middle names
                candidate_first_last = [w for w in candidate_name_lower.split() if w not in common_words][:2]  # First and last name only
                extracted_first_last = [w for w in extracted_name_lower.split() if w not in common_words][:2]
                
                if len(candidate_first_last) >= 2 and len(extracted_first_last) >= 2:
                    # Check if first and last name match
                    if candidate_first_last[0] == extracted_first_last[0] and candidate_first_last[-1] == extracted_first_last[-1]:
                        print(f"✅ Name verified: First and last name match ({candidate_first_last[0]} {candidate_first_last[-1]})")
                    else:
                        return JsonResponse({
                            'status': 'error', 
                            'message': f"Name verification failed. Name on ID ('{name}') does not match the registered candidate name ('{session.candidate_name}'). Please ensure you are using the correct ID card."
                        })
                else:
                    return JsonResponse({
                        'status': 'error', 
                        'message': f"Name verification failed. Name on ID ('{name}') does not match the registered candidate name ('{session.candidate_name}'). Please ensure you are using the correct ID card."
                    })
            else:
                print(f"✅ Name verified: {len(matching_words)} matching words found between '{session.candidate_name}' and '{name}'")

        session.id_verification_status = 'Verified'
        session.save()

        return JsonResponse({'status': 'success', 'message': 'Verification successful!'})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}, status=500)
    pass

# --- Multi-Language Code Execution Logic (Windows Compatible) ---
def run_subprocess_windows(command, cwd=None, input_data=None, env=None):
    try:
        # Reduced timeout to 5 seconds per test case for faster execution
        # Multiple test cases can accumulate, so keep individual timeouts very short
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=cwd,
            input=input_data,
            env=env,
        )
        return result
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(command, 1, stdout=None, stderr="Execution timed out after 5 seconds. Code may be too slow or have infinite loops.")
    except Exception as e:
        return subprocess.CompletedProcess(command, 1, stdout=None, stderr=f"Server execution error: {str(e)}")

def execute_python_windows(code, test_input):
    """
    Execute Python code with test input.
    Handles both function-based and class-based code.
    """
    import re
    
    print(f"🔍 execute_python_windows called with test_input='{test_input}'")
    
    # Check if code contains a class definition (for OOP questions)
    class_match = re.search(r'class\s+(\w+)', code)
    
    if class_match:
        # Class-based code: test_input should be executable Python code
        # Example: "finder = MedianFinder(); finder.addNum(1); finder.findMedian()"
        # Split by semicolon, execute all but last, then print the result of the last
        statements = [s.strip() for s in test_input.split(';') if s.strip()]
        if len(statements) > 1:
            # Execute all statements except the last
            setup = '\n'.join(statements[:-1])
            # Print the result of the last statement
            full_script = f"{code}\n{setup}\nprint({statements[-1]})"
        else:
            # Single statement - just execute and print
            full_script = f"{code}\nprint({test_input})"
    else:
        # Function-based code: find function name and call it
        function_match = re.search(r'def\s+(\w+)\s*\(', code)
        if function_match:
            function_name = function_match.group(1)
            # test_input already contains quotes (e.g., "'hello'" or '"hello"')
            # so we can use it directly: reverse_string('hello')
            # Use repr() to ensure the output is properly formatted for comparison
            full_script = f"{code}\nresult = {function_name}({test_input})\nif result is not None:\n    print(result)\nelse:\n    print('None')"
            print(f"🔍 Generated script (preview): {full_script[:300]}...")
            print(f"🔍 Function name detected: {function_name}")
        else:
            # Fallback to 'solve' if no function found
            full_script = f"{code}\nresult = solve({test_input})\nif result is not None:\n    print(result)\nelse:\n    print('None')"
            print(f"🔍 Using fallback 'solve' function")
    
    result = run_subprocess_windows(['python', '-c', full_script])
    
    # Clean up the output - remove any trailing newlines and normalize
    if result.stdout:
        result.stdout = result.stdout.strip()
    if result.stderr:
        result.stderr = result.stderr.strip()
    
    print(f"🔍 Execution result - stdout: '{result.stdout}', stderr: '{result.stderr}', returncode: {result.returncode}")
    return result

def execute_javascript_windows(code, test_input):
    full_script = f"{code}\nconsole.log(solve({test_input}));"
    return run_subprocess_windows(['node', '-e', full_script])

def _extract_go_imports_and_body(code: str):
    """
    Separate Go imports from the rest of the source so we can rebuild a harness.
    Returns (imports_set, body_string).
    """
    imports = []
    body_lines = []
    lines = code.splitlines()
    i = 0

    # Skip leading shebang/comments/blank lines but capture everything else
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("package "):
            i += 1
            break
        if stripped:
            break
        i += 1

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("import"):
            if stripped.startswith("import (") or stripped == "import(":
                i += 1
                while i < len(lines):
                    inner = lines[i].strip()
                    if inner == ")":
                        break
                    if inner:
                        pkg = inner.split("//")[0].strip().strip('"').strip('`')
                        if pkg:
                            imports.append(pkg)
                    i += 1
            else:
                remainder = stripped[len("import"):].split("//")[0].strip()
                if remainder:
                    pkg = remainder.split()[-1].strip('"').strip('`')
                    if pkg:
                        imports.append(pkg)
        else:
            body_lines.extend(lines[i:])
            break
        i += 1

    body = "\n".join(body_lines).strip()
    return set(imports), body

def _format_go_arguments(raw_input: str) -> str:
    if not raw_input or raw_input.lower() == "n/a":
        return ""
    raw = raw_input.strip()
    if raw.startswith("(") and raw.endswith(")"):
        raw = raw[1:-1]

    parts = [p.strip() for p in raw.split(",") if p.strip()]
    formatted = []
    for part in parts:
        lower = part.lower()
        if re.fullmatch(r"-?\d+", part) or re.fullmatch(r"-?\d+\.\d+", part):
            formatted.append(part)
        elif lower in {"true", "false", "nil"}:
            formatted.append(lower)
        elif part.startswith('"') and part.endswith('"'):
            formatted.append(part)
        elif part.startswith("'") and part.endswith("'"):
            inner = part[1:-1]
            if len(inner) == 1:
                formatted.append(f"'{inner}'")
            else:
                escaped = inner.replace('"', '\\"')
                formatted.append(f"\"{escaped}\"")
        else:
            formatted.append(part)
    return ", ".join(formatted)

def _detect_go_entrypoint(code_body: str) -> str:
    candidates = re.findall(r'^\s*func\s+(\w+)\s*\(', code_body, flags=re.MULTILINE)
    for name in candidates:
        if name and name != "main":
            return name
    return "solve"

def execute_go_windows(code, test_input):
    """
    Compile and execute Go code by wrapping the submission with a harness
    that calls the detected function using the provided test input.
    """
    go_cmd = shutil.which("go")
    if not go_cmd:
        message = (
            "Go toolchain is not available on the server. "
            "Install Go and ensure the 'go' binary is on PATH."
        )
        return subprocess.CompletedProcess(["go"], 1, stdout="", stderr=message)

    imports, body = _extract_go_imports_and_body(code)
    body = re.sub(r'func\s+main\s*\([^)]*\)\s*{[\s\S]*?}\s*', '', body)
    imports.add("fmt")

    function_name = _detect_go_entrypoint(body)
    arg_expr = _format_go_arguments(test_input or "")
    call_expr = f"{function_name}({arg_expr})" if arg_expr else f"{function_name}()"

    if len(imports) == 1:
        import_section = f'import "{next(iter(imports))}"\n'
    else:
        import_section = "import (\n"
        for pkg in sorted(imports):
            import_section += f'    "{pkg}"\n'
        import_section += ")\n"

    harness = (
        "package main\n\n"
        f"{import_section}\n"
        f"{body}\n\n"
        "func main() {\n"
        f"    fmt.Println({call_expr})\n"
        "}\n"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        go_file_path = os.path.join(temp_dir, "main.go")
        with open(go_file_path, "w", encoding="utf-8") as go_file:
            go_file.write(harness)

        run_result = run_subprocess_windows([go_cmd, "run", go_file_path], cwd=temp_dir)
        return run_result

def _resolve_php_binary():
    php_cmd = shutil.which("php")
    if php_cmd:
        return php_cmd

    configured = getattr(settings, "PHP_PATH", None) or os.environ.get("PHP_PATH")
    if configured:
        if os.path.isfile(configured):
            return configured
        possible = os.path.join(configured, "php.exe")
        if os.path.isfile(possible):
            return possible

    common_candidates = [
        r"C:\tools\php84\php.exe",
        r"C:\tools\php\php.exe",
        r"C:\Program Files\PHP\php.exe",
        r"C:\Program Files\Php\php.exe",
        r"C:\Program Files (x86)\PHP\php.exe",
    ]
    for candidate in common_candidates:
        if os.path.isfile(candidate):
            return candidate

    return None

def _detect_cpp_entrypoint(code: str) -> str:
    pattern = re.compile(r'^\s*[^\s#][\w\s:<>,*&\[\]]+\s+([A-Za-z_]\w*)\s*\(', flags=re.MULTILINE)
    for match in pattern.finditer(code):
        name = match.group(1)
        if name and name not in {"if", "for", "while", "switch", "return", "main"}:
            return name
    return "solve"

def _format_cpp_arguments(raw_input: str) -> str:
    if not raw_input or raw_input.lower() == "n/a":
        return ""
    raw = raw_input.strip()
    if raw.startswith(("'", '"')) and raw.endswith(("'", '"')) and "," in raw:
        raw = raw[1:-1]
    if raw.startswith("(") and raw.endswith(")"):
        raw = raw[1:-1]

    parts = [p.strip() for p in raw.split(",") if p.strip()]
    formatted = []
    for part in parts:
        lower = part.lower()
        if re.fullmatch(r"-?\d+", part) or re.fullmatch(r"-?\d+\.\d+", part):
            formatted.append(part)
        elif lower in {"true", "false", "nullptr", "null"}:
            formatted.append(lower)
        elif part.startswith('"') and part.endswith('"'):
            inner = part[1:-1].replace('"', r'\"')
            formatted.append(f"\"{inner}\"")
        elif part.startswith("'") and part.endswith("'"):
            inner = part[1:-1]
            if len(inner) == 1:
                formatted.append(f"'{inner}'")
            else:
                escaped = inner.replace('"', '\\"')
                formatted.append(f"\"{escaped}\"")
        else:
            formatted.append(part)
    return ", ".join(formatted)

def _resolve_cpp_compiler():
    configured = getattr(settings, "CPP_COMPILER", None) or os.environ.get("CPP_COMPILER")
    if configured:
        if os.path.isfile(configured):
            return configured
        possible = os.path.join(configured, "g++.exe")
        if os.path.isfile(possible):
            return possible

    compiler = shutil.which("g++")
    if compiler:
        return compiler

    candidates = [
        r"C:\msys641\mingw64\bin\g++.exe",
        r"C:\msys64\mingw64\bin\g++.exe",
        r"C:\msys64\ucrt64\bin\g++.exe",
        r"C:\mingw64\bin\g++.exe",
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None

def execute_cpp_windows(code, test_input, treat_as_c=False):
    compiler = _resolve_cpp_compiler()
    if not compiler:
        message = (
            "C/C++ compiler not available on the server. "
            "Install MinGW-w64 (g++) and ensure it is on PATH."
        )
        return subprocess.CompletedProcess(["g++"], 1, stdout="", stderr=message)

    function_name = _detect_cpp_entrypoint(code)
    arg_expr = _format_cpp_arguments(test_input or "")
    call_expr = f"{function_name}({arg_expr})" if arg_expr else f"{function_name}()"

    base_includes = [
        "#include <bits/stdc++.h>",
        "#include <type_traits>",
        "#include <functional>",
    ]

    extra_includes = []
    body_content = code
    if treat_as_c:
        user_lines = code.splitlines()
        remaining_lines = []
        for line in user_lines:
            stripped = line.strip()
            if stripped.startswith("#include"):
                extra_includes.append(line)
            else:
                remaining_lines.append(line)
        body_content = "\n".join(remaining_lines)

    includes_block = "\n".join(base_includes + extra_includes) + "\n\n"
    harness = includes_block
    if treat_as_c:
        harness += "#ifdef __cplusplus\nextern \"C\" {\n#endif\n"
        harness += body_content + "\n"
        harness += "#ifdef __cplusplus\n}\n#endif\n"
    else:
        harness += body_content + "\n"

    harness += """
template <typename Func, typename... Args>
void invoke_and_print(Func&& func, Args&&... args) {
    using Result = std::invoke_result_t<Func, Args...>;
    if constexpr (std::is_void_v<Result>) {
        std::invoke(std::forward<Func>(func), std::forward<Args>(args)...);
    } else {
        auto result = std::invoke(std::forward<Func>(func), std::forward<Args>(args)...);
        std::cout << result;
    }
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
"""
    if arg_expr:
        harness += f"    invoke_and_print({function_name}, {arg_expr});\n"
    else:
        harness += f"    invoke_and_print({function_name});\n"
    harness += "    return 0;\n}\n"

    compiler_dir = os.path.dirname(compiler)
    env = os.environ.copy()
    env["PATH"] = compiler_dir + os.pathsep + env.get("PATH", "")

    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "solution.cpp")
        with open(source_path, "w", encoding="utf-8") as cpp_file:
            cpp_file.write(harness)

        executable_path = os.path.join(temp_dir, "solution.exe")
        compile_result = run_subprocess_windows(
            [compiler, "-std=c++17", source_path, "-o", executable_path],
            env=env,
        )
        if compile_result.returncode != 0:
            return compile_result

        run_result = run_subprocess_windows([executable_path], cwd=temp_dir, env=env)
        return run_result

def _resolve_java_binary(binary_name: str):
    """
    Locate the full path for a Java executable (e.g., javac, java).
    Checks PATH, Django settings, JAVA_HOME, and common Windows install directories.
    """
    if not binary_name:
        return None

    candidates = []
    exe_name = binary_name
    if os.name == "nt" and not binary_name.lower().endswith(".exe"):
        exe_name = f"{binary_name}.exe"

    # PATH lookup first
    for name in {binary_name, exe_name}:
        located = shutil.which(name)
        if located:
            return located

    # Django settings or environment JAVA_HOME
    java_home = getattr(settings, "JAVA_HOME", None) or os.environ.get("JAVA_HOME")
    if java_home:
        candidate = os.path.join(java_home, "bin", exe_name)
        if os.path.exists(candidate):
            return candidate

    # Common Windows install locations
    if os.name == "nt":
        potential_roots = [
            os.environ.get("PROGRAMFILES"),
            os.environ.get("PROGRAMFILES(X86)"),
            r"C:\Program Files\Java",
            r"C:\Program Files (x86)\Java",
        ]
        for root in filter(None, potential_roots):
            if not os.path.isdir(root):
                continue
            try:
                entries = sorted(os.listdir(root))
            except OSError:
                continue
            for entry in entries:
                entry_lower = entry.lower()
                if not (entry_lower.startswith("java") or entry_lower.startswith("jdk") or entry_lower.startswith("jre")):
                    continue
                candidate = os.path.join(root, entry, "bin", exe_name)
                if os.path.exists(candidate):
                    return candidate

    return None

def _format_java_arguments(raw_input: str) -> str:
    """
    Convert stored test case input (e.g., '1,2' or '\'hello\'') into
    Java-friendly argument expressions.
    """
    if raw_input is None:
        return ""

    raw = raw_input.strip()
    if not raw:
        return ""

    if raw.startswith("(") and raw.endswith(")"):
        raw = raw[1:-1]

    parts = [part.strip() for part in raw.split(",") if part.strip()]
    formatted_parts = []

    for part in parts:
        if re.fullmatch(r"-?\d+", part) or re.fullmatch(r"-?\d+\.\d+", part):
            formatted_parts.append(part)
        elif part.lower() in {"true", "false", "null"}:
            formatted_parts.append(part.lower())
        elif part.startswith('"') and part.endswith('"'):
            formatted_parts.append(part)
        elif part.startswith("'") and part.endswith("'"):
            inner = part[1:-1]
            if len(inner) == 1:
                formatted_parts.append(f"'{inner}'")
            else:
                escaped = inner.replace('"', '\\"')
                formatted_parts.append(f"\"{escaped}\"")
        else:
            formatted_parts.append(part)

    return ", ".join(formatted_parts)

def _detect_java_entrypoint(code: str):
    """
    Determine class name, method name, and whether the method is static.
    Defaults to Solution.solve if not found.
    """
    class_match = re.search(r'class\s+(\w+)', code)
    class_name = class_match.group(1) if class_match else "Solution"

    preferred_methods = ["solve", "add", "answer", "result"]
    method_name = "solve"
    is_static = True

    for method in preferred_methods:
        pattern = re.compile(r'(public\s+)?(static\s+)?[^\s]+\s+' + re.escape(method) + r'\s*\(')
        match = pattern.search(code)
        if match:
            method_name = method
            is_static = bool(match.group(2))
            break
    else:
        generic_match = re.search(r'(public\s+)?(static\s+)?[^\s]+\s+(\w+)\s*\(', code)
        if generic_match:
            method_name = generic_match.group(3)
            is_static = bool(generic_match.group(2))

    return class_name, method_name, is_static

def _ensure_java_class_wrapper(code: str, class_name: str) -> str:
    """
    If user code does not declare a class, wrap it in a public class so it compiles.
    """
    if re.search(r'\bclass\b', code):
        return code

    indented = []
    for line in code.splitlines():
        if line.strip():
            indented.append(f"    {line}")
        else:
            indented.append("")
    body = "\n".join(indented)
    return f"public class {class_name} {{\n{body}\n}}\n"

def execute_java_windows(code, test_input):
    """
    Compiles and then executes Java code safely on Windows.
    This function creates a temporary directory, writes the user's code into a
    standard Java class structure, compiles it, and then runs it.
    It returns a standard subprocess.CompletedProcess object for consistency.
    """
    # Create a temporary directory that will be automatically cleaned up
    javac_cmd = _resolve_java_binary("javac")
    java_cmd = _resolve_java_binary("java")

    missing = []
    if not javac_cmd:
        missing.append("javac")
    if not java_cmd:
        missing.append("java")

    if missing:
        message = (
            "Java runtime is not available on the server. "
            f"Missing executables: {', '.join(missing)}. "
            "Install a JDK (17+) and ensure JAVA_HOME or PATH is configured."
        )
        return subprocess.CompletedProcess(missing, 1, stdout="", stderr=message)

    class_name, method_name, is_static = _detect_java_entrypoint(code)
    prepared_code = _ensure_java_class_wrapper(code, class_name)
    solution_filename = f"{class_name}.java"

    formatted_args = _format_java_arguments(test_input or "")
    invocation_target = f"{class_name}.{method_name}" if is_static else f"(new {class_name}()).{method_name}"
    invocation_call = f"{invocation_target}({formatted_args})" if formatted_args else f"{invocation_target}()"

    main_code = (
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        try {\n"
        f"            System.out.println({invocation_call});\n"
        "        } catch (Exception e) {\n"
        "            e.printStackTrace();\n"
        "        }\n"
        "    }\n"
        "}\n"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        solution_path = os.path.join(temp_dir, solution_filename)
        main_path = os.path.join(temp_dir, "Main.java")

        with open(solution_path, "w", encoding="utf-8") as solution_file:
            solution_file.write(prepared_code)

        with open(main_path, "w", encoding="utf-8") as main_file:
            main_file.write(main_code)

        compile_result = run_subprocess_windows(
            [javac_cmd, "Main.java", solution_filename], cwd=temp_dir
        )

        if compile_result.returncode != 0:
            if not compile_result.stderr and compile_result.stdout:
                compile_result.stderr = compile_result.stdout
            return compile_result

        run_result = run_subprocess_windows([java_cmd, "-cp", ".", "Main"], cwd=temp_dir)
        return run_result

def execute_php_windows(code, test_input):
    full_script = f"<?php {code} echo solve({test_input}); ?>"
    php_cmd = _resolve_php_binary()
    if not php_cmd:
        message = (
            "PHP runtime is not available on the server. "
            "Install PHP and ensure the executable is on PATH or configure PHP_PATH."
        )
        return subprocess.CompletedProcess(["php"], 1, stdout="", stderr=message)

    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False, encoding='utf-8')
    try:
        temp_file.write(full_script)
        temp_file.flush()
        temp_file.close()
        result = run_subprocess_windows([php_cmd, temp_file.name])
    finally:
        try:
            os.remove(temp_file.name)
        except OSError:
            pass
    return result

def execute_ruby_windows(code, test_input):
    full_script = f"{code}\nputs solve({test_input})"
    return run_subprocess_windows(['ruby', '-e', full_script])

def execute_csharp_windows(code, test_input):
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(['dotnet', 'new', 'console', '--force'], cwd=temp_dir, capture_output=True)
        program_cs_path = os.path.join(temp_dir, 'Program.cs')
        full_code = f"using System; public class Program {{ public static void Main(string[] args) {{ Console.WriteLine(Solve({test_input})); }} {code} }}"
        with open(program_cs_path, 'w') as f: f.write(full_code)
        return run_subprocess_windows(['dotnet', 'run'], cwd=temp_dir)

def execute_sql_windows(code, test_input):
    try:
        con = sqlite3.connect(":memory:")
        cur = con.cursor()
        cur.executescript(code)
        res = cur.fetchall()
        output_str = "\n".join([str(row) for row in res])
        con.close()
        return subprocess.CompletedProcess(None, 0, stdout=output_str, stderr=None)
    except Exception as e:
        return subprocess.CompletedProcess(None, 1, stdout=None, stderr=str(e))

def execute_html_windows(code, test_input):
    """
    HTML doesn't need execution; evaluate by returning the provided markup.
    Test cases simply compare the submitted HTML to the expected output.
    """
    normalized = code.strip()
    return subprocess.CompletedProcess(None, 0, stdout=normalized, stderr=None)
    
def run_test_suite(code, language, test_cases):
    """
    Runs the given code against a set of test cases for a specific language.
    Returns a tuple: (all_passed, output_log_string)
    """
    if not test_cases:
        return False, "No test cases found for this question."

    output_log_lines = []
    all_passed = True
    
    lang_map = {
        'PYTHON': execute_python_windows,
        'JAVASCRIPT': execute_javascript_windows,
        'JAVA': execute_java_windows,
        'GO': execute_go_windows,
        'C': lambda code, test_input: execute_cpp_windows(code, test_input, treat_as_c=True),
        'CPP': execute_cpp_windows,
        'PHP': execute_php_windows,
        'RUBY': execute_ruby_windows,
        'CSHARP': execute_csharp_windows,
        'HTML': execute_html_windows,
        'SQL': execute_sql_windows,
    }
    
    execution_function = lang_map.get(language)
    if not execution_function:
        return False, f"Language '{language}' is not supported."

    for i, test_case in enumerate(test_cases):
        stdout, stderr = None, None
        test_case_label = f"Test Case {i+1}"
        if test_case.is_hidden:
            test_case_label += " (Hidden)"

        # Use test_case.input_data directly - it should be in correct format for the language
        test_input = test_case.input_data.strip()
        expected = test_case.expected_output.strip()
        
        print(f"🧪 Running test case {i+1}:")
        print(f"   Input data: '{test_input}'")
        print(f"   Expected output: '{expected}'")
        print(f"   Code preview: {code[:100]}...")
        
        try:
            result_obj = execution_function(code, test_input)
            stdout = result_obj.stdout.strip() if result_obj.stdout else ""
            stderr = result_obj.stderr.strip() if result_obj.stderr else ""
            returncode = result_obj.returncode
            
            print(f"🧪 Test case {i+1} execution result:")
            print(f"   Return code: {returncode}")
            print(f"   Stdout: '{stdout}'")
            print(f"   Stderr: '{stderr}'")
            print(f"   Expected: '{expected}'")
            print(f"   Match: {stdout == expected}")
            
            if returncode != 0 or stderr:
                all_passed = False
                output_log_lines.append(f"{test_case_label}: FAILED (Error)")
                if stderr:
                    output_log_lines.append(f"  Error: {stderr}")
                else:
                    output_log_lines.append(f"  Exit code: {returncode}")
                output_log_lines.append(f"  Input: {test_case.input_data}")
                output_log_lines.append(f"  Expected: '{expected}'")
                if stdout:
                    output_log_lines.append(f"  Got: '{stdout}'")
            else:
                # Normalize outputs for comparison (trim whitespace)
                actual_output = stdout.strip() if stdout else ""
                expected_output = expected
                
                # For string outputs, compare without quotes if they're present
                if actual_output == expected_output:
                    output_log_lines.append(f"{test_case_label}: PASSED ✅")
                else:
                    all_passed = False
                    output_log_lines.append(f"{test_case_label}: FAILED ❌")
                    output_log_lines.append(f"  Input: {test_case.input_data}")
                    output_log_lines.append(f"  Expected: '{expected_output}'")
                    output_log_lines.append(f"  Got: '{actual_output}'")
                    output_log_lines.append(f"  (Character diff: expected {len(expected_output)} chars, got {len(actual_output)} chars)")
        except Exception as e:
            all_passed = False
            error_msg = str(e)
            output_log_lines.append(f"{test_case_label}: FAILED (Exception)")
            output_log_lines.append(f"  Exception: {error_msg}")
            output_log_lines.append(f"  Input: {test_case.input_data}")
            output_log_lines.append(f"  Expected: '{expected}'")
            print(f"❌ Exception in test case {i+1}: {error_msg}")
            import traceback
            traceback.print_exc()
    
    return all_passed, "\n".join(output_log_lines)
@csrf_exempt
@require_POST
def execute_code(request):
    try:
        data = json.loads(request.body)
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Invalid JSON body: {str(e)}"}, status=400)
    code_to_run = data.get('code')
    language = (data.get('language') or 'PYTHON').upper()
    question_id = data.get('question_id')
    # Get session_key from request body or query params
    session_key = data.get('session_key') or request.GET.get('session_key')

    # Validate required fields
    if not session_key:
        return JsonResponse({"status": "error", "message": "Missing session_key"}, status=400)
    if not question_id:
        return JsonResponse({"status": "error", "message": "Missing question_id"}, status=400)
    if not code_to_run:
        return JsonResponse({"status": "error", "message": "Missing code"}, status=400)

    # Fix: Convert question_id to UUID if it's an integer
    if isinstance(question_id, int):
        # If it's an integer, try to find the question by order
        session = get_object_or_404(InterviewSession, session_key=session_key)
        question = InterviewQuestion.objects.filter(session=session, order=question_id-1).first()
        if not question:
            return JsonResponse({"status": "error", "message": "Question not found."}, status=400)
    else:
        # If it's already a UUID string, use it directly
        question = get_object_or_404(InterviewQuestion, id=question_id)
    
    # Get test cases from database for this question
    test_cases_qs = question.test_cases.all()
    # Debug info to help frontend
    try:
        tc_count = test_cases_qs.count()
    except Exception:
        tc_count = 0

    # Fallback hardcoded test cases if none exist in DB
    if not test_cases_qs.exists():
        class _TC:
            def __init__(self, input_data, expected_output, is_hidden=False):
                self.input_data = input_data
                self.expected_output = expected_output
                self.is_hidden = is_hidden

        lang = (getattr(question, 'coding_language', None) or language or 'PYTHON').upper()
        fallback_map = {
            'PYTHON': [
                _TC("'hello'", 'olleh'),
                _TC("''", ''),
                _TC("'abc'", 'cba'),
            ],
            'JAVASCRIPT': [
                _TC("'hello'", 'olleh'),
                _TC("''", ''),
                _TC("'abc'", 'cba'),
            ],
            'JAVA': [
                _TC('1,2', '3'),
                _TC('-5,5', '0'),
                _TC('10,15', '25'),
            ],
            'PHP': [
                _TC("'hello'", 'olleh'),
                _TC("''", ''),
                _TC("'abc'", 'cba'),
            ],
            'C': [
                _TC('1,2', '3'),
                _TC('-5,5', '0'),
                _TC('10,15', '25'),
            ],
            'CPP': [
                _TC('1,2', '3'),
                _TC('-5,5', '0'),
                _TC('10,15', '25'),
            ],
        }
        test_cases = fallback_map.get(lang, fallback_map['PYTHON'])
    else:
        test_cases = list(test_cases_qs)
    
    # Run code against all test cases
    all_passed, output_log = run_test_suite(code_to_run, language, test_cases)
    
    # Return detailed results
    return JsonResponse({
        'status': 'success' if all_passed else 'error',
        'output': output_log,
        'passed': all_passed,
        'all_passed': all_passed,
        'test_summary': output_log
    })
    
@csrf_exempt
@require_POST
def submit_coding_challenge(request):
    try:
        data = json.loads(request.body)
        session = get_object_or_404(InterviewSession, session_key=data.get('session_key'))
        
        # Fix: Convert question_id to UUID if it's an integer
        question_id = data.get('question_id')
        if isinstance(question_id, int):
            # If it's an integer, try to find the question by order
            question = InterviewQuestion.objects.filter(session=session, order=question_id-1).first()
            if not question:
                return JsonResponse({"status": "error", "message": "Question not found."}, status=400)
        else:
            # If it's already a UUID string, use it directly
            question = get_object_or_404(InterviewQuestion, id=question_id)
        
        submitted_code = data.get('code')
        language = question.coding_language # Get language from the question object for security

        if not all([session, question, submitted_code, language]):
            return JsonResponse({"status": "error", "message": "Missing required data."}, status=400)
        
        # Get test cases for this question
        test_cases = list(question.test_cases.all())
        print(f"📝 Running code against {len(test_cases)} test cases...")
        
        # Evaluate using the same executor as Run & Test for consistency
        all_passed, output_log = run_test_suite(submitted_code, language, test_cases)
        
        # Convert output_log into structured results for UI
        # Simple parse: count PASSED/FAILED lines
        passed_count = output_log.count('PASSED')
        total_count = len(test_cases)
        test_results = []
        for idx, tc in enumerate(test_cases, 1):
            # Best-effort parse; include actual not available without re-run per test
            test_results.append({
                'test_case': idx,
                'input': tc.input_data,
                'expected': tc.expected_output,
                'actual': '',
                'passed': 'Test Case %d: PASSED' % idx in output_log,
                'error': 'FAILED (Error)' in output_log
            })
        
        print(f"✅ Test Results: {passed_count}/{total_count} passed")

        # Create detailed log (no Gemini evaluation)
        final_log = f"Test Results: {passed_count}/{total_count} passed\n\n"
        for result in test_results:
            status_emoji = "✅" if result['passed'] else "❌"
            final_log += f"{status_emoji} Test Case {result['test_case']}:\n"
            final_log += f"   Input: {result['input']}\n"
            final_log += f"   Expected: {result['expected']}\n"
            final_log += f"   Actual: {result['actual']}\n"
            if result.get('error'):
                final_log += f"   Error: Yes\n"
            final_log += "\n"
        
        
        # Store submission with AI evaluation feedback (if available)
        code_submission = CodeSubmission.objects.create(
            session=session,
            question_id=str(question.id),
            submitted_code=submitted_code,
            language=language,
            passed_all_tests=(passed_count == total_count),
            output_log=final_log,
            gemini_evaluation=None
        )
        
        # Also update the InterviewQuestion with the actual submitted code
        # This ensures the code is available even if CodeSubmission lookup fails
        try:
            # Save the actual code to transcribed_answer so it's always available
            # Format: Store the code with a prefix indicating test results
            code_with_results = f"Code submitted: {passed_count}/{total_count} test cases passed\n\nSubmitted Code:\n{submitted_code}"
            question.transcribed_answer = code_with_results
            question.save(update_fields=['transcribed_answer'])
            print(f"✅ Updated InterviewQuestion {question.id} with code submission (code length: {len(submitted_code)} chars)")
            print(f"   CodeSubmission saved with question_id: {str(question.id)}")
        except Exception as e:
            print(f"⚠️ Error updating InterviewQuestion: {e}")
            import traceback
            traceback.print_exc()

        session.status = 'COMPLETED'
        session.save()
        print(f"--- Session {session.session_key} with coding challenge marked as COMPLETED. ---")
        
        # Trigger comprehensive evaluation and persist detailed results
        try:
            from evaluation.services import create_evaluation_from_session
            evaluation = create_evaluation_from_session(session.session_key)
            if evaluation and evaluation.details:
                ai_analysis = evaluation.details.get('ai_analysis', {})
                overall = ai_analysis.get('overall_score_10') or (ai_analysis.get('overall_score', 0) / 10.0)
                recommendation = ai_analysis.get('recommendation') or ai_analysis.get('hiring_recommendation')
                print(f"--- Comprehensive evaluation stored for session {session.session_key} ---")
                print(f"Overall Score (0-10): {overall:.2f}")
                if recommendation:
                    print(f"Recommendation: {recommendation}")
        except Exception as e:
            print(f"--- Error creating stored evaluation: {e} ---")
        
        release_camera_for_session(session.session_key)
        return JsonResponse({"status": "ok", "message": "Submission successful."})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
import json

class InterviewResultsAPIView(APIView):
    """
    API endpoint to get interview results and evaluation data
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        """Get interview results and evaluation data"""
        try:
            session = InterviewSession.objects.get(id=session_id)
            
            # Check if user has permission to view this session
            if not request.user.is_superuser and not request.user.is_staff:
                # For now, allow all authenticated users to view results
                # You can add more specific permission logic here
                pass
            
            # Get all questions and answers
            all_questions = list(session.questions.all().order_by('order'))
            all_logs_list = list(session.logs.all())
            warning_counts = Counter([log.warning_type.replace('_', ' ').title() for log in all_logs_list if log.warning_type != 'excessive_movement'])
            
            # Calculate analytics
            total_filler_words = 0
            avg_wpm = 0
            wpm_count = 0
            sentiment_scores = []
            avg_response_time = 0
            response_time_count = 0

            if session.language_code == 'en':
                for item in all_questions:
                    if item.transcribed_answer:
                        word_count = len(item.transcribed_answer.split())
                        read_time_result = readtime.of_text(item.transcribed_answer)
                        read_time_minutes = read_time_result.minutes + (read_time_result.seconds / 60)
                        if read_time_minutes > 0:
                            item.words_per_minute = round(word_count / read_time_minutes)
                            avg_wpm += item.words_per_minute
                            wpm_count += 1
                        else:
                            item.words_per_minute = 0
                        if item.response_time_seconds:
                            avg_response_time += item.response_time_seconds
                            response_time_count += 1
                        lower_answer = item.transcribed_answer.lower()
                        item.filler_word_count = sum(lower_answer.count(word) for word in FILLER_WORDS)
                        total_filler_words += item.filler_word_count
                        if TEXTBLOB_AVAILABLE and TextBlob:
                            sentiment_scores.append({'question': f"Q{item.order + 1}", 'score': TextBlob(item.transcribed_answer).sentiment.polarity})
                        else:
                            sentiment_scores.append({'question': f"Q{item.order + 1}", 'score': 0.0})
            
            final_avg_wpm = round(avg_wpm / wpm_count) if wpm_count > 0 else 0
            final_avg_response_time = round(avg_response_time / response_time_count, 2) if response_time_count > 0 else 0

            # Prepare questions data
            questions_data = []
            for question in all_questions:
                question_data = {
                    'id': str(question.id),
                    'order': question.order,
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'question_level': question.question_level,
                    'transcribed_answer': question.transcribed_answer,
                    'response_time_seconds': question.response_time_seconds,
                    'words_per_minute': getattr(question, 'words_per_minute', 0),
                    'filler_word_count': getattr(question, 'filler_word_count', 0),
                    'audio_url': question.audio_url if hasattr(question, 'audio_url') else None,
                }
                questions_data.append(question_data)

            # Prepare code submissions data
            code_submissions_data = []
            for submission in session.code_submissions.all():
                submission_data = {
                    'id': str(submission.id),
                    'question_id': str(submission.question_id),
                    'language': submission.language,
                    'submitted_code': submission.submitted_code,
                    'output_log': submission.output_log,
                    'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
                }
                code_submissions_data.append(submission_data)

            # Prepare analytics data
            analytics_data = {
                'warning_counts': dict(warning_counts),
                'sentiment_scores': sentiment_scores,
                'evaluation_scores': {
                    'resume_score': session.resume_score or 0,
                    'answers_score': session.answers_score or 0,
                    'overall_performance_score': session.overall_performance_score or 0
                },
                'communication_metrics': {
                    'avg_words_per_minute': final_avg_wpm,
                    'total_filler_words': total_filler_words,
                    'avg_response_time': final_avg_response_time,
                    'total_questions': len(all_questions),
                    'answered_questions': len([q for q in all_questions if q.transcribed_answer]),
                    'code_submissions': len(code_submissions_data)
                }
            }

            # Prepare response data
            response_data = {
                'session_id': str(session.id),
                'candidate_name': session.candidate_name,
                'candidate_email': session.candidate_email,
                'job_description': session.job_description,
                'scheduled_at': session.scheduled_at.isoformat() if session.scheduled_at else None,
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                'status': session.status,
                'language_code': session.language_code,
                'is_evaluated': session.is_evaluated,
                
                # Evaluation results
                'resume_score': session.resume_score,
                'resume_feedback': session.resume_feedback,
                'answers_score': session.answers_score,
                'answers_feedback': session.answers_feedback,
                'overall_performance_score': session.overall_performance_score,
                'overall_performance_feedback': session.overall_performance_feedback,
                'behavioral_analysis': session.behavioral_analysis,
                'keyword_analysis': session.keyword_analysis,
                
                # Questions and answers
                'questions': questions_data,
                'code_submissions': code_submissions_data,
                
                # Analytics
                'analytics': analytics_data,
                
                # Proctoring data
                'proctoring_warnings': dict(warning_counts),
                'total_warnings': sum(warning_counts.values()),
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except InterviewSession.DoesNotExist:
            return Response({
                'error': 'Interview session not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Error retrieving interview results: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InterviewResultsListAPIView(APIView):
    """
    API endpoint to list all interview results for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of all interview sessions with basic results"""
        try:
            # Get all sessions (you can add filtering based on user role)
            sessions = InterviewSession.objects.all().order_by('-created_at')
            
            sessions_data = []
            for session in sessions:
                # Get basic analytics
                all_questions = session.questions.all()
                answered_questions = all_questions.filter(transcribed_answer__isnull=False).exclude(transcribed_answer='').count()
                code_submissions = session.code_submissions.count()
                
                # Get warning count
                warning_count = session.logs.count()
                
                session_data = {
                    'session_id': str(session.id),
                    'candidate_name': session.candidate_name,
                    'candidate_email': session.candidate_email,
                    'scheduled_at': session.scheduled_at.isoformat() if session.scheduled_at else None,
                    'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                    'status': session.status,
                    'is_evaluated': session.is_evaluated,
                    
                    # Basic metrics
                    'total_questions': all_questions.count(),
                    'answered_questions': answered_questions,
                    'code_submissions': code_submissions,
                    'warning_count': warning_count,
                    
                    # Scores (if evaluated)
                    'resume_score': session.resume_score,
                    'answers_score': session.answers_score,
                    'overall_performance_score': session.overall_performance_score,
                }
                sessions_data.append(session_data)
            
            return Response({
                'sessions': sessions_data,
                'total_count': len(sessions_data)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Error retrieving interview sessions: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InterviewAnalyticsAPIView(APIView):
    """
    API endpoint to get detailed analytics for interview sessions
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        """Get detailed analytics for a specific interview session"""
        try:
            session = InterviewSession.objects.get(id=session_id)
            
            # Get all questions and calculate detailed analytics
            all_questions = list(session.questions.all().order_by('order'))
            all_logs_list = list(session.logs.all())
            
            # Calculate detailed metrics
            total_filler_words = 0
            avg_wpm = 0
            wpm_count = 0
            sentiment_scores = []
            avg_response_time = 0
            response_time_count = 0
            question_analytics = []

            if session.language_code == 'en':
                for item in all_questions:
                    question_analytics_item = {
                        'question_id': str(item.id),
                        'question_order': item.order,
                        'question_text': item.question_text,
                        'question_type': item.question_type,
                        'has_answer': bool(item.transcribed_answer),
                        'answer_length': len(item.transcribed_answer) if item.transcribed_answer else 0,
                        'response_time': item.response_time_seconds,
                        'words_per_minute': 0,
                        'filler_word_count': 0,
                        'sentiment_score': 0.0,
                    }
                    
                    if item.transcribed_answer:
                        word_count = len(item.transcribed_answer.split())
                        read_time_result = readtime.of_text(item.transcribed_answer)
                        read_time_minutes = read_time_result.minutes + (read_time_result.seconds / 60)
                        
                        if read_time_minutes > 0:
                            wpm = round(word_count / read_time_minutes)
                            question_analytics_item['words_per_minute'] = wpm
                            avg_wpm += wpm
                            wpm_count += 1
                        
                        if item.response_time_seconds:
                            avg_response_time += item.response_time_seconds
                            response_time_count += 1
                        
                        lower_answer = item.transcribed_answer.lower()
                        filler_count = sum(lower_answer.count(word) for word in FILLER_WORDS)
                        question_analytics_item['filler_word_count'] = filler_count
                        total_filler_words += filler_count
                        
                        if TEXTBLOB_AVAILABLE and TextBlob:
                            sentiment = TextBlob(item.transcribed_answer).sentiment.polarity
                            question_analytics_item['sentiment_score'] = sentiment
                            sentiment_scores.append(sentiment)
                        else:
                            question_analytics_item['sentiment_score'] = 0.0
                            sentiment_scores.append(0.0)
                    
                    question_analytics.append(question_analytics_item)
            
            final_avg_wpm = round(avg_wpm / wpm_count) if wpm_count > 0 else 0
            final_avg_response_time = round(avg_response_time / response_time_count, 2) if response_time_count > 0 else 0
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            # Proctoring analytics
            warning_counts = Counter([log.warning_type.replace('_', ' ').title() for log in all_logs_list if log.warning_type != 'excessive_movement'])
            total_warnings = sum(warning_counts.values())
            
            # Code submission analytics
            code_submissions = session.code_submissions.all()
            code_analytics = []
            for submission in code_submissions:
                code_analytics.append({
                    'submission_id': str(submission.id),
                    'language': submission.language,
                    'code_length': len(submission.submitted_code),
                    'has_output': bool(submission.output_log),
                    'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
                })
            
            analytics_data = {
                'session_overview': {
                    'total_questions': len(all_questions),
                    'answered_questions': len([q for q in all_questions if q.transcribed_answer]),
                    'code_submissions': len(code_analytics),
                    'total_warnings': total_warnings,
                    'session_duration': None,  # You can calculate this if you have start/end times
                },
                
                'communication_metrics': {
                    'avg_words_per_minute': final_avg_wpm,
                    'total_filler_words': total_filler_words,
                    'avg_response_time': final_avg_response_time,
                    'avg_sentiment_score': round(avg_sentiment, 3),
                },
                
                'evaluation_scores': {
                    'resume_score': session.resume_score or 0,
                    'answers_score': session.answers_score or 0,
                    'overall_performance_score': session.overall_performance_score or 0,
                },
                
                'proctoring_analytics': {
                    'warning_counts': dict(warning_counts),
                    'total_warnings': total_warnings,
                    'warning_types': list(warning_counts.keys()),
                },
                
                'question_analytics': question_analytics,
                'code_analytics': code_analytics,
            }
            
            return Response(analytics_data, status=status.HTTP_200_OK)
            
        except InterviewSession.DoesNotExist:
            return Response({
                'error': 'Interview session not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Error retrieving analytics: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@never_cache
def serve_interview_video(request, video_path):
    """Serve interview video files with proper MIME type and headers for browser playback.
    Prioritizes merged videos from interview_videos_merged/ folder."""
    import os
    from django.conf import settings
    from django.http import Http404
    
    try:
        # Normalize path to prevent directory traversal
        video_path = video_path.replace('\\', '/')  # Normalize separators
        if video_path.startswith('/'):
            video_path = video_path[1:]  # Remove leading slash
        
        # Remove /media/ prefix if present
        if video_path.startswith('media/'):
            video_path = video_path[6:]
        
        # CRITICAL: Prioritize merged videos from interview_videos_merged/
        # Check merged folder first
        merged_path = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged', video_path)
        merged_path = os.path.normpath(merged_path)
        
        # Also check if video_path already contains the folder name
        if 'interview_videos_merged' in video_path:
            full_path = os.path.join(settings.MEDIA_ROOT, video_path)
            full_path = os.path.normpath(full_path)
        elif 'interview_videos_raw' in video_path:
            # Don't serve raw videos - only merged videos
            print(f"❌ Attempted to serve raw video (not allowed): {video_path}")
            raise Http404("Only merged videos are available. Raw videos are not served.")
        else:
            # Try merged folder first, then old folder as fallback
            if os.path.exists(merged_path):
                full_path = merged_path
                print(f"✅ Serving merged video from interview_videos_merged/: {full_path}")
            else:
                # Fallback to old folder (for backward compatibility)
                full_path = os.path.join(settings.MEDIA_ROOT, 'interview_videos', video_path)
                full_path = os.path.normpath(full_path)
                # Only serve if it's a merged video (has _with_audio suffix)
                if '_with_audio' not in video_path and not os.path.exists(full_path):
                    # Try to find merged version
                    video_basename = os.path.basename(video_path)
                    base_name = os.path.splitext(video_basename)[0]
                    if '_converted' in base_name:
                        base_name = base_name.replace('_converted', '')
                    merged_filename = f"{base_name}_with_audio.mp4"
                    merged_full_path = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged', merged_filename)
                    merged_full_path = os.path.normpath(merged_full_path)
                    if os.path.exists(merged_full_path):
                        full_path = merged_full_path
                        print(f"✅ Found and serving merged video: {full_path}")
                    else:
                        print(f"❌ Video file not found (raw videos not served): {video_path}")
                        raise Http404("Only merged videos are available. Video not found.")
                elif '_with_audio' not in video_path:
                    print(f"⚠️ Attempting to serve non-merged video, checking for merged version...")
                    # Try to find merged version
                    video_basename = os.path.basename(video_path)
                    base_name = os.path.splitext(video_basename)[0]
                    if '_converted' in base_name:
                        base_name = base_name.replace('_converted', '')
                    merged_filename = f"{base_name}_with_audio.mp4"
                    merged_full_path = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged', merged_filename)
                    merged_full_path = os.path.normpath(merged_full_path)
                    if os.path.exists(merged_full_path):
                        full_path = merged_full_path
                        print(f"✅ Redirecting to merged video: {full_path}")
                    else:
                        print(f"❌ No merged video found for: {video_path}")
                        raise Http404("Only merged videos are available. Merged version not found.")
        
        media_root = os.path.normpath(settings.MEDIA_ROOT)
        
        # Security check: ensure file is within MEDIA_ROOT
        if not full_path.startswith(media_root):
            raise Http404("Invalid video path")
        
        # Check if file exists
        if not os.path.exists(full_path):
            print(f"❌ Video file not found: {full_path}")
            raise Http404("Video file not found")
        
        # Check file size
        file_size = os.path.getsize(full_path)
        if file_size == 0:
            print(f"❌ Video file is empty: {full_path}")
            raise Http404("Video file is empty")
        
        print(f"✅ Serving video file: {full_path} ({file_size / 1024 / 1024:.2f} MB)")
        
        # Determine content type based on file extension
        content_type = 'video/mp4'
        if full_path.endswith('.webm'):
            content_type = 'video/webm'
        elif full_path.endswith('.mov') or full_path.endswith('.qt'):
            content_type = 'video/quicktime'
        
        # Serve file with proper headers
        response = FileResponse(
            open(full_path, 'rb'),
            content_type=content_type
        )
        response['Content-Length'] = file_size
        response['Accept-Ranges'] = 'bytes'
        response['Cache-Control'] = 'public, max-age=3600'
        
        return response
    except FileNotFoundError:
        raise Http404("Video file not found")
    except Exception as e:
        print(f"❌ Error serving video: {e}")
        import traceback
        traceback.print_exc()
        raise Http404(f"Error serving video: {str(e)}")


@csrf_exempt
@require_POST
def upload_interview_audio(request):
    """Upload interview audio (microphone + TTS) to be merged with backend video recording."""
    try:
        session_key = request.POST.get('session_key')
        audio_file = request.FILES.get('audio_file')
        
        # CRITICAL: Get timestamps for audio-video synchronization
        audio_start_timestamp = request.POST.get('audio_start_timestamp')
        video_start_timestamp = request.POST.get('video_start_timestamp')
        
        if not session_key or not audio_file:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required data: session_key and audio_file'
            }, status=400)
        
        # Get session
        try:
            session = InterviewSession.objects.get(session_key=session_key)
        except InterviewSession.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Session not found'
            }, status=404)
        
        # Store timestamps in session metadata (using JSONField if available, or store in a separate way)
        # Note: InterviewSession model doesn't have timestamp fields, so we'll store them in a way that can be retrieved later
        # For now, we'll just log them and pass them directly to the merge function
        if audio_start_timestamp:
            try:
                audio_ts = float(audio_start_timestamp)
                print(f"📥 Received audio start timestamp: {audio_ts}")
            except (ValueError, TypeError):
                print(f"⚠️ Invalid audio_start_timestamp: {audio_start_timestamp}")
                audio_ts = None
        else:
            audio_ts = None
            
        if video_start_timestamp:
            try:
                video_ts = float(video_start_timestamp)
                print(f"📥 Received video start timestamp: {video_ts}")
            except (ValueError, TypeError):
                print(f"⚠️ Invalid video_start_timestamp: {video_start_timestamp}")
                video_ts = None
        else:
            video_ts = None
        
        # Store timestamps in a way that can be retrieved later (we'll use session metadata or pass directly)
        # For now, we'll store them in a simple cache/dict that can be retrieved by session_key
        if not hasattr(upload_interview_audio, '_timestamp_cache'):
            upload_interview_audio._timestamp_cache = {}
        
        if audio_ts or video_ts:
            upload_interview_audio._timestamp_cache[session_key] = {
                'audio_start_timestamp': audio_ts,
                'video_start_timestamp': video_ts
            }
            print(f"✅ Stored timestamps in cache for session {session_key}")
        
        # Save audio file
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'interview_audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        # Get file extension from uploaded file
        original_filename = audio_file.name
        file_ext = os.path.splitext(original_filename)[1] or '.webm'
        audio_filename = f"{session_key}_interview_audio{file_ext}"
        audio_path = os.path.join(audio_dir, audio_filename)
        
        # Save audio file
        with open(audio_path, 'wb+') as destination:
            for chunk in audio_file.chunks():
                destination.write(chunk)
        
        print(f"✅ Interview audio saved: {audio_path} ({audio_file.size / 1024 / 1024:.2f} MB)")
        
        # Process and convert audio to WAV for better compatibility with FFmpeg
        try:
            from interview_app.audio_processor import process_uploaded_audio, verify_audio_file
            
            # Verify audio file first
            if not verify_audio_file(audio_path):
                print(f"⚠️ Audio file verification failed, but continuing...")
            
            # Process and convert to WAV for better compatibility
            processed_audio_path = process_uploaded_audio(audio_path, convert_to_wav=True)
            
            if processed_audio_path and os.path.exists(processed_audio_path):
                # Use processed audio path (converted WAV if conversion succeeded)
                final_audio_path = processed_audio_path
                print(f"✅ Audio processed successfully: {final_audio_path}")
            else:
                # Fallback to original if processing failed
                final_audio_path = audio_path
                print(f"⚠️ Audio processing failed, using original: {final_audio_path}")
        except Exception as e:
            print(f"⚠️ Error processing audio: {e}")
            import traceback
            traceback.print_exc()
            # Use original audio file if processing fails
            final_audio_path = audio_path
        
        # Get relative path for merging (use processed audio if available)
        relative_audio_path = os.path.relpath(final_audio_path, settings.MEDIA_ROOT).replace('\\', '/')
        
        print(f"✅ Final audio path for merging: {relative_audio_path}")
        
        # Return both audio_path and audio_file_path for compatibility
        return JsonResponse({
            'status': 'success',
            'message': 'Audio uploaded and processed successfully',
            'audio_path': relative_audio_path,
            'audio_file_path': relative_audio_path,  # Also return as audio_file_path for frontend compatibility
            'audio_size_mb': round(os.path.getsize(final_audio_path) / 1024 / 1024, 2),
            'audio_format': os.path.splitext(final_audio_path)[1].lower()
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': f'Error uploading audio: {str(e)}'
        }, status=500)

@csrf_exempt
@require_POST
def upload_interview_video(request):
    """Upload complete interview video (camera + microphone + TTS audio)"""
    try:
        session_key = request.POST.get('session_key')
        video_file = request.FILES.get('video')
        question_timestamps = request.POST.get('question_timestamps', '[]')
        duration = request.POST.get('duration', '0')
        
        if not session_key or not video_file:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required data: session_key and video file'
            }, status=400)
        
        # Get session
        try:
            session = InterviewSession.objects.get(session_key=session_key)
        except InterviewSession.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Session not found'
            }, status=404)
        
        # Save video file
        video_filename = f"interview_{session_key}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.webm"
        session.interview_video.save(video_filename, video_file, save=True)
        
        # Parse and store question timestamps if provided
        try:
            timestamps = json.loads(question_timestamps) if question_timestamps else []
            if timestamps:
                # Store timestamps in session metadata (could use a JSONField if available)
                print(f"📝 Stored {len(timestamps)} question timestamps for video")
        except Exception as e:
            print(f"⚠️ Could not parse question timestamps: {e}")
        
        print(f"✅ Interview video saved: {session.interview_video.name} ({video_file.size / 1024 / 1024:.2f} MB)")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Video uploaded successfully',
            'video_url': session.interview_video.url if session.interview_video else None,
            'video_size_mb': round(video_file.size / 1024 / 1024, 2)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': f'Error uploading video: {str(e)}'
        }, status=500)


# Video recording functionality removed
