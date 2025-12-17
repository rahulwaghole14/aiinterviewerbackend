# interviews/models.py
import uuid
import hashlib
import hmac
import base64
from datetime import datetime, timedelta, date, time
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
    slot_type = models.CharField(
        max_length=20, choices=SlotType.choices, default=SlotType.FIXED
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE
    )

    # Date and Time details (separated for better UX)
    interview_date = models.DateField(
        default=date.today, help_text="Date of the interview"
    )
    start_time = models.TimeField(
        default=time(8, 0), help_text="Start time in 24-hour format"
    )
    end_time = models.TimeField(
        default=time(8, 10), help_text="End time in 24-hour format"
    )
    duration_minutes = models.PositiveIntegerField(
        default=10, help_text="Duration in minutes"
    )

    # Legacy datetime fields (for backward compatibility during migration)
    legacy_start_datetime = models.DateTimeField(
        null=True, blank=True, help_text="Legacy combined datetime field"
    )
    legacy_end_datetime = models.DateTimeField(
        null=True, blank=True, help_text="Legacy combined datetime field"
    )

    # AI Interview details (replacing interviewer)
    ai_interview_type = models.CharField(
        max_length=20,
        choices=AIInterviewType.choices,
        default=AIInterviewType.GENERAL,
        help_text="Type of AI interview to be conducted",
    )
    ai_configuration = models.JSONField(
        default=dict, blank=True, help_text="AI interview configuration settings"
    )

    # Company and job context
    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="interview_slots"
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="interview_slots",
        null=True,
        blank=True,
    )

    # Recurring slot details
    is_recurring = models.BooleanField(default=False)
    recurring_pattern = models.JSONField(
        default=dict, blank=True, help_text="Recurring pattern configuration"
    )

    # Metadata
    notes = models.TextField(blank=True)
    max_candidates = models.PositiveIntegerField(
        default=1, help_text="Maximum candidates per slot"
    )
    current_bookings = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["interview_date", "start_time"]
        indexes = [
            models.Index(fields=["interview_date", "start_time"]),
            models.Index(fields=["status", "ai_interview_type"]),
            models.Index(fields=["company", "interview_date"]),
        ]

    def clean(self):
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError(_("End time must be after start time"))

    def get_full_start_datetime(self):
        """Combine interview_date and start_time to get full datetime in IST, then convert to UTC"""
        if self.interview_date and self.start_time:
            # Create datetime in IST timezone first
            try:
                import pytz
                ist = pytz.timezone('Asia/Kolkata')
                # Combine date and time as naive datetime
                dt_naive = datetime.combine(self.interview_date, self.start_time)
                # Localize to IST
                dt_ist = ist.localize(dt_naive)
                # Convert to UTC for storage
                dt_utc = dt_ist.astimezone(timezone.utc)
                return dt_utc
            except ImportError:
                # Fallback if pytz not available
                dt = timezone.datetime.combine(self.interview_date, self.start_time)
                return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        return None

    def get_full_end_datetime(self):
        """Combine interview_date and end_time to get full datetime in IST, then convert to UTC"""
        if self.interview_date and self.end_time:
            # Create datetime in IST timezone first
            try:
                import pytz
                ist = pytz.timezone('Asia/Kolkata')
                # Combine date and time as naive datetime
                dt_naive = datetime.combine(self.interview_date, self.end_time)
                # Localize to IST
                dt_ist = ist.localize(dt_naive)
                # Convert to UTC for storage
                dt_utc = dt_ist.astimezone(timezone.utc)
                return dt_utc
            except ImportError:
                # Fallback if pytz not available
                dt = timezone.datetime.combine(self.interview_date, self.end_time)
                return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        return None

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def is_available(self):
        """Check if slot is available for booking"""
        if not self.interview_date or not self.start_time:
            return False

        # Use get_full_start_datetime() which handles IST timezone correctly
        slot_datetime = self.get_full_start_datetime()
        if not slot_datetime:
            return False

        return (
            self.status == self.Status.AVAILABLE
            and self.current_bookings < self.max_candidates
            and slot_datetime > timezone.now()
        )

    def book_slot(self):
        """Book the slot for an interview - increments current_bookings"""
        # Check capacity rather than strict availability check
        current_bookings = self.current_bookings or 0
        max_candidates = self.max_candidates or 1
        
        if current_bookings >= max_candidates:
            raise ValidationError(_("Slot is fully booked (no available spots)"))

        print(f"Booking slot {self.id}:")
        print(
            f"  - Before: current_bookings={self.current_bookings}, max_candidates={self.max_candidates}, status={self.status}"
        )

        self.current_bookings += 1
        if self.current_bookings >= self.max_candidates:
            self.status = self.Status.BOOKED
            print(
                f"  - Slot marked as BOOKED because current_bookings ({self.current_bookings}) >= max_candidates ({self.max_candidates})"
            )
        else:
            print(
                f"  - Slot remains AVAILABLE, current_bookings={self.current_bookings}, max_candidates={self.max_candidates}"
            )

        self.save()
        print(
            f"  - After: current_bookings={self.current_bookings}, max_candidates={self.max_candidates}, status={self.status}"
        )

    def release_slot(self):
        """Release the slot booking"""
        if self.current_bookings > 0:
            self.current_bookings -= 1
            if (
                self.status == self.Status.BOOKED
                and self.current_bookings < self.max_candidates
            ):
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
    interview = models.OneToOneField(
        "Interview", on_delete=models.CASCADE, related_name="schedule"
    )
    slot = models.ForeignKey(
        InterviewSlot, on_delete=models.CASCADE, related_name="schedules"
    )

    # Status and metadata
    status = models.CharField(
        max_length=20, choices=ScheduleStatus.choices, default=ScheduleStatus.PENDING
    )
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
        related_name="cancelled_schedules",
    )

    class Meta:
        ordering = ["-booked_at"]
        indexes = [
            models.Index(fields=["status", "booked_at"]),
            models.Index(fields=["slot", "status"]),
        ]

    def save(self, *args, **kwargs):
        # NOTE: Commented out auto-update to prevent timezone conversion issues
        # The Interview.started_at and ended_at should be set explicitly before creating the schedule
        # 
        # # Auto-update interview times when schedule is created/updated
        # if self.slot and self.interview:
        #     # Combine slot date and times into timezone-aware datetimes
        #     try:
        #         start_dt = timezone.datetime.combine(
        #             self.slot.interview_date, self.slot.start_time
        #         )
        #         end_dt = timezone.datetime.combine(
        #             self.slot.interview_date, self.slot.end_time
        #         )
        #         if timezone.is_naive(start_dt):
        #             start_dt = timezone.make_aware(start_dt)
        #         if timezone.is_naive(end_dt):
        #             end_dt = timezone.make_aware(end_dt)
        #         self.interview.started_at = start_dt
        #         self.interview.ended_at = end_dt
        #         self.interview.save(update_fields=["started_at", "ended_at", "updated_at"])
        #     except Exception:
        #         # Fallback to saving without altering interview times
        #         pass
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
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name="interviews"
    )
    job = models.ForeignKey(
        Job, on_delete=models.CASCADE, related_name="interviews", null=True, blank=True
    )
    slot = models.ForeignKey(
        InterviewSlot,
        on_delete=models.CASCADE,
        related_name="interviews",
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )
    interview_round = models.CharField(max_length=100, blank=True)
    feedback = models.TextField(blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    video_url = models.URLField(max_length=500, blank=True)

    # Secure interview link for candidate access
    interview_link = models.CharField(
        max_length=255,
        blank=True,
        help_text="Secure link for candidate to join interview",
    )
    link_expires_at = models.DateTimeField(
        null=True, blank=True, help_text="When the interview link expires"
    )

    # Session key for AI interview portal
    session_key = models.CharField(
        max_length=40,
        blank=True,
        help_text="Short session key for AI interview portal access",
    )

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Prevent duplicate interviews for the same candidate and slot
        unique_together = [["candidate", "slot"]]

    @property
    def duration_seconds(self):
        if self.started_at and self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds())
        return 0

    @property
    def is_scheduled(self):
        return hasattr(self, "schedule") and self.schedule is not None

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
        secret_key = getattr(settings, "INTERVIEW_LINK_SECRET", "default-secret-key")
        signature = hmac.new(
            secret_key.encode("utf-8"), token_data.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        # Create the link token
        link_token = base64.urlsafe_b64encode(
            f"{self.id}:{signature}".encode("utf-8")
        ).decode("utf-8")

        # Generate a short session key for AI interview portal
        import uuid

        session_key = uuid.uuid4().hex

        # Set expiration to 24 hours after interview end time (or 24 hours from now if no end time)
        if self.ended_at:
            self.link_expires_at = self.ended_at + timedelta(hours=24)
        elif self.started_at:
            self.link_expires_at = self.started_at + timedelta(hours=24)
        else:
            self.link_expires_at = timezone.now() + timedelta(hours=24)
        self.interview_link = link_token
        self.session_key = session_key
        self.save()

        # Create or update the InterviewSession
        from interview_app.models import InterviewSession
        
        # Ensure we have the latest data from DB
        self.refresh_from_db()

        # Build job description from job fields
        job_description = "Technical Role"
        if self.job:
            job_description = self.job.job_description or f"Job Title: {self.job.job_title}\nCompany: {self.job.company_name}"
            if self.job.domain:
                job_description += f"\nDomain: {self.job.domain.name}"
        
        # Extract resume text
        resume_text = "Experienced professional seeking new opportunities."
        if self.candidate and self.candidate.resume:
            if hasattr(self.candidate.resume, 'parsed_text') and self.candidate.resume.parsed_text:
                resume_text = self.candidate.resume.parsed_text
            elif hasattr(self.candidate.resume, 'file') and self.candidate.resume.file:
                try:
                    from interview_app_11.views import get_text_from_file
                    resume_text = get_text_from_file(self.candidate.resume.file) or resume_text
                except Exception:
                    pass
        
        # Get coding language from job
        coding_language = 'PYTHON'
        if self.job:
            coding_language = getattr(self.job, 'coding_language', 'PYTHON')
        
        session, created = InterviewSession.objects.get_or_create(
            session_key=session_key,
            defaults={
                "candidate_name": self.candidate.full_name if self.candidate else "Candidate",
                "candidate_email": self.candidate.email if self.candidate else "",
                "job_description": job_description,
                "resume_text": resume_text,
                "language_code": "en-IN",
                "accent_tld": "co.in",
                "scheduled_at": self.started_at or timezone.now(),
                "status": "SCHEDULED",
            },
        )
        
        # Store coding language if session was created or updated
        if created or not session.keyword_analysis:
            try:
                session.keyword_analysis = f"CODING_LANG={coding_language}"
                session.save(update_fields=['keyword_analysis'])
            except Exception:
                pass

        return link_token

    def validate_interview_link(self, link_token):
        """Validate if the interview link is valid and accessible"""
        if not self.interview_link or self.interview_link != link_token:
            return False, "Invalid interview link"

        if self.link_expires_at and timezone.now() > self.link_expires_at:
            return False, "Interview link has expired"

        # Check if it's within the interview window (15 minutes before to 24 hours after)
        now = timezone.now()
        if self.started_at and self.ended_at:
            interview_start = self.started_at - timedelta(minutes=15)
            # Allow access up to 24 hours after interview ends
            interview_end = self.ended_at + timedelta(hours=24)

            if now < interview_start:
                # Format time in IST for better user experience
                try:
                    import pytz
                    ist = pytz.timezone('Asia/Kolkata')
                    started_at_ist = self.started_at.astimezone(ist)
                    time_str = started_at_ist.strftime('%B %d, %Y at %I:%M %p IST')
                except:
                    time_str = self.started_at.strftime('%B %d, %Y at %I:%M %p')
                return (
                    False,
                    f"Interview hasn't started yet. Please join at {time_str}",
                )

            if now > interview_end:
                return False, "Interview link has expired (valid for 24 hours after interview end)"

        return True, "Link is valid"

    def get_interview_url(self, request=None):
        """Get the full interview URL for the candidate"""
        if not self.interview_link:
            return None

        # Use utility function for consistent URL generation
        from interview_app.utils import get_interview_url
        
        # Use session_key if available, otherwise fall back to interview_link
        session_key = self.session_key if self.session_key else self.interview_link
        return get_interview_url(session_key, request)

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

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="ai_interview_configurations",
    )
    interview_type = models.CharField(max_length=20, choices=AIInterviewType.choices)

    # Availability pattern
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Slot configuration
    slot_duration = models.PositiveIntegerField(
        default=60, help_text="Duration in minutes"
    )
    break_duration = models.PositiveIntegerField(
        default=15, help_text="Break between slots in minutes"
    )

    # AI settings
    ai_settings = models.JSONField(
        default=dict, help_text="AI interview specific settings"
    )

    # Date range
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["company", "interview_type", "day_of_week", "valid_from"]
        ordering = ["day_of_week", "start_time"]

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
    resolution = models.CharField(
        max_length=20, choices=Resolution.choices, default=Resolution.PENDING
    )

    # Related interviews
    primary_interview = models.ForeignKey(
        Interview, on_delete=models.CASCADE, related_name="primary_conflicts"
    )
    conflicting_interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name="conflicting_interviews",
        null=True,
        blank=True,
    )

    # Conflict details
    conflict_details = models.JSONField(default=dict)
    resolution_notes = models.TextField(blank=True)

    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-detected_at"]

    def __str__(self):
        return f"Conflict - {self.conflict_type} for {self.primary_interview.candidate.full_name}"
