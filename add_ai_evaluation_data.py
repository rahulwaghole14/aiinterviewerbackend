#!/usr/bin/env python3
"""
Script to add AI interview evaluation data for AI_EVALUATED candidates
and update status to show both manual and AI evaluation when both are present.
"""

import os
import sys
import django
import json
from django.conf import settings
from django.utils import timezone

# Add the project directory to Python path
sys.path.append("/home/mayur/Desktop/AiInterview/aiinterviewerbackend")

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from django.contrib.auth import get_user_model
from candidates.models import Candidate
from interviews.models import Interview
from ai_interview.models import AIInterviewResult
import random
from datetime import datetime, timedelta

User = get_user_model()


def create_ai_evaluation_data():
    """Create sample AI evaluation data"""
    return {
        "overall_rating": random.choice(["EXCELLENT", "GOOD", "FAIR", "POOR"]),
        "total_score": round(random.uniform(6.0, 10.0), 1),
        "technical_score": round(random.uniform(6.0, 10.0), 1),
        "behavioral_score": round(random.uniform(6.0, 10.0), 1),
        "coding_score": round(random.uniform(6.0, 10.0), 1),
        "questions_attempted": random.randint(5, 10),
        "questions_correct": random.randint(3, 8),
        "average_response_time": round(random.uniform(30.0, 120.0), 1),
        "completion_time": random.randint(1800, 3600),
        "ai_summary": "The candidate demonstrated solid technical skills and good communication. Overall performance was satisfactory with room for improvement in certain areas.",
        "ai_recommendations": "Consider for the next round. Focus on improving time management and advanced technical concepts.",
        "strengths": [
            "Strong technical knowledge",
            "Good problem-solving approach",
            "Clear communication skills",
            "Attention to detail",
        ],
        "weaknesses": [
            "Could improve on time management",
            "Needs more experience with advanced concepts",
        ],
        "hire_recommendation": random.choice([True, False]),
        "confidence_level": round(random.uniform(0.7, 0.95), 2),
        "created_at": timezone.now(),
    }


def add_ai_evaluation_data():
    """Add AI evaluation data for AI_EVALUATED candidates"""
    print("🤖 Adding AI evaluation data...")

    # Get all AI_EVALUATED candidates
    ai_evaluated_candidates = Candidate.objects.filter(status="AI_EVALUATED")
    print(f"   - Found {ai_evaluated_candidates.count()} AI_EVALUATED candidates")

    ai_results_created = 0

    for candidate in ai_evaluated_candidates:
        # Get the interview for this candidate
        try:
            interview = Interview.objects.filter(candidate=candidate).first()
            if interview:
                # Create AI evaluation data
                ai_data = create_ai_evaluation_data()

                # Create AIInterviewResult (we'll need to handle the session requirement)
                # For now, we'll create a simple approach
                try:
                    ai_result = AIInterviewResult.objects.create(
                        interview=interview,
                        total_score=ai_data["total_score"],
                        technical_score=ai_data["technical_score"],
                        behavioral_score=ai_data["behavioral_score"],
                        coding_score=ai_data["coding_score"],
                        questions_attempted=ai_data["questions_attempted"],
                        questions_correct=ai_data["questions_correct"],
                        average_response_time=ai_data["average_response_time"],
                        completion_time=ai_data["completion_time"],
                        ai_summary=ai_data["ai_summary"],
                        ai_recommendations=ai_data["ai_recommendations"],
                        strengths=ai_data["strengths"],
                        weaknesses=ai_data["weaknesses"],
                        overall_rating=ai_data["overall_rating"],
                        hire_recommendation=ai_data["hire_recommendation"],
                        confidence_level=ai_data["confidence_level"],
                        created_at=ai_data["created_at"],
                    )
                    ai_results_created += 1
                    print(f"   - Created AI evaluation for {candidate.full_name}")
                except Exception as e:
                    print(
                        f"   - Failed to create AI evaluation for {candidate.full_name}: {e}"
                    )
            else:
                print(f"   - No interview found for {candidate.full_name}")
        except Exception as e:
            print(f"   - Error processing {candidate.full_name}: {e}")

    print(f"✅ Created {ai_results_created} AI evaluation results")
    return ai_results_created


def create_combined_evaluation_candidates():
    """Create candidates with both AI and manual evaluation"""
    print("🔄 Creating candidates with both AI and manual evaluation...")

    # Get some MANUAL_EVALUATED candidates to also add AI evaluation
    manual_evaluated_candidates = Candidate.objects.filter(status="MANUAL_EVALUATED")[
        :3
    ]
    combined_count = 0

    for candidate in manual_evaluated_candidates:
        try:
            interview = Interview.objects.filter(candidate=candidate).first()
            if interview:
                # Check if AI evaluation already exists
                if not hasattr(interview, "aiinterviewresult"):
                    # Create AI evaluation data
                    ai_data = create_ai_evaluation_data()

                    try:
                        ai_result = AIInterviewResult.objects.create(
                            interview=interview,
                            total_score=ai_data["total_score"],
                            technical_score=ai_data["technical_score"],
                            behavioral_score=ai_data["behavioral_score"],
                            coding_score=ai_data["coding_score"],
                            questions_attempted=ai_data["questions_attempted"],
                            questions_correct=ai_data["questions_correct"],
                            average_response_time=ai_data["average_response_time"],
                            completion_time=ai_data["completion_time"],
                            ai_summary=ai_data["ai_summary"],
                            ai_recommendations=ai_data["ai_recommendations"],
                            strengths=ai_data["strengths"],
                            weaknesses=ai_data["weaknesses"],
                            overall_rating=ai_data["overall_rating"],
                            hire_recommendation=ai_data["hire_recommendation"],
                            confidence_level=ai_data["confidence_level"],
                            created_at=ai_data["created_at"],
                        )
                        combined_count += 1
                        print(
                            f"   - Added AI evaluation to {candidate.full_name} (now has both evaluations)"
                        )
                    except Exception as e:
                        print(
                            f"   - Failed to add AI evaluation to {candidate.full_name}: {e}"
                        )
        except Exception as e:
            print(f"   - Error processing {candidate.full_name}: {e}")

    print(f"✅ Created {combined_count} candidates with both AI and manual evaluation")
    return combined_count


def update_candidate_status_logic():
    """Update candidate status to show both evaluations when both are present"""
    print("📊 Updating candidate status logic...")

    # This would typically be done in the frontend logic, but let's check the current statuses
    total_candidates = Candidate.objects.count()
    status_counts = {}

    for status in [
        "NEW",
        "INTERVIEW_SCHEDULED",
        "INTERVIEW_COMPLETED",
        "AI_EVALUATED",
        "MANUAL_EVALUATED",
        "HIRED",
        "REJECTED",
    ]:
        count = Candidate.objects.filter(status=status).count()
        status_counts[status] = count
        print(f"   - {status}: {count} candidates")

    print(f"✅ Total candidates: {total_candidates}")
    return status_counts


def main():
    print("🚀 Adding AI evaluation data and updating status logic...")

    # Add AI evaluation data for AI_EVALUATED candidates
    ai_results_created = add_ai_evaluation_data()

    # Create some candidates with both AI and manual evaluation
    combined_count = create_combined_evaluation_candidates()

    # Show current status distribution
    status_counts = update_candidate_status_logic()

    print(f"\n🎉 Successfully updated data!")
    print(f"   - Added {ai_results_created} AI evaluation results")
    print(f"   - Created {combined_count} candidates with both evaluations")
    print(f"   - Total candidates: {sum(status_counts.values())}")


if __name__ == "__main__":
    main()
