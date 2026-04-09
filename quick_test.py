#!/usr/bin/env python3
import os
import sys
import django

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.voice_analysis_service import VoiceAnalysisService

# Test the problematic session
session_key = 'aa1b4a5f007545ca882055115e92bd27'
audio_path = 'media/interview_audio/aa1b4a5f007545ca882055115e92bd27_interview_audio_converted.wav'

print(f'Testing session: {session_key}')
print(f'Audio file: {audio_path}')
print(f'File exists: {os.path.exists(audio_path)}')

if os.path.exists(audio_path):
    voice_service = VoiceAnalysisService()
    print('Running voice analysis...')
    result = voice_service.analyze_complete_interview_audio(audio_path, session_key)
    if result and result.get('success'):
        diarization = result.get('diarization')
        print(f'NEW RESULT - Speakers: {diarization.get("num_speakers")}')
        print(f'Candidate: {diarization.get("candidate_speech_percentage")}%')
        print(f'Interviewer: {diarization.get("interviewer_speech_percentage")}%')
    else:
        print(f'Analysis failed: {result.get("error")}')
else:
    print('Audio file not found')
