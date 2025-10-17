#!/usr/bin/env python3
"""
Integrated AI Interview Link Generator
=====================================

This script integrates all the append files and generates a complete working
AI interview link with proper authentication, database setup, and AI integration.

Features:
- Creates admin user, company, job, and candidate
- Generates secure interview link with token validation
- Sets up AI interview session with proper configuration
- Integrates with existing AI services and models
- Provides complete working interview flow

Usage: python integrated_ai_interview_link_generator.py [candidate_name]
"""

import os
import sys
import django
import uuid
import base64
import hmac
import hashlib
import requests
import json
import time
from datetime import datetime, timedelta
import pytz

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from candidates.models import Candidate
from jobs.models import Job
from companies.models import Company
from interviews.models import Interview, InterviewSlot, InterviewSchedule
from ai_interview.models import (
    AIInterviewSession,
    AIInterviewQuestion,
    AIInterviewResponse,
    AIInterviewResult,
)
from ai_interview.services import ai_interview_service
from interview_app.models import InterviewSession

User = get_user_model()


class IntegratedAIInterviewLinkGenerator:
    def __init__(self):
        self.ist = pytz.timezone("Asia/Kolkata")
        self.base_url = "http://127.0.0.1:8000"
        self.admin_email = "admin@rslsolution.com"
        self.admin_password = "admin123456"

    def print_step(self, step_num, title, description=""):
        """Print a formatted step header"""
        print(f"\n{'='*60}")
        print(f"🔧 STEP {step_num}: {title}")
        print(f"{'='*60}")
        if description:
            print(f"📝 {description}")
        print()

    def print_success(self, message):
        """Print success message"""
        print(f"✅ {message}")

    def print_error(self, message):
        """Print error message"""
        print(f"❌ {message}")

    def print_info(self, message):
        """Print info message"""
        print(f"ℹ️  {message}")

    def print_warning(self, message):
        """Print warning message"""
        print(f"⚠️  {message}")

    def generate_secure_link_token(self, interview_id):
        """Generate a secure link token for the interview"""
        try:
            # Create a signature using the interview ID and secret key
            signature = hmac.new(
                settings.SECRET_KEY.encode("utf-8"),
                str(interview_id).encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            # Combine interview ID and signature
            token_data = f"{interview_id}:{signature}"

            # Encode to base64 for URL safety
            token = base64.urlsafe_b64encode(token_data.encode("utf-8")).decode("utf-8")

            return token
        except Exception as e:
            self.print_error(f"Failed to generate secure token: {e}")
            return None

    def create_admin_user(self):
        """Create admin user if not exists"""
        try:
            admin_user = User.objects.filter(email=self.admin_email).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    email=self.admin_email,
                    password=self.admin_password,
                    first_name="Admin",
                    last_name="User",
                )
                self.print_success(f"Created admin user: {admin_user.email}")
            else:
                self.print_success(f"Admin user already exists: {admin_user.email}")
            return admin_user
        except Exception as e:
            self.print_error(f"Failed to create admin user: {e}")
            return None

    def create_company(self):
        """Create company if not exists"""
        try:
            company = Company.objects.filter(name="RSL Solutions").first()
            if not company:
                company = Company.objects.create(
                    name="RSL Solutions",
                    description="Leading technology solutions provider",
                    industry="Technology",
                    website="https://rslsolutions.com",
                    phone="+1-555-0123",
                    email="contact@rslsolutions.com",
                )
                self.print_success(f"Created company: {company.name}")
            else:
                self.print_success(f"Company already exists: {company.name}")
            return company
        except Exception as e:
            self.print_error(f"Failed to create company: {e}")
            return None

    def create_job(self, company):
        """Create job if not exists"""
        try:
            job = Job.objects.filter(job_title="Software Engineer").first()
            if not job:
                job = Job.objects.create(
                    job_title="Software Engineer",
                    company_name=company.name,
                    tech_stack_details="Python, Django, React, JavaScript, SQL, AWS, Docker",
                    domain="Technology",
                    position_level="Mid-level",
                    number_to_hire=1,
                    current_team_size_info="5-10 developers",
                    current_process="Technical interview with AI",
                    job_description="""
                    We are looking for a skilled Software Engineer to join our dynamic team.
                    
                    Requirements:
                    - 3+ years of experience in software development
                    - Proficiency in Python, Django, React, and JavaScript
                    - Experience with databases (SQL, PostgreSQL)
                    - Knowledge of cloud platforms (AWS, Azure)
                    - Strong problem-solving and communication skills
                    
                    Responsibilities:
                    - Develop and maintain web applications
                    - Collaborate with cross-functional teams
                    - Write clean, maintainable code
                    - Participate in code reviews
                    - Contribute to technical architecture decisions
                    """,
                    salary_range="60,000 - 90,000 USD",
                    location="Remote/Hybrid",
                    employment_type="Full-time",
                )
                self.print_success(f"Created job: {job.job_title}")
            else:
                self.print_success(f"Job already exists: {job.job_title}")
            return job
        except Exception as e:
            self.print_error(f"Failed to create job: {e}")
            return None

    def create_candidate(self, admin_user, candidate_name="AKSHAY PATIL"):
        """Create candidate if not exists"""
        try:
            candidate = Candidate.objects.filter(full_name=candidate_name).first()
            if not candidate:
                candidate = Candidate.objects.create(
                    full_name=candidate_name,
                    email=f"{candidate_name.lower().replace(' ', '.')}@example.com",
                    phone="+1234567890",
                    work_experience=3,
                    recruiter=admin_user,
                    status="NEW",
                    domain="Technology",
                )
                self.print_success(f"Created candidate: {candidate.full_name}")
            else:
                self.print_success(f"Candidate already exists: {candidate.full_name}")
            return candidate
        except Exception as e:
            self.print_error(f"Failed to create candidate: {e}")
            return None

    def create_interview(self, candidate, job, company):
        """Create interview with proper scheduling"""
        try:
            # Create interview slot
            now = datetime.now(self.ist)
            start_time = now
            end_time = now + timedelta(hours=2)

            # Create interview slot
            slot = InterviewSlot.objects.create(
                start_time=start_time,
                end_time=end_time,
                status="available",
                slot_type="fixed",
                ai_interview_type="technical",
                company=company,
                job=job,
            )

            # Create interview
            interview = Interview.objects.create(
                candidate=candidate,
                job=job,
                interview_round=1,
                started_at=start_time,
                ended_at=end_time,
                status="scheduled",
            )

            # Generate secure link token
            link_token = self.generate_secure_link_token(interview.id)
            if link_token:
                interview.interview_link = link_token
                interview.link_expires_at = end_time
                interview.save()
                self.print_success(f"Generated secure interview link")

            self.print_success(f"Created interview: {interview.id}")
            return interview
        except Exception as e:
            self.print_error(f"Failed to create interview: {e}")
            return None

    def create_ai_interview_session(self, interview):
        """Create AI interview session with proper configuration"""
        try:
            # AI configuration
            ai_configuration = {
                "candidate_name": interview.candidate.full_name,
                "job_title": interview.job.job_title,
                "company_name": interview.job.company_name,
                "job_description": interview.job.tech_stack_details,
                "resume_text": (
                    getattr(interview.candidate.resume, "extracted_text", "")
                    if interview.candidate.resume
                    else "No resume available"
                ),
                "interview_type": "technical",
                "language_code": "en",
                "accent_tld": "com",
                "questions_count": 5,
                "time_per_question": 120,
                "difficulty_level": "medium",
                "focus_areas": ["technical", "behavioral", "problem_solving"],
            }

            # Create AI interview session
            ai_session = AIInterviewSession.objects.create(
                interview=interview,
                status="ACTIVE",
                model_name="gemini-1.5-flash-latest",
                model_version="1.0",
                ai_configuration=ai_configuration,
                session_started_at=timezone.now(),
                total_questions=5,
            )

            self.print_success(f"Created AI interview session: {ai_session.id}")
            return ai_session
        except Exception as e:
            self.print_error(f"Failed to create AI interview session: {e}")
            return None

    def generate_ai_questions(self, ai_session):
        """Generate AI interview questions"""
        try:
            # Use the AI service to generate questions
            questions = ai_interview_service.generate_questions(ai_session)
            self.print_success(f"Generated {len(questions)} AI interview questions")
            return questions
        except Exception as e:
            self.print_error(f"Failed to generate AI questions: {e}")
            # Create fallback questions
            fallback_questions = [
                {
                    "question_text": f'Welcome {ai_session.ai_configuration["candidate_name"]}! Can you tell me about a challenging project you have worked on?',
                    "question_type": "Ice-Breaker",
                    "question_index": 0,
                },
                {
                    "question_text": "What is the difference between `let`, `const`, and `var` in JavaScript?",
                    "question_type": "Technical",
                    "question_index": 1,
                },
                {
                    "question_text": "Describe a time you had a conflict with a coworker and how you resolved it.",
                    "question_type": "Behavioral",
                    "question_index": 2,
                },
                {
                    "question_text": "How would you design a scalable web application architecture?",
                    "question_type": "System Design",
                    "question_index": 3,
                },
                {
                    "question_text": "What are your career goals for the next 5 years?",
                    "question_type": "General",
                    "question_index": 4,
                },
            ]

            created_questions = []
            for q_data in fallback_questions:
                question = AIInterviewQuestion.objects.create(
                    session=ai_session,
                    question_text=q_data["question_text"],
                    question_type=q_data["question_type"],
                    question_index=q_data["question_index"],
                )
                created_questions.append(question)

            self.print_warning(f"Created {len(created_questions)} fallback questions")
            return created_questions

    def create_interview_session(self, interview, link_token):
        """Create interview session for portal"""
        try:
            resume_text = "Experienced candidate with strong technical skills in Python, Django, React, and JavaScript."
            if interview.candidate.resume:
                resume_text = getattr(
                    interview.candidate.resume, "extracted_text", resume_text
                )

            session = InterviewSession.objects.create(
                session_key=link_token,
                candidate_name=interview.candidate.full_name,
                candidate_email=interview.candidate.email,
                job_description=interview.job.tech_stack_details,
                resume_text=resume_text,
                language_code="en",
                accent_tld="com",
                scheduled_at=interview.started_at,
                status="SCHEDULED",
            )
            self.print_success(f"Created interview session: {session.session_key}")
            return session
        except Exception as e:
            self.print_error(f"Failed to create interview session: {e}")
            return None

    def test_api_endpoints(self, interview, link_token):
        """Test the generated interview link via API"""
        try:
            self.print_info("Testing API endpoints...")

            # Test public interview access
            public_url = f"{self.base_url}/api/interviews/public/{link_token}/"
            response = requests.get(public_url, timeout=10)

            if response.status_code == 200:
                self.print_success("Public interview access endpoint is working")
                interview_data = response.json()
                self.print_info(
                    f"Candidate: {interview_data.get('candidate_name', 'Unknown')}"
                )
                self.print_info(f"Job: {interview_data.get('job_title', 'Unknown')}")
            else:
                self.print_warning(
                    f"Public interview access returned {response.status_code}"
                )

            # Test AI interview start endpoint
            ai_start_url = f"{self.base_url}/api/ai-interview/public/start/"
            start_data = {
                "link_token": link_token,
                "candidate_name": interview.candidate.full_name,
            }
            response = requests.post(ai_start_url, json=start_data, timeout=10)

            if response.status_code == 200:
                self.print_success("AI interview start endpoint is working")
                session_data = response.json()
                self.print_info(
                    f"Session ID: {session_data.get('session_id', 'Unknown')}"
                )
            else:
                self.print_warning(
                    f"AI interview start returned {response.status_code}"
                )

        except Exception as e:
            self.print_warning(f"API testing failed: {e}")

    def generate_interview_link(self, candidate_name="AKSHAY PATIL"):
        """Main method to generate integrated AI interview link"""
        try:
            self.print_step(
                1, "SETUP", "Initializing integrated AI interview link generator"
            )
            print(f"🎯 Target Candidate: {candidate_name}")
            print(f"🌐 Base URL: {self.base_url}")
            print(
                f"⏰ Current Time: {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S IST')}"
            )

            # Step 1: Create admin user
            self.print_step(2, "ADMIN USER", "Creating admin user for authentication")
            admin_user = self.create_admin_user()
            if not admin_user:
                return None

            # Step 2: Create company
            self.print_step(3, "COMPANY", "Creating company for job association")
            company = self.create_company()
            if not company:
                return None

            # Step 3: Create job
            self.print_step(4, "JOB", "Creating job for interview")
            job = self.create_job(company)
            if not job:
                return None

            # Step 4: Create candidate
            self.print_step(5, "CANDIDATE", f"Creating candidate: {candidate_name}")
            candidate = self.create_candidate(admin_user, candidate_name)
            if not candidate:
                return None

            # Step 5: Create interview
            self.print_step(6, "INTERVIEW", "Creating interview with secure link")
            interview = self.create_interview(candidate, job, company)
            if not interview:
                return None

            # Step 6: Create AI interview session
            self.print_step(7, "AI SESSION", "Creating AI interview session")
            ai_session = self.create_ai_interview_session(interview)
            if not ai_session:
                return None

            # Step 7: Generate AI questions
            self.print_step(8, "AI QUESTIONS", "Generating AI interview questions")
            questions = self.generate_ai_questions(ai_session)

            # Step 8: Create interview session
            self.print_step(
                9, "PORTAL SESSION", "Creating interview session for portal"
            )
            interview_session = self.create_interview_session(
                interview, interview.interview_link
            )

            # Step 10: Test API endpoints
            self.print_step(10, "API TESTING", "Testing generated interview link")
            self.test_api_endpoints(interview, interview.interview_link)

            # Success summary
            print("\n" + "=" * 60)
            print("🎉 SUCCESS! INTEGRATED AI INTERVIEW LINK GENERATED")
            print("=" * 60)
            print(f"👤 Candidate: {candidate.full_name}")
            print(f"💼 Job: {job.job_title}")
            print(f"🏢 Company: {company.name}")
            print(f"🔗 Interview Link: {interview.interview_link}")
            print(f"🤖 AI Session ID: {ai_session.id}")
            print(f"❓ Questions Generated: {len(questions)}")
            print(
                f"⏰ Valid Until: {interview.link_expires_at.strftime('%Y-%m-%d %H:%M:%S IST')}"
            )
            print("=" * 60)

            # Return the complete data
            return {
                "interview": interview,
                "ai_session": ai_session,
                "questions": questions,
                "link_token": interview.interview_link,
                "public_url": f"{self.base_url}/api/interviews/public/{interview.interview_link}/",
                "ai_start_url": f"{self.base_url}/api/ai-interview/public/start/",
                "candidate_name": candidate.full_name,
                "job_title": job.job_title,
                "company_name": company.name,
            }

        except Exception as e:
            self.print_error(f"Failed to generate interview link: {e}")
            import traceback

            traceback.print_exc()
            return None


def main():
    """Main function to run the integrated generator"""
    print("🚀 INTEGRATED AI INTERVIEW LINK GENERATOR")
    print("=" * 60)
    print("This script integrates all components and generates a complete")
    print("working AI interview link with proper authentication and AI integration.")
    print("=" * 60)

    # Force output to ensure it's working
    import sys

    sys.stdout.flush()

    # Get candidate name from command line argument
    candidate_name = "AKSHAY PATIL"
    if len(sys.argv) > 1:
        candidate_name = sys.argv[1]

    # Create generator instance
    generator = IntegratedAIInterviewLinkGenerator()

    # Generate the interview link
    result = generator.generate_interview_link(candidate_name)

    if result:
        print(f"\n✅ Ready to use! Copy this link:")
        print(f"🔗 {result['link_token']}")
        print(f"\n🌐 Full URL: {result['public_url']}")
        print(f"\n🤖 AI Interview Start: {result['ai_start_url']}")
        print(f"\n📝 To start the interview, visit the full URL above.")
        print(f"\n🔐 Admin Login:")
        print(f"   Email: {generator.admin_email}")
        print(f"   Password: {generator.admin_password}")
        print(f"\n🎯 This is a complete AI-powered interview system!")
        print(f"🤖 The AI will ask questions and evaluate responses in real-time!")

        return result
    else:
        print("\n❌ Failed to generate interview link. Please check the errors above.")
        return None


if __name__ == "__main__":
    main()
