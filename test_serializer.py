#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interviews.models import Interview
from interviews.serializers import InterviewSerializer

# Get the interview with screen recording
interview = Interview.objects.get(id='d8c4d36c-461e-42fe-be4a-4d432daf2972')
print(f'Interview ID: {interview.id}')
print(f'Session Key: {interview.session_key}')
print(f'Screen recording file: {interview.screen_recording_file}')
print(f'Screen recording URL: {interview.screen_recording_url}')

# Test serializer
serializer = InterviewSerializer(interview)
data = serializer.data
print(f'\nSerializer data:')
print(f'screen_recording_file: {data.get("screen_recording_file")}')
print(f'screen_recording_url: {data.get("screen_recording_url")}')
print(f'screen_recording_duration: {data.get("screen_recording_duration")}')
