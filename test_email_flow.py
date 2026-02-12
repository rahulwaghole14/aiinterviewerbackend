from interviews.models import Interview
from notifications.services import NotificationService

print('🔍 Testing Email Sending with New Interview')
print('=' * 50)

# Create a test interview to check the full flow
from candidates.models import Candidate
from jobs.models import Job
from companies.models import Company

# Get test data
company = Company.objects.first()
candidate = Candidate.objects.first()
job = Job.objects.first()

if all([company, candidate, job]):
    print(f'Test Data:')
    print(f'  Candidate: {candidate.email}')
    print(f'  Job: {job.job_title}')
    print(f'  Company: {company.name}')
    
    # Create interview like the API does
    print(f'\n🧪 Creating interview...')
    interview = Interview.objects.create(
        candidate=candidate,
        job=job,
        status='scheduled'  # Set status to scheduled
    )
    
    print(f'Created interview {interview.id} with status "{interview.status}"')
    print(f'Session key before generate_interview_link(): {interview.session_key}')
    
    # Generate session key (like our fix)
    print(f'\n🔗 Generating session key...')
    try:
        interview.generate_interview_link()
        print(f'✅ Session key generated: {interview.session_key}')
        print(f'✅ Interview link: {interview.interview_link}')
    except Exception as e:
        print(f'❌ Session key generation failed: {e}')
        import traceback
        traceback.print_exc()
    
    # Refresh to get latest data
    interview.refresh_from_db()
    print(f'After refresh - Session key: {interview.session_key}')
    
    # Test email sending
    print(f'\n📧 Testing email sending...')
    try:
        result = NotificationService.send_candidate_interview_scheduled_notification(interview)
        print(f'Email result: {result}')
        
        if result:
            print('✅ Email sent successfully!')
        else:
            print('❌ Email returned False')
            
    except Exception as e:
        print(f'❌ Email sending failed: {e}')
        import traceback
        traceback.print_exc()
    
    # Clean up
    interview.delete()
    print(f'\n🧹 Test interview deleted')
    
else:
    print('❌ Missing test data (company, candidate, or job)')
