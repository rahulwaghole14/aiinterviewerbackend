#!/usr/bin/env python
"""
Test script for question-answer pair functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aiinterviewer.settings')
django.setup()

from interview_app.models import InterviewSession, InterviewQuestion
from django.utils import timezone
import uuid

def test_question_answer_functionality():
    print("🧪 Testing Question-Answer Pair Functionality")
    print("=" * 60)
    
    # Create a test session
    session, created = InterviewSession.objects.get_or_create(
        session_key="test_session_" + uuid.uuid4().hex[:8],
        defaults={
            'candidate_name': 'Test Candidate',
            'candidate_email': 'test@example.com',
            'job_description': 'Test job description',
            'resume_text': 'Test resume text',
            'status': 'SCHEDULED'
        }
    )
    
    if created:
        print(f"✅ Created test session: {session.id}")
    else:
        print(f"📋 Using existing session: {session.id}")
    
    # Test 1: Create introduction question-answer pair
    print("\n📝 Test 1: Creating Introduction Question-Answer Pair")
    intro_question = InterviewQuestion.objects.create(
        session=session,
        question_text="Hello! Can you please introduce yourself and tell me about your background?",
        transcribed_answer="Hi, I'm a software developer with 5 years of experience in Python and Django.",
        question_type='INTRODUCTION',
        question_level='INTRO',
        order=0,
        asked_at=timezone.now(),
        answered_at=timezone.now(),
        role='AI'
    )
    print(f"✅ Created: {intro_question}")
    
    # Test 2: Create technical question-answer pair
    print("\n💻 Test 2: Creating Technical Question-Answer Pair")
    tech_question = InterviewQuestion.objects.create(
        session=session,
        question_text="What is your experience with Django framework?",
        transcribed_answer="I have 3 years of experience building REST APIs with Django, including authentication, database models, and deployment.",
        question_type='TECHNICAL',
        question_level='MAIN',
        order=1,
        asked_at=timezone.now(),
        answered_at=timezone.now(),
        role='AI',
        question_category='frameworks'
    )
    print(f"✅ Created: {tech_question}")
    
    # Test 3: Create behavioral question-answer pair
    print("\n🤝 Test 3: Creating Behavioral Question-Answer Pair")
    behavioral_question = InterviewQuestion.objects.create(
        session=session,
        question_text="Tell me about a time when you had to work with a difficult team member.",
        transcribed_answer="I had a situation where a team member wasn't meeting deadlines. I scheduled a private meeting, understood their challenges, and we worked together to create a better timeline that helped them succeed while meeting project goals.",
        question_type='BEHAVIORAL',
        question_level='MAIN',
        order=2,
        asked_at=timezone.now(),
        answered_at=timezone.now(),
        role='AI',
        question_category='teamwork'
    )
    print(f"✅ Created: {behavioral_question}")
    
    # Test 4: Create coding question-answer pair
    print("\n💻 Test 4: Creating Coding Question-Answer Pair")
    coding_question = InterviewQuestion.objects.create(
        session=session,
        question_text="Write a function to find the factorial of a number using recursion.",
        transcribed_answer="def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
        question_type='CODING',
        question_level='MAIN',
        order=3,
        asked_at=timezone.now(),
        answered_at=timezone.now(),
        role='AI',
        coding_language='PYTHON'
    )
    print(f"✅ Created: {coding_question}")
    
    # Test 5: Create pre-closing question-answer pair
    print("\n🔚 Test 5: Creating Pre-closing Question-Answer Pair")
    pre_closing_question = InterviewQuestion.objects.create(
        session=session,
        question_text="Is there anything else about your experience that you'd like to highlight?",
        transcribed_answer="I'm also experienced with cloud technologies like AWS and have led a team of 3 developers.",
        question_type='PRECLOSING',
        question_level='PRECLOSE',
        order=4,
        asked_at=timezone.now(),
        answered_at=timezone.now(),
        role='AI'
    )
    print(f"✅ Created: {pre_closing_question}")
    
    # Test 6: Create closing question-answer pair
    print("\n👋 Test 6: Creating Closing Question-Answer Pair")
    closing_question = InterviewQuestion.objects.create(
        session=session,
        question_text="Do you have any questions for us about the role or company?",
        transcribed_answer="No, I don't have any questions. Thank you for the opportunity!",
        question_type='CLOSING',
        question_level='CLOSE',
        order=5,
        asked_at=timezone.now(),
        answered_at=timezone.now(),
        role='AI'
    )
    print(f"✅ Created: {closing_question}")
    
    # Test 7: Verify all questions are saved
    print("\n📊 Test 7: Verifying All Questions Saved")
    all_questions = InterviewQuestion.objects.filter(session=session).order_by('order')
    
    print(f"Total questions saved: {all_questions.count()}")
    
    question_types = {}
    for question in all_questions:
        qtype = question.question_type
        question_types[qtype] = question_types.get(qtype, 0) + 1
        print(f"  Q{question.order + 1}: {question.question_type} - {question.question_text[:50]}...")
        print(f"    Answer: {question.transcribed_answer[:50] if question.transcribed_answer else 'No answer'}...")
    
    print(f"\n📈 Question Type Summary:")
    for qtype, count in question_types.items():
        print(f"  {qtype}: {count}")
    
    # Test 8: Test conversation sequence
    print("\n🔄 Test 8: Testing Conversation Sequence")
    for question in all_questions:
        print(f"  Sequence {question.conversation_sequence}: {question.role} - {question.question_type}")
    
    # Test 9: Test performance metrics
    print("\n📊 Test 9: Testing Performance Metrics")
    
    # Add some performance metrics
    tech_question.response_time_seconds = 45.5
    tech_question.words_per_minute = 120
    tech_question.filler_word_count = 3
    tech_question.save()
    
    behavioral_question.response_time_seconds = 67.2
    behavioral_question.words_per_minute = 98
    behavioral_question.filler_word_count = 7
    behavioral_question.save()
    
    print(f"✅ Updated performance metrics for technical and behavioral questions")
    
    # Test 10: Test query by question type
    print("\n🔍 Test 10: Testing Queries by Question Type")
    
    technical_questions = InterviewQuestion.objects.filter(session=session, question_type='TECHNICAL')
    behavioral_questions = InterviewQuestion.objects.filter(session=session, question_type='BEHAVIORAL')
    coding_questions = InterviewQuestion.objects.filter(session=session, question_type='CODING')
    
    print(f"Technical questions: {technical_questions.count()}")
    print(f"Behavioral questions: {behavioral_questions.count()}")
    print(f"Coding questions: {coding_questions.count()}")
    
    print("\n🎉 All tests completed successfully!")
    print(f"Session ID: {session.id}")
    print(f"Total Questions: {all_questions.count()}")
    print(f"Question Types: {list(question_types.keys())}")
    
    return session

if __name__ == "__main__":
    test_question_answer_functionality()
