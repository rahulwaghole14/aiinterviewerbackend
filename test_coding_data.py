#!/usr/bin/env python
"""
Find coding questions with actual transcribed_answer data
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.models import InterviewQuestion, InterviewSession

# Find coding questions with actual transcribed_answer data
coding_questions = InterviewQuestion.objects.filter(
    question_type='CODING'
).exclude(transcribed_answer__isnull=True).exclude(transcribed_answer='')

print(f'Found {coding_questions.count()} coding questions with transcribed_answer data')

for q in coding_questions[:3]:
    print(f'\nQuestion ID: {q.id}')
    print(f'Session: {q.session.session_key if q.session else "None"}')
    print(f'Order: {q.order}')
    print(f'Question: {q.question_text[:60]}...')
    print(f'Transcribed: {q.transcribed_answer[:100] if q.transcribed_answer else "None"}...')

# Also test one with the interview serializer
if coding_questions.exists():
    q = coding_questions.first()
    if q.session:
        from interviews.models import Interview
        from interviews.serializers import InterviewSerializer
        
        interview = Interview.objects.filter(session_key=q.session.session_key).first()
        if interview:
            print(f'\n🔍 Testing with Interview ID: {interview.id}')
            serializer = InterviewSerializer(interview)
            qa_data = serializer.get_questions_and_answers(interview)
            
            coding_items = [qa for qa in qa_data if qa['question_type'] == 'CODING']
            for qa in coding_items:
                print(f'   Answer: {qa["answer_text"][:100]}...')

print('Test completed')
