from django.core.mail import send_mail
from django.conf import settings
from interviews.models import Interview
from notifications.services import NotificationService

print('🔍 Debug Interview Link Generation Issue')
print('=' * 50)

# Get recent interviews
interviews = Interview.objects.all().order_by('-created_at')[:3]

for i, interview in enumerate(interviews):
    print(f'\n📋 Interview {i+1}:')
    print(f'ID: {interview.id}')
    print(f'Candidate: {interview.candidate}')
    print(f'Status: {interview.status}')
    print(f'Session Key: {interview.session_key}')
    print(f'Interview Link: {interview.interview_link}')
    print(f'Scheduled Time: {interview.scheduled_time}')
    print(f'Started At: {interview.started_at}')
    print(f'Ended At: {interview.ended_at}')
    
    # Check if interview has link generation data
    if interview.candidate:
        print(f'Candidate Email: {interview.candidate.email}')
        
        # Test link generation
        try:
            print(f'\n🔗 Testing link generation...')
            link = interview.generate_interview_link()
            print(f'Generated Link Token: {link}')
            
            # Refresh to see updated values
            interview.refresh_from_db()
            print(f'Updated Session Key: {interview.session_key}')
            print(f'Updated Interview Link: {interview.interview_link}')
            
            # Test URL generation
            if interview.session_key:
                from interview_app.utils import get_interview_url
                url = get_interview_url(interview.session_key)
                print(f'Full Interview URL: {url}')
            else:
                print('❌ No session key generated')
                
        except Exception as e:
            print(f'❌ Link generation failed: {e}')
            import traceback
            traceback.print_exc()

# Test the email function with link debugging
if interviews:
    test_interview = interviews[0]
    print(f'\n📧 Testing email with interview {test_interview.id}...')
    
    # Check what URL would be included in email
    candidate_email = test_interview.candidate.email if test_interview.candidate else None
    session_key = test_interview.session_key
    
    if session_key:
        from interview_app.utils import get_interview_url
        interview_url = get_interview_url(session_key)
        print(f'🔗 URL that would be in email: {interview_url}')
    else:
        print('❌ No session key - no interview link in email')

print(f'\n🔧 Configuration:')
print(f'BACKEND_URL: {getattr(settings, "BACKEND_URL", "Not set")}')
