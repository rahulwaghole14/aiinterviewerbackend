#!/usr/bin/env python3
"""
Trigger AI evaluation for all completed interview sessions that don't have evaluations
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from ai_platform.interview_app.models import InterviewSession

def trigger_evaluation_for_completed_sessions():
    """Trigger AI evaluation for all completed sessions without evaluations"""
    
    # Find all completed sessions that haven't been evaluated
    completed_sessions = InterviewSession.objects.filter(
        status='COMPLETED',
        is_evaluated=False
    )
    
    print(f"Found {completed_sessions.count()} completed sessions without evaluations")
    
    for session in completed_sessions:
        print(f"\n{'='*60}")
        print(f"Processing session: {session.id}")
        print(f"Candidate: {session.candidate_name}")
        print(f"Created: {session.created_at}")
        print(f"Status: {session.status}")
        print(f"Is evaluated: {session.is_evaluated}")
        
        # Check if session has content to evaluate
        has_spoken_answers = session.questions.filter(transcribed_answer__isnull=False, transcribed_answer__gt='').exists()
        has_code_submissions = session.code_submissions.exists()
        
        print(f"Has spoken answers: {has_spoken_answers}")
        print(f"Has code submissions: {has_code_submissions}")
        
        if has_spoken_answers or has_code_submissions:
            print("Triggering AI evaluation...")
            try:
                # Import the trigger function
                from ai_platform.interview_app.views import trigger_ai_evaluation
                trigger_ai_evaluation(session)
                print("✅ Evaluation completed successfully")
            except Exception as e:
                print(f"❌ Error during evaluation: {e}")
        else:
            print("⚠️  No content to evaluate - skipping")
    
    print(f"\n{'='*60}")
    print("Evaluation trigger process completed!")

if __name__ == "__main__":
    try:
        trigger_evaluation_for_completed_sessions()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()



