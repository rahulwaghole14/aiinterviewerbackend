import os, django, pytz
from datetime import datetime, timedelta
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.models import InterviewSession
from interviews.models import Interview, InterviewSlot, InterviewSchedule
from candidates.models import Candidate
from jobs.models import Job
from companies.models import Company

# Generate a clean session key
clean_session_key = uuid.uuid4().hex
print(f"Generated clean session key: {clean_session_key}")

# Create a simple InterviewSession directly
candidate = Candidate.objects.filter(email="paturkardhananjay4321@gmail.com").first()
if not candidate:
    print("❌ Candidate not found!")
    exit(1)

company = Company.objects.filter(name="TechCorp Solutions").first()
if not company:
    print("❌ Company not found!")
    exit(1)

job = Job.objects.filter(job_title="Data Scientist", company_name=company.name).first()
if not job:
    print("❌ Job not found!")
    exit(1)

# Create InterviewSession directly
session, created = InterviewSession.objects.get_or_create(
    session_key=clean_session_key,
    defaults={
        "candidate_name": candidate.full_name,
        "candidate_email": candidate.email,
        "job_description": job.tech_stack_details or "Data Scientist role",
        "resume_text": getattr(candidate, "resume_text", "") or "Experienced professional seeking new opportunities.",
        "language_code": "en",
        "accent_tld": "com",
    }
)

if created:
    print(f"✅ Created new InterviewSession: {session.id}")
else:
    print(f"✅ Using existing InterviewSession: {session.id}")

print(f"\n{'='*70}")
print(f"CLEAN TEST LINK:")
print(f"   http://127.0.0.1:8000/?session_key={clean_session_key}")
print(f"{'='*70}")
print(f"Session ID: {session.id}")
print(f"Session Key: {session.session_key}")
print(f"{'='*70}\n")
