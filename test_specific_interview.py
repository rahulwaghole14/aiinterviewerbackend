#!/usr/bin/env python
"""
Test the specific interview that's causing the error
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interviews.serializers import InterviewSerializer
from interviews.models import Interview

def test_specific_interview():
    """Test the specific interview ID from the error"""
    
    interview_id = "6e291523-bce5-487d-ab22-7f938e71ac6d"
    
    print(f"=== Testing Specific Interview ID: {interview_id} ===\n")
    
    try:
        interview = Interview.objects.get(id=interview_id)
        print(f"✅ Found interview: {interview.candidate_id}")
        
        # Test the serializer
        serializer = InterviewSerializer(interview)
        qa_data = serializer.get_questions_and_answers(interview)
        
        print(f"✅ Successfully retrieved Q&A data")
        print(f"📊 Total Q&A items: {len(qa_data)}")
        
        # Show question types
        qa_types = list(set(item.get('question_type', 'N/A') for item in qa_data))
        print(f"📋 Question types: {qa_types}")
        
        # Show all items
        for i, item in enumerate(qa_data):
            print(f"   Q{i+1}: {item.get('question_type', 'N/A')} - {item.get('question_text', '')[:50]}...")
        
    except Interview.DoesNotExist:
        print(f"❌ Interview not found")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_interview()
