from django.core.mail import send_mail
from django.conf import settings
from interviews.models import Interview
from candidates.models import Candidate
from jobs.models import Job
from companies.models import Company
from notifications.services import NotificationService

print('🔍 Debug Interview Creation Email Issue')
print('=' * 50)

# Check recent interviews and their statuses
print('\n📋 Recent Interviews with Status:')
interviews = Interview.objects.all().order_by('-created_at')[:5]
for interview in interviews:
    print(f'ID: {interview.id}')
    print(f'  Status: "{interview.status}"')
    print(f'  Candidate: {interview.candidate}')
    print(f'  Created: {interview.created_at}')
    print('---')

# Test the status condition
print('\n🧪 Testing Email Status Condition:')
for interview in interviews[:3]:
    print(f'Interview {interview.id}:')
    print(f'  Status: "{interview.status}"')
    print(f'  In ["scheduled", "confirmed"]?: {interview.status in ["scheduled", "confirmed"]}')
    
    if interview.status in ["scheduled", "confirmed"]:
        print('  ✅ Should send email')
        try:
            result = NotificationService.send_candidate_interview_scheduled_notification(interview)
            print(f'  Email result: {result}')
        except Exception as e:
            print(f'  Email error: {e}')
    else:
        print('  ❌ Will NOT send email (wrong status)')
    print('---')

# Check what status values are actually being used
print('\n📊 All Interview Status Values:')
unique_statuses = Interview.objects.values_list('status', flat=True).distinct()
for status in unique_statuses:
    count = Interview.objects.filter(status=status).count()
    print(f'  "{status}": {count} interviews')

# Test creating a new interview to see what happens
print('\n🧪 Test Interview Creation:')
try:
    # Get test data
    company = Company.objects.first()
    candidate = Candidate.objects.first()
    job = Job.objects.first()
    
    if all([company, candidate, job]):
        print(f'Creating test interview for {candidate.email}...')
        
        # Create interview with explicit status
        test_interview = Interview.objects.create(
            candidate=candidate,
            job=job,
            status='scheduled'  # Explicitly set to scheduled
        )
        
        print(f'Created interview {test_interview.id} with status "{test_interview.status}"')
        
        # Test email immediately
        result = NotificationService.send_candidate_interview_scheduled_notification(test_interview)
        print(f'Email result: {result}')
        
        # Clean up
        test_interview.delete()
        print('Test interview deleted')
    else:
        print('Missing test data (company, candidate, or job)')
        
except Exception as e:
    print(f'Test creation failed: {e}')
    import traceback
    traceback.print_exc()

print(f'\n🔧 Email Configuration:')
print(f'Email Backend: {settings.EMAIL_BACKEND}')
print(f'Use SendGrid: {getattr(settings, "USE_SENDGRID", False)}')
