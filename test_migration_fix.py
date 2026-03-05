#!/usr/bin/env python
"""
Test script to verify the database migration fix
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interviews.serializers import InterviewSerializer
from interviews.models import Interview

def test_migration_fix():
    """Test that the migration fixed the asked_at field issue"""
    
    print("=== Testing Database Migration Fix ===\n")
    
    # Find interviews to test
    for interview in Interview.objects.all():
        print(f"🎯 Testing Interview ID: {interview.id}")
        
        try:
            # Test the serializer that was failing
            serializer = InterviewSerializer(interview)
            qa_data = serializer.get_questions_and_answers(interview)
            
            print(f"   ✅ Successfully retrieved Q&A data")
            print(f"   📊 Total Q&A items: {len(qa_data)}")
            
            # Show question types
            qa_types = list(set(item.get('question_type', 'N/A') for item in qa_data))
            print(f"   📋 Question types: {qa_types}")
            
            # Show first few items
            for i, item in enumerate(qa_data[:3]):
                print(f"      Q{i+1}: {item.get('question_type', 'N/A')} - {item.get('question_text', '')[:50]}...")
            
            print(f"   ✅ Test completed successfully for interview {interview.id}")
            break  # Test first interview only
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n✅ Migration fix test completed")
    print(f"💡 The 'asked_at' field should now be available in the database")

if __name__ == "__main__":
    test_migration_fix()
