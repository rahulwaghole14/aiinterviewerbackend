#!/usr/bin/env python
"""
Test script to verify that the InterviewSerializer is using QAConversationPair table
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interviews.serializers import InterviewSerializer
from interview_app.models import Interview, InterviewSession, QAConversationPair

def test_serializer_qa_data():
    """Test that serializer returns Q&A data from QAConversationPair table"""
    
    print("=== Testing InterviewSerializer Q&A Data ===\n")
    
    # Get interviews with Q&A pairs
    interviews = Interview.objects.all().order_by('-created_at')[:3]
    
    for interview in interviews:
        print(f"Interview ID: {interview.id}")
        print(f"Candidate: {interview.candidate.full_name if interview.candidate else 'N/A'}")
        print(f"Session Key: {interview.session_key}")
        print(f"Status: {interview.status}")
        
        # Test the serializer
        serializer = InterviewSerializer(interview)
        qa_data = serializer.get_questions_and_answers(interview)
        
        print(f"\n📊 Q&A Data from Serializer:")
        print(f"   Total Q&A pairs: {len(qa_data)}")
        
        if qa_data:
            print(f"\n📝 Q&A Pair Details:")
            for i, qa in enumerate(qa_data[:5], 1):  # Show first 5
                print(f"   {i}. Q#{qa['question_number']} ({qa['question_type']})")
                if qa.get('is_candidate_question'):
                    print(f"      🗣️ Candidate Question: {qa['answer_text'][:50]}...")
                    print(f"      🤖 AI Response: {qa['question_text'][:50]}...")
                else:
                    print(f"      🤖 AI Question: {qa['question_text'][:50]}...")
                    print(f"      🗣️ Candidate Answer: {qa['answer_text'][:50]}...")
                print(f"      ⏱️ Response Time: {qa.get('response_time', 'N/A')}s")
                print(f"      📝 WPM: {qa.get('words_per_minute', 'N/A')}")
        
        # Verify data is coming from QAConversationPair table
        if interview.session_key:
            try:
                session = InterviewSession.objects.get(session_key=interview.session_key)
                qa_pairs = QAConversationPair.objects.filter(session=session)
                print(f"\n🔍 Verification:")
                print(f"   QAConversationPair records: {qa_pairs.count()}")
                print(f"   Serializer returned: {len(qa_data)}")
                
                if qa_pairs.count() == len(qa_data):
                    print("   ✅ Data matches QAConversationPair table!")
                else:
                    print("   ⚠️ Mismatch between table and serializer data")
                    
            except InterviewSession.DoesNotExist:
                print(f"\n⚠️ No session found for session_key: {interview.session_key}")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    test_serializer_qa_data()
