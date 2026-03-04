import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
django.setup()

from interview_app.models import InterviewSession, TechnicalInterviewQA
# Import the update function we just created
from interview_app.qa_service import update_technical_qa_summary

def populate_technical_qa():
    print("Starting population of TechnicalInterviewQA table (Single Row per Session)...")
    
    sessions = InterviewSession.objects.all()
    count = 0
    
    for session in sessions:
        # Clear existing entries first to avoid duplicates or stale multi-row data
        deleted_count, _ = TechnicalInterviewQA.objects.filter(session=session).delete()
        if deleted_count > 0:
            print(f"Cleared {deleted_count} existing rows for session {session.id}")
            
        try:
            # Call the service function to regenerate the single row
            update_technical_qa_summary(session)
            count += 1
            import time
            time.sleep(0.05) # Small sleep to yield lock
        except Exception as e:
            print(f"❌ Error processing session {session.id}: {e}")
            
    print(f"Completed! Processed {count} sessions.")

if __name__ == "__main__":
    populate_technical_qa()
