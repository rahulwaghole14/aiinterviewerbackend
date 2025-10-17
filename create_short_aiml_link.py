"""
Generate interview link for AI/ML Intern position
4 technical voice questions + 2 coding questions
"""
import os
import django
import sys
from datetime import datetime, timedelta
import pytz
import secrets

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.models import InterviewSession

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

def main():
    # Generate clean session key
    session_key = secrets.token_hex(16)
    
    # Create interview session
    utc_now = datetime.now(pytz.UTC)
    
    session = InterviewSession.objects.create(
        candidate_name='Dhananjay Suhas Paturkar',
        candidate_email='dhananjay@example.com',
        job_description=JD,
        session_key=session_key,
        scheduled_at=utc_now,
        status='SCHEDULED',
        language_code='en-IN',
        accent_tld='co.in'
    )
    
    print(f"Generated session key: {session_key}")
    print(f"✅ Created InterviewSession: {session.id}")
    print()
    print("=" * 70)
    print("AI/ML INTERN INTERVIEW LINK (Valid for 2 hours):")
    print(f"   http://127.0.0.1:8000/?session_key={session_key}")
    print("=" * 70)
    print(f"Position: AI/ML Intern")
    print(f"Candidate: Dhananjay Suhas Paturkar")
    print(f"Session ID: {session.id}")
    print(f"Session Key: {session_key}")
    print(f"Technical Voice Questions: 4")
    print(f"Coding Questions: 2")
    print(f"Scheduled At: {session.scheduled_at}")
    print(f"Status: {session.status}")
    print("=" * 70)
    print()
    print("Next step:")
    print(f"  python generate_coding_questions.py {session_key} 2")
    print("=" * 70)
    
    return session_key

if __name__ == "__main__":
    session_key = main()

