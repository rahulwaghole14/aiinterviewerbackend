# interviews/models.py
import uuid
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from candidates.models import Candidate
from jobs.models import Job
from authapp.models import CustomUser


class InterviewSlot(models.Model):
    """
    Represents available interview time slots that can be booked for AI interviews
    """
    class SlotType(models.TextChoices):
        FIXED = "fixed", "Fixed Time Slot"
        FLEXIBLE = "flexible", "Flexible Time Slot"
        RECURRING = "recurring", "Recurring Slot"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        BOOKED = "booked", "Booked"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    class AIInterviewType(models.TextChoices):
        TECHNICAL = "technical", "Technical Interview"
        BEHAVIORAL = "behavioral", "Behavioral Interview"
        CODING = "coding", "Coding Interview"
        SYSTEM_DESIGN = "system_design", "System Design Interview"
        GENERAL = "general", "General Interview"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Slot details
    slot_type = models.CharField(max_length=20, choices=SlotType.choices, default=SlotType.FIXED)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    
    # Time details
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60, help_text="Duration in minutes")
    
    # AI Interview details (replacing interviewer)
    ai_interview_type = models.CharField(
        max_length=20, 
        choices=AIInterviewType.choices, 
        default=AIInterviewType.GENERAL,
        help_text="Type of AI interview to be conducted"
    )
    ai_configuration = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="AI interview configuration settings"
    )
    
    # Company and job context
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='interview_slots')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='interview_slots', null=True, blank=True)
    
    # Recurring slot details
    is_recurring = models.BooleanField(default=False)
    recurring_pattern = models.JSONField(default=dict, blank=True, help_text="Recurring pattern configuration")
    
    # Metadata
    notes = models.TextField(blank=True)
    max_candidates = models.PositiveIntegerField(default=1, help_text="Maximum candidates per slot")
    current_bookings = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['status', 'ai_interview_type']),
            models.Index(fields=['company', 'start_time']),
        ]

    def clean(self):
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError(_("End time must be after start time"))
            
            # Only validate business hours if this is a new slot or time is being changed
            if not self.pk or self._state.adding:
                # Check if time is within business hours (08:00-22:00 UTC)
                start_hour = self.start_time.hour
                end_hour = self.end_time.hour
                
                if start_hour < 8 or end_hour > 22:
                    raise ValidationError(_("Interview time must be between 08:00 and 22:00 UTC"))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def is_available(self):
        """Check if slot is available for booking"""
        return (
            self.status == self.Status.AVAILABLE and
            self.current_bookings < self.max_candidates and
            self.start_time > timezone.now()
        )

    def book_slot(self):
        """Book the slot for an interview"""
        if not self.is_available():
            raise ValidationError(_("Slot is not available for booking"))
        
        self.current_bookings += 1
        if self.current_bookings >= self.max_candidates:
            self.status = self.Status.BOOKED
        self.save()

    def release_slot(self):
        """Release the slot booking"""
        if self.current_bookings > 0:
            self.current_bookings -= 1
            if self.status == self.Status.BOOKED and self.current_bookings < self.max_candidates:
                self.status = self.Status.AVAILABLE
            self.save()
            return True
        return False

    def __str__(self):
        return f"AI Interview Slot - {self.ai_interview_type} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"


class InterviewSchedule(models.Model):
    """
    Links interviews to specific slots and manages the booking process for AI interviews
    """
    class ScheduleStatus(models.TextChoices):
        PENDING = "pending", "Pending Confirmation"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        RESCHEDULED = "rescheduled", "Rescheduled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core relationships
    interview = models.OneToOneField('Interview', on_delete=models.CASCADE, related_name='schedule')
    slot = models.ForeignKey(InterviewSlot, on_delete=models.CASCADE, related_name='schedules')
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=ScheduleStatus.choices, default=ScheduleStatus.PENDING)
    booking_notes = models.TextField(blank=True)
    
    # Timestamps
    booked_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Cancellation details
    cancellation_reason = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='cancelled_schedules'
    )

    class Meta:
        ordering = ['-booked_at']
        indexes = [
            models.Index(fields=['status', 'booked_at']),
            models.Index(fields=['slot', 'status']),
        ]

    def save(self, *args, **kwargs):
        # Auto-update interview times when schedule is created/updated
        if self.slot and self.interview:
            self.interview.started_at = self.slot.start_time
            self.interview.ended_at = self.slot.end_time
            self.interview.save()
        super().save(*args, **kwargs)

    def confirm_schedule(self):
        """Confirm the interview schedule"""
        self.status = self.ScheduleStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save()

    def cancel_schedule(self, reason="", cancelled_by=None):
        """Cancel the interview schedule"""
        self.status = self.ScheduleStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.cancelled_by = cancelled_by
        self.slot.release_slot()
        self.save()

    def __str__(self):
        return f"AI Interview Schedule - {self.interview.candidate.full_name} ({self.slot.ai_interview_type})"


class Interview(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        ERROR     = "error",     "Error"

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate     = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="interviews")
    job           = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="interviews",
                                     null=True, blank=True)

    status        = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    interview_round = models.CharField(max_length=100, blank=True)
    feedback      = models.TextField(blank=True)

    started_at    = models.DateTimeField(null=True, blank=True)
    ended_at      = models.DateTimeField(null=True, blank=True)
    video_url     = models.URLField(max_length=500, blank=True)
    
    # Secure interview link for candidate access
    interview_link = models.CharField(max_length=255, blank=True, help_text="Secure link for candidate to join interview")
    link_expires_at = models.DateTimeField(null=True, blank=True, help_text="When the interview link expires")

    created_at    = models.DateTimeField(default=timezone.now, editable=False)
    updated_at    = models.DateTimeField(auto_now=True)

    @property
    def duration_seconds(self):
        if self.started_at and self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds())
        return 0

    @property
    def is_scheduled(self):
        return hasattr(self, 'schedule') and self.schedule is not None

    @property
    def ai_interview_type(self):
        """Get the AI interview type from the scheduled slot"""
        if self.is_scheduled and self.schedule.slot:
            return self.schedule.slot.ai_interview_type
        return None

    def generate_interview_link(self):
        """Generate a secure interview link for the candidate"""
        if not self.started_at:
            return None
        
        # Create a unique token based on interview ID and candidate email
        token_data = f"{self.id}:{self.candidate.email}:{self.started_at.isoformat()}"
        
        # Use HMAC with a secret key for security
        secret_key = getattr(settings, 'INTERVIEW_LINK_SECRET', 'default-secret-key')
        signature = hmac.new(
            secret_key.encode('utf-8'),
            token_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Create the link token
        link_token = base64.urlsafe_b64encode(f"{self.id}:{signature}".encode('utf-8')).decode('utf-8')
        
        # Set expiration to 2 hours after interview end time
        self.link_expires_at = self.ended_at + timedelta(hours=2) if self.ended_at else None
        self.interview_link = link_token
        self.save()
        
        return link_token

    def validate_interview_link(self, link_token):
        """Validate if the interview link is valid and accessible"""
        if not self.interview_link or self.interview_link != link_token:
            return False, "Invalid interview link"
        
        if self.link_expires_at and timezone.now() > self.link_expires_at:
            return False, "Interview link has expired"
        
        # Check if it's within the interview window (15 minutes before to 2 hours after)
        now = timezone.now()
        if self.started_at and self.ended_at:
            interview_start = self.started_at - timedelta(minutes=15)
            interview_end = self.ended_at + timedelta(hours=2)
            
            if now < interview_start:
                return False, f"Interview hasn't started yet. Please join at {self.started_at.strftime('%B %d, %Y at %I:%M %p')}"
            
            if now > interview_end:
                return False, "Interview has ended"
        
        return True, "Link is valid"

    def get_interview_url(self):
        """Get the full interview URL for the candidate"""
        if not self.interview_link:
            return None
        
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return f"{base_url}/interview/{self.interview_link}"

    def __str__(self):
        return f"AI Interview - {self.candidate.full_name} ({self.status})"


class AIInterviewConfiguration(models.Model):
    """
    Manages AI interview configuration patterns and settings
    """
    class AIInterviewType(models.TextChoices):
        TECHNICAL = "technical", "Technical Interview"
        BEHAVIORAL = "behavioral", "Behavioral Interview"
        CODING = "coding", "Coding Interview"
        SYSTEM_DESIGN = "system_design", "System Design Interview"
        GENERAL = "general", "General Interview"

    class DayOfWeek(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='ai_interview_configurations')
    interview_type = models.CharField(max_length=20, choices=AIInterviewType.choices)
    
    # Availability pattern
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Slot configuration
    slot_duration = models.PositiveIntegerField(default=60, help_text="Duration in minutes")
    break_duration = models.PositiveIntegerField(default=15, help_text="Break between slots in minutes")
    
    # AI settings
    ai_settings = models.JSONField(default=dict, help_text="AI interview specific settings")
    
    # Date range
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['company', 'interview_type', 'day_of_week', 'valid_from']
        ordering = ['day_of_week', 'start_time']

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_("End time must be after start time"))

    def __str__(self):
        return f"AI Config - {self.interview_type} ({self.get_day_of_week_display()})"


class InterviewConflict(models.Model):
    """
    Tracks and manages interview scheduling conflicts for AI interviews
    """
    class ConflictType(models.TextChoices):
        OVERLAP = "overlap", "Time Overlap"
        AI_SYSTEM_ERROR = "ai_system_error", "AI System Error"
        SLOT_UNAVAILABLE = "slot_unavailable", "Slot Unavailable"
        CANDIDATE_UNAVAILABLE = "candidate_unavailable", "Candidate Unavailable"
        SYSTEM_ERROR = "system_error", "System Error"

    class Resolution(models.TextChoices):
        PENDING = "pending", "Pending Resolution"
        RESCHEDULED = "rescheduled", "Rescheduled"
        CANCELLED = "cancelled", "Cancelled"
        RESOLVED = "resolved", "Resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Conflict details
    conflict_type = models.CharField(max_length=30, choices=ConflictType.choices)
    resolution = models.CharField(max_length=20, choices=Resolution.choices, default=Resolution.PENDING)
    
    # Related interviews
    primary_interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='primary_conflicts')
    conflicting_interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='conflicting_interviews', null=True, blank=True)
    
    # Conflict details
    conflict_details = models.JSONField(default=dict)
    resolution_notes = models.TextField(blank=True)
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-detected_at']

    def __str__(self):
        return f"Conflict - {self.conflict_type} for {self.primary_interview.candidate.full_name}"
