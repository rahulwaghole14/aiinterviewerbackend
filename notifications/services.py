from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    Notification, NotificationTemplate, UserNotificationPreference,
    NotificationType, NotificationChannel, NotificationPriority
)
from utils.logger import ActionLogger
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class NotificationService:
    """Service class for handling notifications"""
    
    @staticmethod
    def create_notification(
        recipient,
        notification_type,
        title,
        message,
        channels=None,
        priority=NotificationPriority.MEDIUM,
        metadata=None
    ):
        """Create and send a notification"""
        try:
            # Get user notification preferences
            preferences, created = UserNotificationPreference.objects.get_or_create(
                user=recipient,
                defaults={
                    'email_enabled': True,
                    'in_app_enabled': True,
                    'sms_enabled': False
                }
            )
            
            # Filter channels based on user preferences
            if channels is None:
                channels = preferences.get_enabled_channels()
            else:
                # Only use channels that user has enabled
                enabled_channels = preferences.get_enabled_channels()
                channels = [ch for ch in channels if ch in enabled_channels]
            
            # Check if user wants this type of notification
            if not NotificationService._should_send_notification(preferences, notification_type):
                return None
            
            # Create notification
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                channels=channels,
                metadata=metadata or {}
            )
            
            # Send notification
            notification.send_notification()
            
            # Log the notification
            ActionLogger.log_user_action(
                user=recipient,
                action='notification_sent',
                details={
                    'notification_id': notification.id,
                    'type': notification_type,
                    'channels': channels,
                    'priority': priority
                },
                status='SUCCESS'
            )
            
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            ActionLogger.log_user_action(
                user=recipient,
                action='notification_failed',
                details={
                    'type': notification_type,
                    'error': str(e)
                },
                status='FAILED'
            )
            return None
    
    @staticmethod
    def create_notification_from_template(
        recipient,
        template_name,
        context=None,
        channels=None,
        priority=None
    ):
        """Create notification using a template"""
        try:
            template = NotificationTemplate.objects.get(
                name=template_name,
                is_active=True
            )
            
            # Render template with context
            title, message = template.render_template(context or {})
            
            # Use template priority if not specified
            if priority is None:
                priority = template.priority
            
            # Use template channels if not specified
            if channels is None:
                channels = template.channels
            
            return NotificationService.create_notification(
                recipient=recipient,
                notification_type=template.notification_type,
                title=title,
                message=message,
                channels=channels,
                priority=priority,
                metadata={'template': template_name, 'context': context}
            )
            
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Notification template '{template_name}' not found")
            return None
        except Exception as e:
            logger.error(f"Error creating notification from template: {e}")
            return None
    
    @staticmethod
    def send_interview_scheduled_notification(interview, recipient=None):
        """Send notification when interview is scheduled"""
        if recipient is None:
            recipient = interview.candidate.recruiter
        
        context = {
            'candidate_name': interview.candidate.full_name,
            'job_title': interview.job.job_title if interview.job else 'N/A',
            'interview_date': interview.started_at.strftime('%B %d, %Y at %I:%M %p') if interview.started_at else 'TBD',
            'company_name': interview.job.company_name if interview.job else 'N/A'
        }
        
        return NotificationService.create_notification_from_template(
            recipient=recipient,
            template_name='interview_scheduled',
            context=context,
            priority=NotificationPriority.HIGH
        )
    
    @staticmethod
    def send_resume_processed_notification(resume, recipient=None):
        """Send notification when resume is processed"""
        if recipient is None:
            recipient = resume.user
        
        context = {
            'filename': resume.file.name.split('/')[-1],
            'extracted_data': resume.parsed_text[:100] + '...' if resume.parsed_text else 'No text extracted'
        }
        
        return NotificationService.create_notification_from_template(
            recipient=recipient,
            template_name='resume_processed',
            context=context,
            priority=NotificationPriority.MEDIUM
        )
    
    @staticmethod
    def send_bulk_upload_completed_notification(user, results):
        """Send notification for bulk resume upload completion"""
        try:
            summary = results.get('summary', {})
            total_files = summary.get('total_files', 0)
            successful = summary.get('successful', 0)
            failed = summary.get('failed', 0)
            
            message = f"Bulk resume upload completed: {successful}/{total_files} successful"
            if failed > 0:
                message += f", {failed} failed"
            
            NotificationService.create_notification(
                user=user,
                notification_type='BULK_UPLOAD_COMPLETED',
                title='Bulk Resume Upload Completed',
                message=message,
                details={
                    'total_files': total_files,
                    'successful': successful,
                    'failed': failed,
                    'results': results.get('results', [])
                }
            )
        except Exception as e:
            logger.error(f"Failed to send bulk upload notification: {e}")

    @staticmethod
    def send_bulk_candidate_creation_notification(user, successful_count, domain, role):
        """Send notification for bulk candidate creation completion"""
        try:
            message = f"Bulk candidate creation completed: {successful_count} candidates created for {domain}/{role}"
            
            NotificationService.create_notification(
                user=user,
                notification_type='BULK_CANDIDATE_CREATION_COMPLETED',
                title='Bulk Candidate Creation Completed',
                message=message,
                details={
                    'successful_count': successful_count,
                    'domain': domain,
                    'role': role
                }
            )
        except Exception as e:
            logger.error(f"Failed to send bulk candidate creation notification: {e}")
    
    @staticmethod
    def send_candidate_added_notification(candidate, recipient=None):
        """Send notification when candidate is added"""
        if recipient is None:
            recipient = candidate.recruiter
        
        context = {
            'candidate_name': candidate.full_name,
            'candidate_email': candidate.email,
            'domain': candidate.domain
        }
        
        return NotificationService.create_notification_from_template(
            recipient=recipient,
            template_name='candidate_added',
            context=context,
            priority=NotificationPriority.MEDIUM
        )
    
    @staticmethod
    def send_job_created_notification(job, recipient=None):
        """Send notification when job is created"""
        if recipient is None:
            # Send to all hiring agencies under the company
            from hiring_agency.models import UserData
            recipients = UserData.objects.filter(company_name=job.company_name)
        else:
            recipients = [recipient]
        
        context = {
            'job_title': job.job_title,
            'company_name': job.company_name,
            'position_level': job.position_level,
            'number_to_hire': job.number_to_hire
        }
        
        notifications = []
        for recipient in recipients:
            notification = NotificationService.create_notification_from_template(
                recipient=recipient.user,
                template_name='job_created',
                context=context,
                priority=NotificationPriority.MEDIUM
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def send_interview_reminder_notification(interview):
        """Send reminder notification for upcoming interview"""
        context = {
            'candidate_name': interview.candidate.full_name,
            'interview_date': interview.started_at.strftime('%B %d, %Y at %I:%M %p') if interview.started_at else 'TBD',
            'job_title': interview.job.job_title if interview.job else 'N/A'
        }
        
        # Send to both candidate's recruiter and candidate (if they have an account)
        recipients = [interview.candidate.recruiter]
        if hasattr(interview.candidate, 'user') and interview.candidate.user:
            recipients.append(interview.candidate.user)
        
        notifications = []
        for recipient in recipients:
            notification = NotificationService.create_notification_from_template(
                recipient=recipient,
                template_name='interview_reminder',
                context=context,
                priority=NotificationPriority.HIGH
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def mark_notification_as_read(notification_id, user):
        """Mark a notification as read"""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=user
            )
            notification.mark_as_read()
            
            ActionLogger.log_user_action(
                user=user,
                action='notification_read',
                details={'notification_id': notification_id},
                status='SUCCESS'
            )
            
            return True
        except Notification.DoesNotExist:
            return False
    
    @staticmethod
    def get_unread_notifications_count(user):
        """Get count of unread notifications for user"""
        return Notification.objects.filter(
            recipient=user,
            status__in=['pending', 'sent']
        ).count()
    
    @staticmethod
    def _should_send_notification(preferences, notification_type):
        """Check if user wants to receive this type of notification"""
        if notification_type in [
            NotificationType.INTERVIEW_SCHEDULED,
            NotificationType.INTERVIEW_REMINDER
        ]:
            return preferences.interview_notifications
        elif notification_type in [
            NotificationType.RESUME_PROCESSED,
            NotificationType.BULK_UPLOAD_COMPLETED
        ]:
            return preferences.resume_notifications
        elif notification_type == NotificationType.SYSTEM_ALERT:
            return preferences.system_notifications
        else:
            return True  # Default to sending other types 