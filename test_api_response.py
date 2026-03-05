#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interviews.models import Interview
from interviews.serializers import InterviewSerializer
from django.test import RequestFactory

# Create a mock request
factory = RequestFactory()
request = factory.get('/api/interviews/test/')

# Get the interview with screen recording
interview = Interview.objects.get(id='d8c4d36c-461e-42fe-be4a-4d432daf2972')

# Test with request context (should return absolute URLs)
serializer = InterviewSerializer(interview, context={'request': request})
data = serializer.data

print('=== API Response Data ===')
print(f'screen_recording_file: {data.get("screen_recording_file")}')
print(f'screen_recording_url: {data.get("screen_recording_url")}')
print(f'screen_recording_duration: {data.get("screen_recording_duration")}')

# Test what the frontend would construct
base_url = 'http://localhost:8000'
screen_file = data.get('screen_recording_file')
screen_url = data.get('screen_recording_url')

print('\n=== Frontend URL Construction ===')
if screen_url:
    if screen_url.startswith('http'):
        final_url = screen_url
    else:
        final_url = f'{base_url}{screen_url}'
    print(f'Final URL from screen_recording_url: {final_url}')

if screen_file:
    if screen_file.startswith('http'):
        final_url = screen_file
    else:
        final_url = f'{base_url}{screen_file}'
    print(f'Final URL from screen_recording_file: {final_url}')
