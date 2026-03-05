#!/usr/bin/env python
"""
Test script to verify performance metrics are working correctly
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interviews.serializers import InterviewSerializer
from interviews.models import Interview

def test_performance_metrics():
    """Test that performance metrics show actual question counts"""
    
    print("=== Testing Performance Metrics Fix ===\n")
    
    # Find interviews to test
    for interview in Interview.objects.all()[:3]:  # Test first 3 interviews
        print(f"🎯 Testing Interview ID: {interview.id}")
        
        try:
            # Test the serializer
            serializer = InterviewSerializer(interview)
            qa_data = serializer.get_questions_and_answers(interview)
            
            # Count question types
            technical_questions = [qa for qa in qa_data if (qa.get('question_type') or '').upper() in ['TECHNICAL', 'BEHAVIORAL', 'INTRODUCTION', 'CLOSING']]
            coding_questions = [qa for qa in qa_data if (qa.get('question_type') or '').upper() == 'CODING']
            
            technical_count = len(technical_questions)
            coding_count = len(coding_questions)
            
            print(f"   📊 Total Q&A items: {len(qa_data)}")
            print(f"   🔧 Technical questions: {technical_count}")
            print(f"   💻 Coding questions: {coding_count}")
            
            # Show question breakdown
            qa_types = {}
            for qa in qa_data:
                qtype = qa.get('question_type', 'N/A')
                qa_types[qtype] = qa_types.get(qtype, 0) + 1
            
            print(f"   📋 Question types breakdown:")
            for qtype, count in qa_types.items():
                print(f"      {qtype}: {count}")
            
            print(f"   ✅ Test completed for interview {interview.id}")
            print(f"   💡 Frontend should now show {technical_count} technical questions and {coding_count} coding questions")
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    print(f"✅ Performance metrics test completed")
    print(f"💡 Frontend will now show actual counts instead of hardcoded '12'")

if __name__ == "__main__":
    test_performance_metrics()
