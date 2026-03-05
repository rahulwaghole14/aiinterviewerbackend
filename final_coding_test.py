#!/usr/bin/env python
"""
Final test to verify coding question answers are working correctly
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interviews.models import Interview
from interviews.serializers import InterviewSerializer

def final_coding_test():
    """Final test to verify coding question answers are working"""
    
    print("=== Final Test: Coding Question Answers ===\n")
    
    # Test interviews that have coding questions with actual code
    interview_ids = [
        "e53c9c0e-c9ae-4a9f-9da4-c8aa8a797f04",  # Has coding question with code
        "6e291523-bce5-487d-ab22-7f938e71ac6d",  # Has coding question with code
    ]
    
    for interview_id in interview_ids:
        print(f"🎯 Testing Interview ID: {interview_id}")
        
        try:
            interview = Interview.objects.get(id=interview_id)
            serializer = InterviewSerializer(interview)
            qa_data = serializer.get_questions_and_answers(interview)
            
            coding_questions = [qa for qa in qa_data if qa.get('question_type') == 'CODING']
            
            if coding_questions:
                print(f"   💻 Found {len(coding_questions)} coding question(s)")
                
                for i, qa in enumerate(coding_questions):
                    answer = qa.get('answer_text', '')
                    print(f"   📝 Question {i+1}: {qa.get('question_text', '')[:60]}...")
                    
                    if answer and answer != 'No code submitted':
                        print(f"   ✅ Has Code: {len(answer)} characters")
                        print(f"   📄 Code Preview: {answer.strip()[:100]}...")
                        
                        # Check if it has CodeSubmission metadata
                        if qa.get('code_submission'):
                            cs = qa['code_submission']
                            print(f"   🔧 CodeSubmission: ID {cs.get('id')}, Language {cs.get('language')}, Passed {cs.get('passed_all_tests')}")
                    else:
                        print(f"   ❌ No Code: {answer}")
                        
                    print()
            else:
                print(f"   ⚠️ No coding questions found")
                
        except Interview.DoesNotExist:
            print(f"   ❌ Interview not found")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("-" * 60)
    
    print("✅ Final test completed!")
    print("💡 If you see 'Has Code' above, the coding answers are working correctly!")
    print("🎉 Frontend should now display the actual code submitted by candidates")

if __name__ == "__main__":
    final_coding_test()
