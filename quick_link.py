import os, django, pytz
from datetime import datetime, timedelta
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.models import InterviewSession
from interviews.models import Interview, InterviewSlot, InterviewSchedule
from candidates.models import Candidate
from jobs.models import Job
from companies.models import Company

ist, utc = pytz.timezone('Asia/Kolkata'), pytz.UTC
target_date = datetime.now(ist).date()
target_time_ist = datetime.now(ist)
target_time_utc = target_time_ist.astimezone(utc)
end_time_utc = target_time_utc + timedelta(minutes=10)

candidate = Candidate.objects.filter(email="paturkardhananjay4321@gmail.com").first()
company = Company.objects.filter(name="TechCorp Solutions").first()
job = Job.objects.filter(job_title="Data Scientist", company_name=company.name).first()

slot, _ = InterviewSlot.objects.get_or_create(
    interview_date=target_date, start_time=target_time_utc.time(),
    end_time=end_time_utc.time(), company=company, defaults={'status': 'AVAILABLE'}
)

interview = Interview.objects.create(
    candidate=candidate, job=job, started_at=target_time_utc,
    ended_at=end_time_utc, status='SCHEDULED'
)

schedule = InterviewSchedule.objects.create(interview=interview, slot=slot, status='SCHEDULED')
link_token = interview.generate_interview_link()
session_key = interview.session_key

print(f"\n{'='*70}")
print(f"TEST LINK (ACTIVE NOW):")
print(f"   http://127.0.0.1:8000/?session_key={session_key}")
print(f"{'='*70}")
print(f"\nInstructions:")
print(f"1. Open link in browser")
print(f"2. Complete camera + ID verification")
print(f"3. Open browser console (F12)")
print(f"4. Watch for colorful debug logs showing each step")
print(f"5. Check Django terminal for /ai/start logs")
print(f"\n{'='*70}\n")
