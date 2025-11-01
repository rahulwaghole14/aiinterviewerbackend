import os
import google.generativeai as genai
from numpy._core.numeric import False_
import whisper
import PyPDF2
import docx
import re
import json
import threading
import csv
# from gtts import gTTS  # Removed - using only Google Cloud TTS
from pathlib import Path
from dotenv import load_dotenv
import pytz
from textblob import TextBlob
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
import cv2
import base64
from django.utils import timezone
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
import urllib.parse


from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
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
from weasyprint import HTML

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
    def detect_face_with_yolo(img): return [type('obj', (object,), {'boxes': []})()]


load_dotenv()
# Use hardcoded API key for now (same as other files)
gemini_api_key = "AIzaSyBU4ZmzsBdCUGlHg4eZCednvOwL4lqDVtw"
try:
    from django.conf import settings as dj_settings
    active_key = getattr(dj_settings, 'GEMINI_API_KEY', gemini_api_key)
    if active_key:
        genai.configure(api_key=active_key)
except Exception:
    pass
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
# --- DEVELOPMENT MODE SWITCH ---
# Set to True to use hardcoded questions and skip AI generation for faster testing.
# This does NOT affect AI evaluation in the report or email sending.
DEV_MODE = False

try:
    whisper_model = whisper.load_model("base")
    print("Whisper model 'base' loaded.")
except Exception as e:
    print(f"Error loading Whisper model: {e}"); whisper_model = None

FILLER_WORDS = ['um', 'uh', 'er', 'ah', 'like', 'okay', 'right', 'so', 'you know', 'i mean', 'basically', 'actually', 'literally']
CAMERAS, camera_lock = {}, threading.Lock()

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

def release_camera_for_session(session_key):
    with camera_lock:
        if session_key in CAMERAS:
            print(f"--- Releasing camera for session {session_key} ---")
            CAMERAS[session_key].cleanup()
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

        interview_url = request.build_absolute_uri(f"/?session_key={session.session_key}")

        try:
            scheduled_time_str = aware_datetime.strftime('%A, %B %d, %Y at %I:%M %p %Z')
            
            email_subject = "Your Talaro Interview Invitation"
            email_body = (
                f"Dear {candidate_name},\n\n"
                f"Your AI screening interview has been scheduled for: {scheduled_time_str}.\n\n"
                "Please use the following unique link to begin your interview at the scheduled time. "
                "The link will become active at the start time and will expire 10 minutes after.\n"
                f"{interview_url}\n\n"
                "Best of luck!\n"
            )
            
            send_mail(
                email_subject,
                email_body,
                os.getenv('EMAIL_HOST_USER'),
                [candidate_email],
                fail_silently=False,
            )
            print(f"--- Invitation sent to {candidate_email} via Gmail SMTP ---")
        except Exception as e:
            print(f"ERROR sending email: {e}")
            return render(request, 'interview_app/create_invite.html', {'error': f'Could not send email. Please check your .env settings and ensure you are using a Google App Password. Error: {e}', 'languages': SUPPORTED_LANGUAGES})

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
            
            # Generate interview link
            base_url = request.build_absolute_uri('/')
            interview_link = f"{base_url}?session_key={session.session_key}"
            
            return JsonResponse({
                'success': True,
                'interview_link': interview_link,
                'session_key': session.session_key,
                'session_id': str(session.id),
                'candidate_name': session.candidate_name,
                'candidate_email': session.candidate_email,
                'scheduled_at': session.scheduled_at.isoformat() if session.scheduled_at else None,
                'status': session.status
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
        credentials_path = os.path.join(settings.BASE_DIR, "ringed-reach-471807-m3-cf0ec93e3257.json")
        if os.path.exists(credentials_path):
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
                # Create hardcoded question if none exist
                # Determine language from session or URL param
                allowed_langs = {'PYTHON', 'JAVASCRIPT', 'C', 'CPP', 'JAVA', 'GO', 'HTML', 'PHP'}
                requested_lang = None
                try:
                    if session.keyword_analysis and 'CODING_LANG=' in session.keyword_analysis:
                        requested_lang = session.keyword_analysis.split('CODING_LANG=')[1].split()[0].upper()
                except Exception:
                    requested_lang = None
                if not requested_lang:
                    requested_lang = (request.GET.get('lang') or 'PYTHON').upper()
                if requested_lang not in allowed_langs:
                    requested_lang = 'PYTHON'
                
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
                
                # Save to database
                for i, coding_q in enumerate(coding_questions):
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
                    
                    # Add dynamic coding questions based on job profile using Gemini API
                    job_title = None
                    domain_name = None
                    if hasattr(session, 'interview') and session.interview and session.interview.job:
                        job_title = session.interview.job.job_title
                        if session.interview.job.domain:
                            domain_name = session.interview.job.domain.name
                    
                    # Use Gemini API for dynamic question generation
                    from interview_app_11.gemini_question_generator import get_coding_questions_from_gemini
                    coding_questions = get_coding_questions_from_gemini(job_title, domain_name)
                
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
                
                # Save coding questions to database and update coding_questions_data with real IDs
                for i, coding_q in enumerate(coding_questions):
                    coding_question_obj = InterviewQuestion.objects.create(
                        session=session,
                        question_text=coding_q['description'],
                        question_type='CODING',
                        coding_language=coding_q['language'],
                        order=len(all_questions) + i,
                        question_level='MAIN'
                    )
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
                
                # Add coding question
                coding_questions = [
                    {
                        'id': 'coding_1',
                        'type': 'CODING',
                        'title': 'Reverse String',
                        'description': 'Write a function that reverses a string. For example, if the input is "hello", the output should be "olleh".',
                        'language': 'PYTHON',
                        'starter_code': 'def reverse_string(s):\n    # Your code here\n    pass',
                        'test_cases': [
                            {'input': '"hello"', 'output': 'olleh'},
                            {'input': '"world"', 'output': 'dlrow'},
                            {'input': '"python"', 'output': 'nohtyp'}
                        ]
                    }
                ]
            else:
                print("--- RUNNING IN PRODUCTION MODE: Calling Gemini API. ---")
                model = genai.GenerativeModel('gemini-2.5-flash')
                summary_prompt = f"Summarize key skills from the following resume:\n\n{session.resume_text}"
                summary_response = model.generate_content(summary_prompt)
                session.resume_summary = summary_response.text
                language_name = SUPPORTED_LANGUAGES.get(session.language_code, 'English')
                master_prompt = (
                    f"You are an expert Talaro interviewer.Your task is to generate 5 insightful interview 1-2 liner questions in {language_name}. "
                    f"The interview is for a '{session.job_description.splitlines()[0]}' role. "
                    "starting from introduction question .Please base the questions on the provided job description and candidate's resume. "
                    "Start with a welcoming ice-breaker question that also references something specific from the candidate's resume. "
                    "Then, generate a mix of technical Questions. 70 percent from jd and 30 percent from resume"
                    "You MUST format the output as Markdown. "
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
                
                # HARD-CODED SINGLE CODING QUESTION PER LANGUAGE (no Gemini)
                # Allow selecting language via ?lang=PYTHON (defaults to PYTHON)
                allowed_langs = {
                    'PYTHON', 'JAVASCRIPT', 'C', 'CPP', 'JAVA', 'GO', 'HTML', 'PHP'
                }
                # Prioritize language chosen at scheduling time if stored
                requested_lang = None
                try:
                    if session.keyword_analysis and 'CODING_LANG=' in session.keyword_analysis:
                        requested_lang = session.keyword_analysis.split('CODING_LANG=')[1].split()[0].upper()
                except Exception:
                    requested_lang = None
                if not requested_lang:
                    requested_lang = (request.GET.get('lang') or 'PYTHON').upper()
                if requested_lang not in allowed_langs:
                    requested_lang = 'PYTHON'

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
            model = genai.GenerativeModel('gemini-2.5-flash')
            
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
                    sentiment_scores.append({'question': f"Q{item.order + 1}", 'score': TextBlob(item.transcribed_answer).sentiment.polarity})
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
        if not session_key:
            return JsonResponse({"status": "error", "message": "Session key required."}, status=400)
        
        session = InterviewSession.objects.get(session_key=session_key)
        if session.status == 'SCHEDULED':
            session.status = 'COMPLETED'
            session.save()
            print(f"--- Spoken-only session {session_key} marked as COMPLETED. ---")
            
            # Trigger comprehensive evaluation for spoken-only interviews
            try:
                from interview_app_11.comprehensive_evaluation_service import comprehensive_evaluation_service
                evaluation_results = comprehensive_evaluation_service.evaluate_complete_interview(session_key)
                print(f"--- Comprehensive evaluation completed for session {session_key} ---")
                print(f"Overall Score: {evaluation_results['overall_score']:.1f}/100")
                print(f"Recommendation: {evaluation_results['recommendation']}")
            except Exception as e:
                print(f"--- Error in comprehensive evaluation: {e} ---")
            
        release_camera_for_session(session_key)
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_POST
def submit_coding_challenge(request):
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        question_id = data.get('question_id')
        submitted_code = data.get('code')
        language = data.get('language')

        if not all([session_key, question_id, submitted_code, language]):
            return JsonResponse({"status": "error", "message": "Missing required data."}, status=400)

        session = get_object_or_404(InterviewSession, session_key=session_key)
        question = get_object_or_404(InterviewQuestion, id=question_id)

        CodeSubmission.objects.create(
            session=session,
            question=question,
            submitted_code=submitted_code,
            language=language,
            passed_all_tests=False # Placeholder, would need full test suite logic
        )

        session.status = 'COMPLETED'
        session.save()
        print(f"--- Session {session_key} with coding challenge marked as COMPLETED. ---")
        
        release_camera_for_session(session_key)
        return JsonResponse({"status": "ok", "message": "Submission successful."})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def interview_complete(request):
    session_key = request.GET.get('session_key')
    context = {}
    if session_key:
        context['session_key'] = session_key
        # Also release camera resources when complete page is accessed
        try:
            release_camera_for_session(session_key)
        except Exception as e:
            print(f"Error releasing camera for session {session_key}: {e}")
    
    template = loader.get_template('interview_app/interview_complete.html')
    return HttpResponse(template.render(context, request))

def generate_and_save_follow_up(session, parent_question, transcribed_answer):
    if DEV_MODE:
        print("--- DEV MODE: Skipping AI follow-up question generation. ---")
        return None

    model = genai.GenerativeModel('gemini-2.5-flash')
    language_name = SUPPORTED_LANGUAGES.get(session.language_code, 'English')
    prompt = (
        f"You are an expert, friendly interviewer conducting an interview in {language_name}. "
        f"The candidate was asked the following question:\n'{parent_question.question_text}'\n\n"
        f"The candidate gave this transcribed answer:\n'{transcribed_answer}'\n\n"
        "Your task is to analyze the response and act as a conversational partner. Follow these rules strictly:\n"
        "1. If the candidate explicitly states they are unsure, don't know, or only know the basics "
        "(e.g., 'I am not sure', 'I only have basic knowledge of that...'), "
        "then you MUST generate ONE single, simpler, follow-up question. Make it interactive by referencing their statement. "
        "For example, if they say 'I only know the basics of Django ORM', your follow-up could be: "
        "'That's perfectly fine. Could you then explain what you know about the basic 'filter' and 'get' methods?'\n"
        "2. If the answer is confident, complete, or does not express uncertainty, you MUST respond with the exact text: NO_FOLLOW_UP\n"
        "Do NOT add any other text, prefixes, or formatting. Your entire output must be either the conversational follow-up question itself or the text 'NO_FOLLOW_UP'."
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
    if not whisper_model: return JsonResponse({'error': 'Whisper model not available.'}, status=500)
    if request.method == 'POST' and request.FILES.get('audio_data'):
        audio_file = request.FILES['audio_data']
        session_id = request.POST.get('session_id')
        question_id = request.POST.get('question_id')
        response_time = request.POST.get('response_time')
        
        file_path = default_storage.save('temp_audio.webm', audio_file)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        try:
            result = whisper_model.transcribe(full_path, fp16=False)
            transcribed_text = result.get('text', '')
            follow_up_data = None

            if session_id and question_id:
                try:
                    question_to_update = InterviewQuestion.objects.get(id=question_id, session_id=session_id)
                    
                    question_to_update.transcribed_answer = transcribed_text
                    if response_time:
                        question_to_update.response_time_seconds = float(response_time)
                    question_to_update.save()

                    # Only generate a follow-up if the question just answered was a MAIN one
                    if transcribed_text and question_to_update.question_level == 'MAIN' and question_to_update.session.language_code == 'en':
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
            if os.path.exists(full_path): os.remove(full_path)
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

def video_frame(request):
    """Return a single JPEG frame (for polling-based display)"""
    session_key = request.GET.get('session_key')
    camera = get_camera_for_session(session_key)
    if not camera:
        # Return a minimal error frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, "Camera Not Found", (20, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        ok, buf = cv2.imencode('.jpg', frame)
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
def check_camera(request):
    session_key = request.GET.get('session_key')
    camera = get_camera_for_session(session_key)
    if camera and camera.video.isOpened():
        return JsonResponse({"status": "ok"})
    else:
        release_camera_for_session(session_key)
        return JsonResponse({"status": "error"}, status=500)

@csrf_exempt
@require_POST
def activate_proctoring_camera(request):
    """Explicitly activate camera and YOLOv8n detection when technical interview starts"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        if not session_key:
            return JsonResponse({'status': 'error', 'message': 'session_key required'}, status=400)
        
        # Get or create camera for this session
        camera = get_camera_for_session(session_key)
        
        if not camera:
            return JsonResponse({'status': 'error', 'message': 'Could not create camera'}, status=500)
        
        # Ensure camera is running and detection loop is active
        if hasattr(camera, 'video') and camera.video.isOpened():
            if not camera._running:
                # Restart detection loop if it stopped
                import threading
                camera._running = True
                if hasattr(camera, '_detector_thread'):
                    if not camera._detector_thread.is_alive():
                        camera._detector_thread = threading.Thread(target=camera._capture_and_detect_loop, daemon=True)
                        camera._detector_thread.start()
                        print(f"✅ YOLOv8n detection loop reactivated for session {str(camera.session_id)[:8]}")
                else:
                    # Start detection loop if it doesn't exist
                    camera._detector_thread = threading.Thread(target=camera._capture_and_detect_loop, daemon=True)
                    camera._detector_thread.start()
                    print(f"✅ YOLOv8n detection loop started for session {str(camera.session_id)[:8]}")
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Camera and YOLOv8n detection activated',
                'camera_active': True,
                'detection_running': camera._running if hasattr(camera, '_running') else False
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
    session_key = request.GET.get('session_key', '')
    return render(request, 'interview_app/chatbot_direct_deepgram.html', {
        'session_key': session_key
    })

@csrf_exempt
@require_POST
def ai_start(request):
    from .complete_ai_bot import start_interview
    from .models import InterviewSession as DjangoSession
    
    print(f"\n{'='*60}")
    print(f"🎯 AI_START called (using simple_ai_bot)")
    print(f"{'='*60}")
    try:
        data = json.loads(request.body.decode('utf-8'))
        print(f"📦 Received JSON data: {data}")
    except Exception as e:
        print(f"⚠️ JSON parse failed: {e}, using POST data")
        data = request.POST
    
    session_key = data.get('session_key', '')
    print(f"🔑 Session Key: {session_key}")
    
    # Get candidate name and JD from database
    candidate_name = 'Candidate'
    jd_text = ''
    
    if session_key:
        try:
            django_session = DjangoSession.objects.get(session_key=session_key)
            candidate_name = django_session.candidate_name
            jd_text = django_session.job_description or ''
            print(f"✅ Retrieved from DB:")
            print(f"   Candidate: {candidate_name}")
            print(f"   JD length: {len(jd_text)}")
        except DjangoSession.DoesNotExist:
            print(f"❌ Session not found in DB")
            return JsonResponse({"error": "Invalid session key"}, status=400)
    
    # Call simple AI bot (exact copy of app.py logic)
    result = start_interview(candidate_name, jd_text)
    
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
    from .complete_ai_bot import upload_answer
    
    try:
        # Support both multipart and JSON
        session_id = request.POST.get('session_id')
        if not session_id and request.body:
            data = json.loads(request.body.decode('utf-8'))
            session_id = data.get('session_id')
            transcript = data.get('transcript', '')
        else:
            transcript = (request.POST.get('transcript') or '').strip()
        
        print(f"\n{'='*60}")
        print(f"📝 AI_UPLOAD_ANSWER called")
        print(f"   Session ID: {session_id}")
        print(f"   Transcript: {transcript[:100] if transcript else 'Empty'}...")
        print(f"{'='*60}")
        
        result = upload_answer(session_id, transcript)
        
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
            pdf_bytes = ai_comprehensive_pdf_django(session_key)
            
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
        
        full_image = cv2.imread(tmp_path)
        if full_image is None:
            return JsonResponse({'status': 'error', 'message': 'Invalid image format.'})

        results = detect_face_with_yolo(full_image)
        boxes = results[0].boxes if results and hasattr(results[0], 'boxes') else []
        num_faces_detected = len(boxes)

        # Check for exactly two faces (candidate + ID photo)
        if num_faces_detected != 2:
            if num_faces_detected < 2:
                message = f"Verification failed. Only {num_faces_detected} face(s) detected. Please ensure both your live face and the face on your ID card are clearly visible and well-lit."
            else:
                message = f"Verification failed. {num_faces_detected} faces detected. Please ensure only you and your ID card are in the frame, with no other people in the background."
            return JsonResponse({'status': 'error', 'message': message})

        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
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
        elif session.candidate_name.lower().split()[0] not in name.lower():
             return JsonResponse({'status': 'error', 'message': f"Name on ID ('{name}') does not match the registered name ('{session.candidate_name}')."})

        session.id_verification_status = 'Verified'
        session.save()

        return JsonResponse({'status': 'success', 'message': 'Verification successful!'})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}, status=500)
    pass

# --- Multi-Language Code Execution Logic (Windows Compatible) ---
def run_subprocess_windows(command, cwd=None, input_data=None):
    try:
        # Reduced timeout to 5 seconds per test case for faster execution
        # Multiple test cases can accumulate, so keep individual timeouts very short
        result = subprocess.run(command, capture_output=True, text=True, timeout=5, cwd=cwd, input=input_data)
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

def execute_java_windows(code, test_input):
    """
    Compiles and then executes Java code safely on Windows.
    This function creates a temporary directory, writes the user's code into a
    standard Java class structure, compiles it, and then runs it.
    It returns a standard subprocess.CompletedProcess object for consistency.
    """
    # Create a temporary directory that will be automatically cleaned up
    with tempfile.TemporaryDirectory() as temp_dir:
        java_file_path = os.path.join(temp_dir, 'Main.java')
        
        # The user's code is injected into a complete, runnable Java class structure.
        # The question prompt must instruct the user to provide only the method body.
        # For example: "Write a public static String solve(String s) { ... }"
        full_code = f"""
        public class Main {{
            // --- Start of User's Injected Code ---
            {code}
            // --- End of User's Injected Code ---
            
            // The main method that will execute the user's function with the test case input.
            public static void main(String[] args) {{
                try {{
                    // This simple input handling works for primitive types like numbers and strings.
                    // For more complex types, this part would need to be more sophisticated.
                    System.out.println(solve({test_input}));
                }} catch (Exception e) {{
                    e.printStackTrace();
                }}
            }}
        }}
        """
        
        # Write the complete Java code to a temporary file
        with open(java_file_path, 'w') as f:
            f.write(full_code)

        # Step 1: Compile the code using the Java Compiler (javac).
        # 'javac' must be in the system's PATH environment variable.
        # We run this command inside the temporary directory.
        compile_result = run_subprocess_windows(['javac', java_file_path], cwd=temp_dir)
        
        # If the compiler returns anything in stderr, it means there was a compilation error
        # (e.g., a syntax error). We should stop here and return that error.
        if compile_result.stderr:
            return compile_result

        # Step 2: If compilation was successful, run the compiled code using the Java runtime (java).
        # 'java' must also be in the system's PATH.
        # The '-cp .' command tells Java to look for class files in the current directory.
        run_result = run_subprocess_windows(['java', '-cp', '.', 'Main'], cwd=temp_dir)
        
        # Return the result of the execution (which will contain stdout or any runtime errors).
        return run_result

def execute_php_windows(code, test_input):
    full_script = f"<?php {code} echo solve({test_input}); ?>"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as temp_file:
        temp_file.write(full_script)
        temp_file.flush()
    result = run_subprocess_windows(['php', temp_file.name])
    os.remove(temp_file.name)
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
        'PHP': execute_php_windows,
        'RUBY': execute_ruby_windows,
        'CSHARP': execute_csharp_windows,
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
        
        
        # Store submission without AI evaluation
        CodeSubmission.objects.create(
            session=session,
            question_id=str(question.id),
            submitted_code=submitted_code,
            language=language,
            passed_all_tests=(passed_count == total_count),
            output_log=final_log,
            gemini_evaluation=None
        )

        session.status = 'COMPLETED'
        session.save()
        print(f"--- Session {session.session_key} with coding challenge marked as COMPLETED. ---")
        
        # Trigger comprehensive evaluation
        try:
            from interview_app_11.comprehensive_evaluation_service import comprehensive_evaluation_service
            evaluation_results = comprehensive_evaluation_service.evaluate_complete_interview(session.session_key)
            print(f"--- Comprehensive evaluation completed for session {session.session_key} ---")
            print(f"Overall Score: {evaluation_results['overall_score']:.1f}/100")
            print(f"Recommendation: {evaluation_results['recommendation']}")
        except Exception as e:
            print(f"--- Error in comprehensive evaluation: {e} ---")
        
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
                        
                        sentiment = TextBlob(item.transcribed_answer).sentiment.polarity
                        question_analytics_item['sentiment_score'] = sentiment
                        sentiment_scores.append(sentiment)
                    
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