#!/usr/bin/env python
"""
Test script for the new simplified Q&A system
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.models import InterviewSession, InterviewQA
from django.utils import timezone

def test_qa_system():
    """Test the new simplified Q&A system"""
    print("🧪 Testing Simplified Q&A System")
    
    # Create a test session
    session = InterviewSession.objects.create(
        candidate_name="Test Candidate",
        job_description="Test job description for Python developer position",
        status='SCHEDULED'
    )
    
    print(f"✅ Created test session: {session.session_key}")
    
    # Create some test Q&A pairs
    test_data = [
        {
            'question_number': 1,
            'question_text': 'What is your experience with Python?',
            'answer_text': 'I have 5 years of experience with Python development.',
            'question_type': 'TECHNICAL'
        },
        {
            'question_number': 2,
            'question_text': 'Can you explain Django ORM?',
            'answer_text': 'Django ORM is a high-level abstraction over SQL that provides database access.',
            'question_type': 'TECHNICAL'
        },
        {
            'question_number': 3,
            'question_text': 'How do you handle database migrations?',
            'answer_text': 'I use Django migrations to manage database schema changes over time.',
            'question_type': 'TECHNICAL'
        }
    ]
    
    # Create Q&A pairs
    for data in test_data:
        qa_pair = InterviewQA.objects.create(
            session=session,
            question_number=data['question_number'],
            question_text=data['question_text'],
            answer_text=data['answer_text'],
            question_type=data['question_type'],
            asked_at=timezone.now(),
            answered_at=timezone.now()
        )
        print(f"✅ Created Q&A pair {data['question_number']}")
    
    # Retrieve and display all Q&A pairs
    qa_pairs = InterviewQA.objects.filter(session=session).order_by('question_number')
    
    print(f"\n📊 Retrieved Q&A Pairs:")
    for qa in qa_pairs:
        print(f"   Q{qa.question_number}: {qa.question_text[:50]}...")
        print(f"   A{qa.question_number}: {qa.answer_text[:50]}...")
        print(f"   Type: {qa.question_type}")
        print(f"   Asked: {qa.asked_at}")
        print(f"   Answered: {qa.answered_at}")
        print(f"   Response Time: {qa.response_time_seconds}s")
        print(f"   Words/Min: {qa.words_per_minute}")
        print()
    
    print(f"\n🎉 Test completed successfully!")
    print(f"   Total Q&A pairs: {qa_pairs.count()}")
    print(f"   Session Key: {session.session_key}")
    
    return session

if __name__ == '__main__':
    test_qa_system()
