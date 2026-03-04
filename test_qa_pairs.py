#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.models import InterviewSession, InterviewQuestion, QAConversationPair
from interview_app.qa_conversation_service import get_qa_pairs_for_session_ordered

# Get the most recent session with Q&A pairs
sessions = InterviewSession.objects.all().order_by('-created_at')[:3]

print("=== Enhanced QA Conversation Pairs Analysis ===\n")

for session in sessions:
    print(f"Session: {session.session_key}")
    print(f"Created: {session.created_at}")
    print(f"Candidate: {session.candidate_name}")
    
    # Get all questions for this session
    questions = InterviewQuestion.objects.filter(session=session).order_by('conversation_sequence')
    print(f"\n📋 Total InterviewQuestions: {questions.count()}")
    
    # Get Q&A pairs using the new ordered function
    qa_data = get_qa_pairs_for_session_ordered(session.session_key)
    chronological_pairs = qa_data['chronological_pairs']
    ai_questions = qa_data['ai_questions']
    candidate_questions = qa_data['candidate_questions']
    
    print(f"💬 Total QAConversationPairs: {chronological_pairs.count()}")
    print(f"🤖 AI Questions: {ai_questions.count()}")
    print(f"🗣️ Candidate Questions: {candidate_questions.count()}")
    
    if chronological_pairs.exists():
        print("\n📝 Actual Interview Sequence (Chronological Order):")
        for i, qa in enumerate(chronological_pairs, 1):
            print(f"\n{i}. Question #{qa.question_number} ({qa.question_type})")
            print(f"   🆔 Session Key: {qa.session_key}")
            if qa.question_type == 'CANDIDATE_QUESTION':
                print(f"   🗣️ Candidate Question: {qa.answer_text[:100]}...")
                print(f"   🤖 AI Response: {qa.question_text[:100]}...")
            else:
                print(f"   🤖 AI Question: {qa.question_text[:100]}...")
                print(f"   🗣️ Candidate Answer: {qa.answer_text[:100]}...")
            print(f"   Time: {qa.response_time_seconds}s" if qa.response_time_seconds else "   Time: N/A")
            print(f"   WPM: {qa.words_per_minute}" if qa.words_per_minute else "   WPM: N/A")
    
    # Show separated questions
    if ai_questions.exists():
        print(f"\n🤖 AI Questions (Main Sequence):")
        for i, qa in enumerate(ai_questions, 1):
            print(f"   {i}. Q#{qa.question_number}: {qa.question_text[:60]}...")
    
    if candidate_questions.exists():
        print(f"\n🗣️ Candidate Questions (Separate Sequence):")
        for i, qa in enumerate(candidate_questions, 1):
            print(f"   {i}. Q#{qa.question_number}: {qa.answer_text[:60]}...")
    
    # Check for potential issues
    print("\n🔍 Analysis:")
    
    # Check candidate questions specifically
    if candidate_questions.exists():
        print(f"🗣️ Candidate Questions: {candidate_questions.count()}")
        for cq in candidate_questions:
            print(f"   - AI: {cq.question_text[:50]}...")
            print(f"   - Candidate: {cq.answer_text[:50]}...")
    else:
        print("🗣️ No candidate questions found")
    
    # Check if questions are being repeated
    question_texts = [q.question_text for q in chronological_pairs]
    unique_questions = set(question_texts)
    if len(question_texts) != len(unique_questions):
        print("⚠️  WARNING: Duplicate questions found in Q&A pairs!")
        for q in unique_questions:
            count = question_texts.count(q)
            if count > 1:
                print(f"   - '{q[:50]}...' appears {count} times")
    else:
        print("✅ No duplicate questions in Q&A pairs")
    
    # Compare with InterviewQuestions
    ai_questions_db = questions.filter(role='AI', question_level__in=['MAIN', 'FOLLOW_UP', 'CLARIFICATION', 'INTRODUCTORY'])
    print(f"📊 AI Questions in InterviewQuestions: {ai_questions_db.count()}")
    print(f"📊 Q&A Pairs saved: {chronological_pairs.count()}")
    
    if ai_questions_db.count() != ai_questions.count():
        print("⚠️  Mismatch between AI questions and Q&A pairs!")
        print("   This might indicate missing Q&A pairs or duplicate saving")
    else:
        print("✅ Good match between AI questions and Q&A pairs")
    
    # Check sequencing
    print(f"\n🔢 Sequencing Analysis:")
    print(f"   Total questions in sequence: 1 to {chronological_pairs.last().question_number if chronological_pairs.exists() else 'N/A'}")
    print(f"   AI Questions in sequence: {[q.question_number for q in ai_questions]}")
    print(f"   Candidate Questions in sequence: {[q.question_number for q in candidate_questions]}")
    
    print("\n" + "="*60 + "\n")

print("🎯 Recommendations:")
print("1. All questions now use sequential numbering (1, 2, 3, 4, 5, 6...)")
print("2. Question types are identified by the 'question_type' field")
print("3. Chronological order is maintained by 'question_number'")
print("4. Candidate questions are properly integrated into the main sequence")
print("5. Check console logs during interviews to see the Q&A saving process")
