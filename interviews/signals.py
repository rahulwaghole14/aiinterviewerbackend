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
    latest_interview = candidate.interviews.order_by('-created_at').first()
    
    if latest_interview:
        # Map interview status to candidate status
        status_mapping = {
            'scheduled': Candidate.Status.PENDING_SCHEDULING,
            'completed': Candidate.Status.BR_EVALUATED,
            'error': Candidate.Status.REQUIRES_ACTION,
        }
        
        if latest_interview.status in status_mapping:
            new_status = status_mapping[latest_interview.status]
            
            # Only update if status is different
            if candidate.status != new_status:
                candidate.status = new_status
                candidate.save(update_fields=['status', 'last_updated'])
