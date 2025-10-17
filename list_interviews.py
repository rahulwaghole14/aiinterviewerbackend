#!/usr/bin/env python
"""
List all previous interviews and generate PDF download links
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.models import InterviewSession
from django.utils import timezone

def list_interviews():
    """List all interview sessions with PDF links"""
    sessions = InterviewSession.objects.all().order_by('-created_at')
    
    if not sessions:
        print("\n" + "="*70)
        print("NO INTERVIEWS FOUND")
        print("="*70)
        return
    
    print("\n" + "="*70)
    print(f"FOUND {sessions.count()} INTERVIEW SESSION(S)")
    print("="*70)
    
    for i, session in enumerate(sessions, 1):
        print(f"\n{i}. Interview Session")
        print("-" * 70)
        print(f"   Session ID: {session.id}")
        print(f"   Candidate: {session.candidate_name}")
        print(f"   Email: {session.candidate_email or 'N/A'}")
        print(f"   Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Status: {session.status}")
        print(f"   Evaluated: {'Yes' if session.is_evaluated else 'No'}")
        
        if session.answers_score:
            print(f"   Answers Score: {session.answers_score:.1f}%")
        if session.resume_score:
            print(f"   Resume Score: {session.resume_score:.1f}%")
        
        # PDF Download Link
        pdf_url = f"http://127.0.0.1:8000/ai/transcript_pdf?session_id={session.id}"
        print(f"\n   📄 PDF Download Link:")
        print(f"   {pdf_url}")
        
        # Interview Portal Link (if not expired)
        if session.status == 'SCHEDULED':
            portal_url = f"http://127.0.0.1:8000/?session_key={session.session_key}"
            print(f"\n   🔗 Interview Portal Link:")
            print(f"   {portal_url}")
    
    print("\n" + "="*70)
    print("To download a PDF, copy the link and open it in your browser")
    print("="*70 + "\n")

if __name__ == '__main__':
    list_interviews()

