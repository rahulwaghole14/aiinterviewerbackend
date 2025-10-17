#!/usr/bin/env python
"""Check if coding questions exist for a session"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.models import InterviewSession, InterviewQuestion, TestCase
import sys

session_key = sys.argv[1] if len(sys.argv) > 1 else "4f88a4423efb420aad6e99d91ce43ee3"

try:
    session = InterviewSession.objects.get(session_key=session_key)
    print(f"\n{'='*70}")
    print(f"Session: {session.candidate_name}")
    print(f"Session Key: {session_key}")
    print(f"{'='*70}\n")
    
    # Get all questions
    all_q = session.questions.all().order_by('order')
    print(f"Total questions: {all_q.count()}")
    
    # Get coding questions specifically
    coding_q = session.questions.filter(question_type='CODING').order_by('order')
    print(f"Coding questions: {coding_q.count()}\n")
    
    if coding_q.exists():
        print("CODING QUESTIONS IN DATABASE:")
        print("-" * 70)
        for idx, q in enumerate(coding_q, 1):
            print(f"\n{idx}. {q.question_text[:100]}...")
            print(f"   Language: {q.coding_language}")
            print(f"   Order: {q.order}")
            print(f"   ID: {q.id}")
            
            # Get test cases
            test_cases = q.test_cases.all()
            print(f"   Test cases: {test_cases.count()}")
            for tc_idx, tc in enumerate(test_cases[:3], 1):
                print(f"      TC{tc_idx}: {tc.input_data[:40]} → {tc.expected_output[:40]}")
    else:
        print("❌ NO CODING QUESTIONS FOUND!")
        print(f"\nRun: python generate_coding_questions.py {session_key} 2")
    
    print(f"\n{'='*70}\n")
    
except InterviewSession.DoesNotExist:
    print(f"❌ Session not found: {session_key}")

