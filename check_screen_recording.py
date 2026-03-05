#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interviews.models import Interview
from interview_app.models import InterviewSession

# Check Interview model for the session with screen recording
session_key = '0b236cb2f26a4df0b3f45852aad3eff7'
interview = Interview.objects.filter(session_key=session_key).first()
if interview:
    print(f'Interview found: {interview.id}')
    print(f'Screen recording URL: {interview.screen_recording_url}')
    print(f'Screen recording file: {interview.screen_recording_file}')
else:
    print('No Interview record found for this session')
    
# Check all interviews
print(f'\nTotal interviews: {Interview.objects.count()}')
for i in Interview.objects.all()[:5]:
    print(f'Interview: {i.id} - Session: {i.session_key} - Screen URL: {i.screen_recording_url or "None"}')

# Also check if we need to create Interview records for sessions with screen recordings
print('\nSessions with screen recordings but no Interview record:')
sessions_with_recording = InterviewSession.objects.filter(screen_recording__isnull=False)
for session in sessions_with_recording:
    interview = Interview.objects.filter(session_key=session.session_key).first()
    if not interview:
        print(f'Session {session.session_key} has screen recording but no Interview record')
