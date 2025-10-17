from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import json

User = get_user_model()


class NotificationType(models.TextChoices):
    """Types of notifications"""

    INTERVIEW_SCHEDULED = "interview_scheduled", "Interview Scheduled"
    INTERVIEW_REMINDER = "interview_reminder", "Interview Reminder"
    RESUME_PROCESSED = "resume_processed", "Resume Processed"
    CANDIDATE_ADDED = "candidate_added", "Candidate Added"
    JOB_CREATED = "job_created", "Job Created"
    EVALUATION_COMPLETED = "evaluation_completed", "Evaluation Completed"
    SYSTEM_ALERT = "system_alert", "System Alert"
    PERMISSION_GRANTED = "permission_granted", "Permission Granted"
    BULK_UPLOAD_COMPLETED = "bulk_upload_completed", "Bulk Upload Completed"


class NotificationPriority(models.TextChoices):
    """Notification priority levels"""

    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class NotificationStatus(models.TextChoices):
    """Notification delivery status"""

    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    READ = "read", "Read"


class NotificationChannel(models.TextChoices):
    """Notification delivery channels"""

    EMAIL = "email", "Email"
    IN_APP = "in_app", "In-App"
    SMS = "sms", "SMS"
    PUSH = "push", "Push Notification"


class Notification(models.Model):
    """Base notification model"""

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(
        max_length=50, choices=NotificationType.choices
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.MEDIUM,
    )
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    channels = models.JSONField(
        default=list, help_text="List of channels to send notification through"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict, help_text="Additional data for the notification"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Delivery tracking
    email_sent = models.BooleanField(default=False)
    in_app_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "status"]),
            models.Index(fields=["notification_type", "created_at"]),
            models.Index(fields=["priority", "status"]),
        ]

    def __str__(self):
        return f"{self.notification_type} - {self.recipient.email} ({self.status})"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.read_at:
            self.read_at = timezone.now()
            self.status = NotificationStatus.READ
            self.save()

    def send_notification(self):
        """Send notification through all specified channels"""
        success = True

        for channel in self.channels:
            if channel == NotificationChannel.EMAIL:
                if not self.send_email():
                    success = False
            elif channel == NotificationChannel.IN_APP:
                if not self.send_in_app():
                    success = False
            elif channel == NotificationChannel.SMS:
                if not self.send_sms():
                    success = False

        if success:
            self.status = NotificationStatus.SENT
            self.sent_at = timezone.now()
        else:
            self.status = NotificationStatus.FAILED

        self.save()
        return success

    def send_email(self):
        """Send email notification"""
        try:
            send_mail(
                subject=self.title,
                message=self.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.recipient.email],
                fail_silently=False,
            )
            self.email_sent = True
            self.save()
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False

    def send_in_app(self):
        """Send in-app notification (stored in database)"""
        try:
            self.in_app_sent = True
            self.save()
            return True
        except Exception as e:
            print(f"In-app notification failed: {e}")
            return False

    def send_sms(self):
        """Send SMS notification (placeholder for SMS service integration)"""
        try:
            # TODO: Integrate with SMS service (Twilio, etc.)
            # For now, just mark as sent
            self.sms_sent = True
            self.save()
            return True
        except Exception as e:
            print(f"SMS sending failed: {e}")
            return False


class NotificationTemplate(models.Model):
    """Templates for different types of notifications"""

    name = models.CharField(max_length=100, unique=True)
    notification_type = models.CharField(
        max_length=50, choices=NotificationType.choices
    )
    title_template = models.CharField(
        max_length=255, help_text="Template for notification title"
    )
    message_template = models.TextField(help_text="Template for notification message")
    channels = models.JSONField(
        default=list, help_text="Default channels for this template"
    )
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.MEDIUM,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.notification_type})"

    def render_template(self, context):
        """Render template with context variables"""
        title = self.title_template
        message = self.message_template

        for key, value in context.items():
            title = title.replace(f"{{{{{key}}}}}", str(value))
            message = message.replace(f"{{{{{key}}}}}", str(value))

        return title, message


class UserNotificationPreference(models.Model):
    """User preferences for notifications"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_preferences"
    )

    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)

    # Type preferences
    interview_notifications = models.BooleanField(default=True)
    resume_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)

    # Frequency preferences
    daily_digest = models.BooleanField(default=False)
    weekly_summary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.email}"

    def get_enabled_channels(self):
        """Get list of enabled channels"""
        channels = []
        if self.email_enabled:
            channels.append(NotificationChannel.EMAIL)
        if self.in_app_enabled:
            channels.append(NotificationChannel.IN_APP)
        if self.sms_enabled:
            channels.append(NotificationChannel.SMS)
        return channels
