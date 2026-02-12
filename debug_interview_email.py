from django.core.mail import send_mail
from django.conf import settings
from interviews.models import Interview
from candidates.models import Candidate
from notifications.services import NotificationService

print('🔍 Debug Interview Email Issues')
print('=' * 50)

# Check recent interviews
print('\n📋 Recent Interviews:')
interviews = Interview.objects.all().order_by('-created_at')[:5]
for interview in interviews:
    print(f'ID: {interview.id}')
    print(f'  Candidate: {interview.candidate}')
    print(f'  Status: {interview.status}')
    print(f'  Session Key: {interview.session_key}')
    print(f'  Interview Link: {interview.interview_link}')
    print(f'  Started At: {interview.started_at}')
    print(f'  Ended At: {interview.ended_at}')
    print('---')

# Test with a specific interview
if interviews:
    test_interview = interviews[0]
    print(f'\n🧪 Testing with Interview ID: {test_interview.id}')
    print(f'Candidate: {test_interview.candidate}')
    
    if test_interview.candidate:
        print(f'Candidate Email: {test_interview.candidate.email}')
        print(f'Candidate Name: {test_interview.candidate.full_name}')
    else:
        print('❌ No candidate linked to interview')
    
    # Test the email function
    print(f'\n📧 Testing email function...')
    try:
        result = NotificationService.send_candidate_interview_scheduled_notification(test_interview)
        print(f'Email result: {result}')
    except Exception as e:
        print(f'❌ Email function failed: {e}')
        import traceback
        traceback.print_exc()
else:
    print('❌ No interviews found')

# Test simple email (working)
print(f'\n📧 Testing simple email (should work)...')
try:
    result = send_mail(
        'Simple Test Email',
        'This is the simple test email that works.',
        settings.DEFAULT_FROM_EMAIL,
        ['paturkardhananjay9075@gmail.com'],
        fail_silently=False
    )
    print(f'✅ Simple email result: {result}')
except Exception as e:
    print(f'❌ Simple email failed: {e}')

print(f'\n🔧 Email Configuration:')
print(f'Email Backend: {settings.EMAIL_BACKEND}')
print(f'Use SendGrid: {getattr(settings, "USE_SENDGRID", False)}')
print(f'Default From: {settings.DEFAULT_FROM_EMAIL}')
