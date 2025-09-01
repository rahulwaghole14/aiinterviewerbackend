#!/usr/bin/env python3
"""
Trigger evaluation for Dhananjay Paturkar Pune's interview
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
from ai_platform.interview_app.views import trigger_ai_evaluation
from django.utils import timezone

def trigger_dhananjay_evaluation():
    """Trigger evaluation for Dhananjay's interview"""
    
    print("🔧 TRIGGERING EVALUATION FOR DHANANJAY PATURKAR PUNE")
    print("=" * 60)
    
    # Find Dhananjay's interview session
    session = InterviewSession.objects.filter(
        candidate_name__icontains="dhananjay"
    ).order_by('-created_at').first()
    
    if not session:
        print("❌ No interview session found for Dhananjay")
        return
    
    print(f"📋 INTERVIEW SESSION FOUND:")
    print(f"   ID: {session.id}")
    print(f"   Candidate: {session.candidate_name}")
    print(f"   Status: {session.status}")
    print(f"   Is Evaluated: {session.is_evaluated}")
    
    # Check if session is completed
    if session.status != 'COMPLETED':
        print(f"\n❌ SESSION NOT COMPLETED:")
        print(f"   Cannot trigger evaluation for incomplete session")
        return
    
    # Check if already evaluated
    if session.is_evaluated:
        print(f"\n⚠️  SESSION ALREADY EVALUATED:")
        print(f"   Evaluation has already been performed")
        return
    
    # Check if there's data to evaluate
    questions = session.questions.all()
    answered_questions = questions.filter(transcribed_answer__isnull=False).exclude(transcribed_answer='')
    code_submissions = session.code_submissions.all()
    
    print(f"\n📊 DATA AVAILABLE FOR EVALUATION:")
    print(f"   Questions with answers: {answered_questions.count()}")
    print(f"   Code submissions: {code_submissions.count()}")
    
    if answered_questions.count() == 0 and code_submissions.count() == 0:
        print(f"\n❌ NO DATA TO EVALUATE:")
        print(f"   No spoken answers or code submissions found")
        print(f"   Cannot perform evaluation without data")
        return
    
    print(f"\n🚀 TRIGGERING AI EVALUATION...")
    
    try:
        # Trigger the evaluation
        trigger_ai_evaluation(session)
        
        # Refresh the session from database
        session.refresh_from_db()
        
        print(f"\n✅ EVALUATION COMPLETED!")
        print(f"   Is Evaluated: {session.is_evaluated}")
        print(f"   Resume Score: {session.resume_score}")
        print(f"   Answers Score: {session.answers_score}")
        print(f"   Overall Score: {session.overall_performance_score}")
        print(f"   Resume Feedback: {'Present' if session.resume_feedback else 'Missing'}")
        print(f"   Answers Feedback: {'Present' if session.answers_feedback else 'Missing'}")
        print(f"   Overall Feedback: {'Present' if session.overall_performance_feedback else 'Missing'}")
        
        if session.is_evaluated:
            print(f"\n🎉 SUCCESS! Evaluation is now complete.")
            print(f"   The frontend should now show the evaluation results.")
        else:
            print(f"\n⚠️  EVALUATION MAY HAVE FAILED:")
            print(f"   is_evaluated flag is still False")
            print(f"   Check the logs for any errors")
        
    except Exception as e:
        print(f"\n❌ EVALUATION FAILED:")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    return session

if __name__ == "__main__":
    try:
        session = trigger_dhananjay_evaluation()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()




