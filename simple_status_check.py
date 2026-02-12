from interviews.models import Interview

print('Checking interview statuses...')
interviews = Interview.objects.all().order_by('-created_at')[:5]
for interview in interviews:
    should_send = interview.status in ["scheduled", "confirmed"]
    print(f'ID: {interview.id}, Status: {interview.status}, Should send email: {should_send}')
