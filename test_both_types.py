#!/usr/bin/env python
"""
Test both regular Q&A and coding questions together
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interviews.serializers import InterviewSerializer
from interviews.models import Interview
from interview_app.models import InterviewSession, InterviewQuestion, QAConversationPair

# Find an interview with both regular Q&A and coding questions
for interview in Interview.objects.all():
    if interview.session_key:
        try:
            session = InterviewSession.objects.get(session_key=interview.session_key)
            
            # Check for both regular Q&A and coding questions
            regular_count = QAConversationPair.objects.filter(
                session=session
            ).exclude(question_type='CODING').count()
            
            coding_count = InterviewQuestion.objects.filter(
                session=session, 
                question_type='CODING'
            ).count()
            
            if regular_count > 0 and coding_count > 0:
                print(f'Found interview with both types: {interview.id}')
                print(f'Regular Q&A: {regular_count}, Coding: {coding_count}')
                
                # Test the serializer
                serializer = InterviewSerializer(interview)
                qa_data = serializer.get_questions_and_answers(interview)
                
                print(f'Total items returned: {len(qa_data)}')
                for qa in qa_data:
                    q_type = qa['question_type']
                    q_num = qa['question_number']
                    q_text = qa['question_text'][:40]
                    print(f'  Q#{q_num} ({q_type}): {q_text}...')
                break
        except Exception as e:
            print(f'Error: {e}')
            continue

print('Test completed')
