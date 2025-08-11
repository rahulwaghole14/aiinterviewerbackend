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
    Represents available interview time slots that can be booked
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Slot details
    slot_type = models.CharField(max_length=20, choices=SlotType.choices, default=SlotType.FIXED)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    
    # Time details
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60, help_text="Duration in minutes")
    
    # Interviewer details
    interviewer = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='interview_slots',
        limit_choices_to={'role__in': ['ADMIN', 'COMPANY', 'HIRING_AGENCY', 'RECRUITER']}
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
            models.Index(fields=['interviewer', 'start_time']),
            models.Index(fields=['company', 'start_time']),
            models.Index(fields=['status', 'start_time']),
        ]

    def clean(self):
        """Validate slot times and conflicts"""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError(_("End time must be after start time"))
            
            # Check for overlapping slots for the same interviewer
            overlapping = InterviewSlot.objects.filter(
                interviewer=self.interviewer,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
                status__in=['available', 'booked']
            ).exclude(id=self.id)
            
            if overlapping.exists():
                raise ValidationError(_("This slot overlaps with existing slots for the interviewer"))

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
        """Book this slot"""
        if self.is_available():
            self.current_bookings += 1
            if self.current_bookings >= self.max_candidates:
                self.status = self.Status.BOOKED
            self.save()
            return True
        return False

    def release_slot(self):
        """Release a booking from this slot"""
        if self.current_bookings > 0:
            self.current_bookings -= 1
            if self.status == self.Status.BOOKED:
                self.status = self.Status.AVAILABLE
            self.save()
            return True
        return False

    def __str__(self):
        return f"Slot {self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.interviewer.full_name}"


class InterviewSchedule(models.Model):
    """
    Links interviews to specific slots and manages the booking process
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
        self.save()
        
        # Release the slot
        self.slot.release_slot()

    def __str__(self):
        return f"Schedule {self.interview.candidate.full_name} - {self.slot.start_time.strftime('%Y-%m-%d %H:%M')}"


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
        return None

    @property
    def is_scheduled(self):
        """Check if interview has a confirmed schedule"""
        return hasattr(self, 'schedule') and self.schedule.status == InterviewSchedule.ScheduleStatus.CONFIRMED

    @property
    def interviewer(self):
        """Get the interviewer from the schedule"""
        if hasattr(self, 'schedule'):
            return self.schedule.slot.interviewer
        return None

    def __str__(self):
        return f"Interview {self.id} — {self.candidate.full_name}"


class InterviewerAvailability(models.Model):
    """
    Manages interviewer availability patterns and preferences
    """
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    interviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='availability_patterns')
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='interviewer_availability')
    
    # Availability pattern
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Slot configuration
    slot_duration = models.PositiveIntegerField(default=60, help_text="Duration in minutes")
    break_duration = models.PositiveIntegerField(default=15, help_text="Break between slots in minutes")
    
    # Availability settings
    is_available = models.BooleanField(default=True)
    max_slots_per_day = models.PositiveIntegerField(default=8)
    
    # Date range
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['interviewer', 'day_of_week', 'valid_from']
        ordering = ['day_of_week', 'start_time']

    def clean(self):
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError(_("End time must be after start time"))

    def __str__(self):
        return f"{self.interviewer.full_name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class InterviewConflict(models.Model):
    """
    Tracks and manages interview scheduling conflicts
    """
    class ConflictType(models.TextChoices):
        OVERLAP = "overlap", "Time Overlap"
        INTERVIEWER_UNAVAILABLE = "interviewer_unavailable", "Interviewer Unavailable"
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
        return f"Conflict {self.conflict_type} - {self.primary_interview.candidate.full_name}"
