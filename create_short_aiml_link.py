"""
Generate interview link for AI/ML Intern position
4 technical voice questions + 2 coding questions

Usage:
    python create_short_aiml_link.py [LANGUAGE] [CANDIDATE_NAME] [CANDIDATE_EMAIL] [SCHEDULED_TIME]

Parameters:
    LANGUAGE: Optional. Coding language (PYTHON, JAVASCRIPT, JAVA, etc.). Default: PYTHON
    CANDIDATE_NAME: Optional. Full name of the candidate. Default: "Test Candidate"
    CANDIDATE_EMAIL: Optional. Email address of the candidate. Default: "test@example.com"
    SCHEDULED_TIME: Optional. Scheduled time in format YYYY-MM-DD HH:MM (IST). Default: Current time

Examples:
    # Default (current time, PYTHON)
    python create_short_aiml_link.py
    
    # Specify language only
    python create_short_aiml_link.py JAVASCRIPT
    
    # Specify all details
    python create_short_aiml_link.py PYTHON "John Doe" "john@example.com" "2024-10-15 14:30"
    
    # Future scheduled time
    python create_short_aiml_link.py PYTHON "Jane Smith" "jane@example.com" "2024-10-20 10:00"
"""
import os
import django
import sys
from datetime import datetime, timedelta
import pytz
import secrets
import argparse

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.models import InterviewSession
from django.core.mail import send_mail
from django.conf import settings

# AI/ML Intern Job Description
JD = """Job Title: AI/ML Intern

Location: Remote
Job Type: Internship (Full-time)
Duration: 3-6 months

Job Overview:
We are seeking a passionate and motivated AI/ML Intern to join our research and development team. As an intern, you will work closely with experienced professionals in Artificial Intelligence (AI) and Machine Learning (ML) to design, develop, and deploy algorithms that power next-generation AI solutions.

Key Responsibilities:
- Machine Learning Model Development: Build, train, and fine-tune ML models for classification, regression, and recommendation systems
- Data Preprocessing & Analysis: Data cleaning, feature extraction, and transformations
- Research & Innovation: Conduct research on latest AI/ML techniques
- Algorithm Optimization: Improve efficiency and accuracy of ML algorithms
- Testing & Evaluation: Evaluate model performance and troubleshoot issues
- Collaboration: Integrate AI/ML models into production systems
- Documentation: Document processes, experiments, and results

Required Skills:
- Educational Background: Degree in Computer Science, Data Science, Mathematics, Statistics, or related field
- Basic Knowledge of AI/ML: Supervised/unsupervised learning, classification, regression, clustering, neural networks
- Programming Skills: Proficiency in Python, scikit-learn, TensorFlow, Keras, or PyTorch
- Data Structures & Algorithms: Strong foundation in algorithms and data structures
- Mathematics & Statistics: Statistical methods, linear algebra, probability theory, optimization techniques
- Communication Skills: Ability to communicate technical concepts effectively

Preferred Skills:
- Deep learning techniques (CNNs, RNNs)
- Cloud platforms (AWS, Google Cloud, Azure)
- Version control (Git)
- NLP, Computer Vision, or Reinforcement Learning
- Previous internships or projects in AI/ML
"""

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate interview link for AI Interview Portal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s JAVASCRIPT
  %(prog)s PYTHON "John Doe" "john@example.com"
  %(prog)s PYTHON "Jane Smith" "jane@example.com" "2024-10-20 14:30"
        """
    )
    parser.add_argument('language', nargs='?', default='PYTHON', 
                        help='Coding language (PYTHON, JAVASCRIPT, JAVA, etc.). Default: PYTHON')
    parser.add_argument('candidate_name', nargs='?', default='Test Candidate',
                        help='Full name of the candidate. Default: Test Candidate')
    parser.add_argument('candidate_email', nargs='?', default='test@example.com',
                        help='Email address of the candidate. Default: test@example.com')
    parser.add_argument('scheduled_time', nargs='?', default=None,
                        help='Scheduled time in format YYYY-MM-DD HH:MM (IST). Default: Current time')
    return parser.parse_args()

def parse_scheduled_time(time_str):
    """Parse scheduled time string and convert to UTC"""
    if not time_str:
        return datetime.now(pytz.UTC)
    
    try:
        # Parse IST time string: "YYYY-MM-DD HH:MM"
        ist = pytz.timezone('Asia/Kolkata')
        naive_datetime = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
        aware_datetime = ist.localize(naive_datetime)
        # Convert to UTC for storage
        return aware_datetime.astimezone(pytz.UTC)
    except ValueError:
        print(f"❌ Invalid time format: {time_str}")
        print("   Expected format: YYYY-MM-DD HH:MM (e.g., '2024-10-15 14:30')")
        print("   Using current time instead...")
        return datetime.now(pytz.UTC)

def main():
    args = parse_arguments()
    
    # Process arguments
    coding_lang = args.language.upper()
    candidate_name = args.candidate_name
    candidate_email = args.candidate_email
    scheduled_at_utc = parse_scheduled_time(args.scheduled_time)
    
    # Generate clean session key
    session_key = secrets.token_hex(16)
    
    # Create interview session
    session = InterviewSession.objects.create(
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        job_description=JD,
        session_key=session_key,
        scheduled_at=scheduled_at_utc,
        status='SCHEDULED',
        language_code='en-IN',
        accent_tld='co.in'
    )
    # Store chosen coding language marker in a free-form field
    try:
        session.keyword_analysis = f"CODING_LANG={coding_lang}"
        session.save()
    except Exception:
        pass
    
    # Format scheduled time for display
    ist = pytz.timezone('Asia/Kolkata')
    scheduled_time_ist = session.scheduled_at.astimezone(ist)
    scheduled_time_display = scheduled_time_ist.strftime('%Y-%m-%d %I:%M %p IST')
    
    print()
    print("=" * 70)
    print("✅ INTERVIEW SESSION CREATED SUCCESSFULLY")
    print("=" * 70)
    print(f"📋 Candidate Name: {candidate_name}")
    print(f"📧 Candidate Email: {candidate_email}")
    print(f"📅 Scheduled Time: {scheduled_time_display}")
    print(f"💻 Coding Language: {coding_lang}")
    print(f"🆔 Session ID: {session.id}")
    print(f"🔑 Session Key: {session_key}")
    print()
    print("=" * 70)
    print("🔗 INTERVIEW LINK:")
    print("=" * 70)
    print(f"   http://127.0.0.1:8000/?session_key={session_key}")
    print("=" * 70)
    print()
    print(f"📝 Interview Details:")
    print(f"   • Position: AI/ML Intern")
    print(f"   • Technical Voice Questions: 4")
    print(f"   • Coding Questions: 1")
    print(f"   • Status: {session.status}")
    print("=" * 70)
    print()
    
    # Send email notification to candidate
    try:
        interview_url = f"http://127.0.0.1:8000/?session_key={session_key}"
        
        # Format scheduled time
        ist = pytz.timezone('Asia/Kolkata')
        if session.scheduled_at:
            scheduled_time_ist = session.scheduled_at.astimezone(ist)
            scheduled_time_str = scheduled_time_ist.strftime('%A, %B %d, %Y at %I:%M %p IST')
            scheduled_date = scheduled_time_ist.strftime('%B %d, %Y')
            scheduled_time_only = scheduled_time_ist.strftime('%I:%M %p IST')
        else:
            scheduled_time_str = "To be determined"
            scheduled_date = "TBD"
            scheduled_time_only = "TBD"
        
        # Check email configuration
        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        email_host = getattr(settings, 'EMAIL_HOST', '')
        email_user = getattr(settings, 'EMAIL_HOST_USER', '')
        email_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        
        if 'console' in str(email_backend).lower():
            print(f"\n[EMAIL NOT SENT] EMAIL_BACKEND is 'console' - email would print to console only")
        elif not email_host or not email_user or not email_password:
            print(f"\n[EMAIL NOT SENT] Email configuration incomplete")
            print(f"  EMAIL_HOST: {bool(email_host)}")
            print(f"  EMAIL_HOST_USER: {bool(email_user)}")
            print(f"  EMAIL_HOST_PASSWORD: {bool(email_password)}")
        else:
            # Send email
            email_subject = f"Your Interview Has Been Scheduled - AI/ML Intern"
            email_body = f"""Dear {candidate_name},

Your AI interview has been scheduled successfully!

📋 **Interview Details:**
• Candidate: {session.candidate_name}
• Position: AI/ML Intern
• Date: {scheduled_date}
• Time: {scheduled_time_only}
• Session ID: {session.id}

🔗 **Join Your Interview:**
Click the link below to join your interview at the scheduled time:
{interview_url}

⚠️ **Important Instructions:**
• Please join the interview 5-10 minutes before the scheduled time
• The link will be active 30 seconds before the scheduled time
• The link will expire 10 minutes after the scheduled start time
• Make sure you have a stable internet connection and a quiet environment
• Ensure your camera and microphone are working properly
• Have a valid government-issued ID ready for verification

Best of luck with your interview!

---
This is an automated message. Please do not reply to this email.
"""
            try:
                from_email = email_user or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@talaro.com')
                send_mail(
                    email_subject,
                    email_body,
                    from_email,
                    [session.candidate_email],
                    fail_silently=False,
                )
                print(f"✅ Email sent successfully to {session.candidate_email}")
            except Exception as e:
                print(f"❌ ERROR sending email to {session.candidate_email}: {e}")
    except Exception as e:
        print(f"❌ ERROR in email sending process: {e}")
        import traceback
        traceback.print_exc()
    
    return session_key

if __name__ == "__main__":
    session_key = main()


