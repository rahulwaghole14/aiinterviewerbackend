# interviews/models.py
import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
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
            models.Index(fields=['ai_interview_type', 'start_time']),
            models.Index(fields=['company', 'start_time']),
            models.Index(fields=['status', 'start_time']),
        ]

    def clean(self):
        """Validate slot times and conflicts"""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError(_("End time must be after start time"))
            
            # Check for overlapping slots for the same company and AI interview type
            overlapping = InterviewSlot.objects.filter(
                company=self.company,
                ai_interview_type=self.ai_interview_type,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
                status__in=['available', 'booked']
            ).exclude(id=self.id)
            
            if overlapping.exists():
                raise ValidationError(_("This slot overlaps with existing slots for the same AI interview type"))

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
        """Book this slot for an interview"""
        if self.is_available():
            self.current_bookings += 1
            if self.current_bookings >= self.max_candidates:
                self.status = self.Status.BOOKED
            self.save()
            return True
        return False

    def release_slot(self):
        """Release this slot from booking"""
        if self.current_bookings > 0:
            self.current_bookings -= 1
            if self.status == self.Status.BOOKED and self.current_bookings < self.max_candidates:
                self.status = self.Status.AVAILABLE
            self.save()
            return True
        return False

    def __str__(self):
        return f"AI {self.ai_interview_type.title()} Interview Slot - {self.start_time.strftime('%Y-%m-%d %H:%M')} ({self.company.name})"


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
        """Confirm this schedule"""
        self.status = self.ScheduleStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save()

    def cancel_schedule(self, reason="", cancelled_by=None):
        """Cancel this schedule"""
        self.status = self.ScheduleStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.cancelled_by = cancelled_by
        # Release the slot
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
        return f"AI {self.interview_type.title()} Configuration - {self.company.name} ({self.get_day_of_week_display()})"


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
        return f"AI Interview Conflict - {self.conflict_type} ({self.primary_interview.candidate.full_name})"
