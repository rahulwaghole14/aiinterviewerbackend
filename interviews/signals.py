from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Interview
from candidates.models import Candidate
from ai_interview.models import AIInterviewSession
from django.utils import timezone


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


@receiver(post_save, sender=Interview)
def create_ai_interview_session_on_interview_scheduled(sender, instance, created, **kwargs):
    """
    Automatically create AI interview session when interview is scheduled
    """
    # Only create AI session for newly created interviews or when status changes to 'scheduled'
    if created or (not created and instance.status == 'scheduled'):
        # Check if AI session already exists
        existing_session = AIInterviewSession.objects.filter(interview=instance).first()
        
        if not existing_session:
            try:
                # Create AI configuration
                ai_configuration = {
                    'candidate_name': instance.candidate.full_name,
                    'candidate_email': instance.candidate.email,
                    'job_title': instance.job.job_title if instance.job else '',
                    'job_description': getattr(instance.job, 'description', '') or getattr(instance.job, 'job_description', '') or '',
                    'resume_text': getattr(instance.candidate, 'resume_text', '') or '',
                    'language_code': 'en',
                    'accent_tld': 'com'
                }
                
                # Create AI interview session
                ai_session = AIInterviewSession.objects.create(
                    interview=instance,
                    status='ACTIVE',
                    model_name='gemini-1.5-flash-latest',
                    model_version='1.0',
                    ai_configuration=ai_configuration,
                    session_started_at=timezone.now()
                )
                
                print(f"Created AI interview session {ai_session.id} for interview {instance.id}")
                
            except Exception as e:
                print(f"Error creating AI interview session for interview {instance.id}: {e}")
