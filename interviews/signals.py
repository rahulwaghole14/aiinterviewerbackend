from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Interview
from candidates.models import Candidate


@receiver(post_save, sender=Interview)
def update_candidate_status_on_interview_change(sender, instance, created, **kwargs):
    """
    Automatically update candidate status when interview status changes
    """
    candidate = instance.candidate

    # Get the most recent interview for this candidate
    latest_interview = candidate.interviews.order_by("-created_at").first()

    if latest_interview:
        # Map interview status to candidate status
        status_mapping = {
            "scheduled": Candidate.Status.INTERVIEW_SCHEDULED,
            "completed": Candidate.Status.INTERVIEW_COMPLETED,
            "error": Candidate.Status.REQUIRES_ACTION,
        }

        if latest_interview.status in status_mapping:
            new_status = status_mapping[latest_interview.status]

            # Only update if status is different
            if candidate.status != new_status:
                candidate.status = new_status
                candidate.save(update_fields=["status", "last_updated"])


@receiver(post_save, sender="evaluation.Evaluation")
def update_candidate_status_on_evaluation_creation(sender, instance, created, **kwargs):
    """
    Automatically update candidate status to EVALUATED when an evaluation is created
    """
    if created:
        candidate = instance.interview.candidate

        # Only update if status is not already EVALUATED
        if candidate.status != Candidate.Status.EVALUATED:
            candidate.status = Candidate.Status.EVALUATED
            candidate.save(update_fields=["status", "last_updated"])
            print(f"Updated candidate {candidate.full_name} status to EVALUATED")
