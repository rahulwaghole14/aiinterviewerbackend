from interviews.models import Interview
from notifications.services import NotificationService

print('🔍 Debug Interview URL in Email')
print('=' * 50)

# Get a recent interview
interview = Interview.objects.all().order_by('-created_at').first()
if interview:
    print(f'Interview ID: {interview.id}')
    print(f'Candidate: {interview.candidate}')
    print(f'Status: {interview.status}')
    print(f'Session Key: {interview.session_key}')
    print(f'Interview Link: {interview.interview_link}')
    print(f'Scheduled Time: {interview.scheduled_time}')
    
    # Manually test URL generation logic
    candidate_email = interview.candidate.email if interview.candidate else None
    session_key = None
    interview_url = None
    
    # First, try to get session_key from Interview model
    if interview.session_key:
        session_key = interview.session_key
        print(f'✅ Session Key found: {session_key}')
    else:
        print('❌ No session key in interview model')
    
    # Generate URL using session_key
    if session_key:
        from interview_app.utils import get_interview_url
        interview_url = get_interview_url(session_key, request=None)
        print(f'✅ Generated interview URL: {interview_url}')
    else:
        print('❌ Cannot generate URL - no session key')
        
        # Try fallback methods
        try:
            interview_url = interview.get_interview_url()
            print(f'Fallback URL from get_interview_url(): {interview_url}')
        except Exception as e:
            print(f'Fallback failed: {e}')
            
        # Final fallback
        if not interview_url and interview.interview_link:
            interview_url = interview.interview_link
            print(f'Using interview_link: {interview_url}')
            
        if not interview_url:
            from django.conf import settings
            base_url = getattr(settings, "BACKEND_URL", "http://localhost:8000")
            interview_url = f"{base_url}/interview_app/?interview_id={interview.id}"
            print(f'Last resort URL: {interview_url}')
    
    # Test email function with debug
    print(f'\n📧 Testing email function...')
    print(f'Interview URL that will be in email: {interview_url}')
    
    try:
        result = NotificationService.send_candidate_interview_scheduled_notification(interview)
        print(f'Email result: {result}')
    except Exception as e:
        print(f'Email error: {e}')
        import traceback
        traceback.print_exc()
else:
    print('No interviews found')
