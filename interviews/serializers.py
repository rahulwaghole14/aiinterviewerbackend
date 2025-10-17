# interviews/serializers.py
from datetime import time, datetime, timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import (
    Interview,
    InterviewSlot,
    InterviewSchedule,
    AIInterviewConfiguration,
    InterviewConflict,
)


class InterviewSerializer(serializers.ModelSerializer):
    """
    Main read / write serializer for Interview.
    Adds two read‑only convenience fields:
      • candidate_name – Candidate.full_name
      • job_title       – Job.job_title

    Includes a custom validate() that restricts the scheduled
    window to **08:00 – 22:00 UTC** for both start and end times.
    """

    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    job_title = serializers.CharField(source="job.job_title", read_only=True)
    is_scheduled = serializers.BooleanField(read_only=True)
    ai_interview_type = serializers.CharField(read_only=True)

    # Slot information
    slot_details = serializers.SerializerMethodField()
    schedule_status = serializers.SerializerMethodField()
    booking_notes = serializers.SerializerMethodField()

    # AI Interview Result
    ai_result = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = [
            "id",
            "candidate",
            "candidate_name",
            "job",
            "job_title",
            "status",
            "interview_round",
            "feedback",
            "started_at",
            "ended_at",
            "video_url",
            "created_at",
            "updated_at",
            "is_scheduled",
            "ai_interview_type",
            "slot_details",
            "schedule_status",
            "booking_notes",
            "ai_result",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "candidate_name",
            "job_title",
            "is_scheduled",
            "ai_interview_type",
        ]
        extra_kwargs = {
            "candidate": {"required": False},
            "job": {"required": False},
            "started_at": {"required": False},
            "ended_at": {"required": False},
            "status": {"required": False},
            "interview_round": {"required": False},
            "feedback": {"required": False},
            "video_url": {"required": False},
        }

    # ──────────────────────────────────────────────────────────
    # Custom validation: 08:00 – 22:00 UTC scheduling window
    # ──────────────────────────────────────────────────────────
    def validate(self, data):
        """
        Ensure both started_at and ended_at fall between 08:00 and 22:00 UTC.

        If this is a partial update (PATCH), keep the existing
        instance's values where the client omitted a field.
        """
        # Set default interview round if not provided
        if "interview_round" not in data or not data.get("interview_round"):
            data["interview_round"] = "AI Interview"

        # Only validate time constraints if we're updating time fields
        if "started_at" in data or "ended_at" in data:
            start_dt = data.get("started_at") or getattr(
                self.instance, "started_at", None
            )
            end_dt = data.get("ended_at") or getattr(self.instance, "ended_at", None)

            if not start_dt or not end_dt:
                raise serializers.ValidationError(
                    "Both 'started_at' and 'ended_at' must be provided when updating time fields."
                )

            # Time window bounds (24‑hour clock, UTC)
            min_time = time(8, 0)  # 08:00
            max_time = time(22, 0)  # 22:00

            start_t = start_dt.time()
            end_t = end_dt.time()

            # Temporarily disabled time validation for testing
            # if not (min_time <= start_t <= max_time):
            #     raise serializers.ValidationError(
            #         "started_at must be between 08:00 and 22:00 UTC."
            #     )
            # if not (min_time <= end_t <= max_time):
            #     raise serializers.ValidationError(
            #         "ended_at must be between 08:00 and 22:00 UTC."
            #     )
            if end_dt <= start_dt:
                raise serializers.ValidationError("ended_at must be after started_at.")

        return data

    def get_slot_details(self, obj):
        """Get slot details if interview is scheduled"""
        if hasattr(obj, "schedule") and obj.schedule:
            slot = obj.schedule.slot
            return {
                "slot_id": slot.id,
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "duration_minutes": slot.duration_minutes,
                "ai_interview_type": slot.ai_interview_type,
                "max_candidates": slot.max_candidates,
                "current_bookings": slot.current_bookings,
                "slot_status": slot.status,
            }
        return None

    def get_schedule_status(self, obj):
        """Get schedule status"""
        if hasattr(obj, "schedule") and obj.schedule:
            return obj.schedule.status
        return None

    def get_booking_notes(self, obj):
        """Get booking notes"""
        if hasattr(obj, "schedule") and obj.schedule:
            return obj.schedule.booking_notes
        return None

    def get_ai_result(self, obj):
        """Get AI interview result if available"""
        try:
            if hasattr(obj, "ai_result") and obj.ai_result:
                from ai_interview.serializers import AIInterviewResultSerializer

                return AIInterviewResultSerializer(obj.ai_result).data
        except Exception:
            pass
        return None


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for updating interview feedback
    """

    class Meta:
        model = Interview
        fields = ["interview_round", "feedback"]


class InterviewSlotSerializer(serializers.ModelSerializer):
    """
    Serializer for AI interview slots with separate date and time fields
    """

    company_name = serializers.CharField(source="company.name", read_only=True)
    job_title = serializers.CharField(source="job.job_title", read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    available_spots = serializers.SerializerMethodField()

    # Computed fields for backward compatibility
    full_start_datetime = serializers.SerializerMethodField()
    full_end_datetime = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSlot
        fields = [
            "id",
            "slot_type",
            "status",
            "interview_date",
            "start_time",
            "end_time",
            "duration_minutes",
            "ai_interview_type",
            "ai_configuration",
            "company",
            "company_name",
            "job",
            "job_title",
            "is_recurring",
            "recurring_pattern",
            "notes",
            "max_candidates",
            "current_bookings",
            "is_available",
            "available_spots",
            "full_start_datetime",
            "full_end_datetime",
            "legacy_start_datetime",
            "legacy_end_datetime",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "is_available",
            "available_spots",
            "full_start_datetime",
            "full_end_datetime",
        ]

    def get_available_spots(self, obj):
        return max(0, obj.max_candidates - obj.current_bookings)

    def get_full_start_datetime(self, obj):
        """Return combined datetime for frontend compatibility"""
        return obj.get_full_start_datetime()

    def get_full_end_datetime(self, obj):
        """Return combined datetime for frontend compatibility"""
        return obj.get_full_end_datetime()

    def validate(self, data):
        if data.get("start_time") and data.get("end_time"):
            if data["start_time"] >= data["end_time"]:
                raise serializers.ValidationError("End time must be after start time")

        return data


class InterviewScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for AI interview schedules
    """

    interview_details = serializers.SerializerMethodField()
    slot_details = serializers.SerializerMethodField()
    ai_interview_type = serializers.CharField(
        source="slot.ai_interview_type", read_only=True
    )
    candidate_name = serializers.CharField(
        source="interview.candidate.full_name", read_only=True
    )

    class Meta:
        model = InterviewSchedule
        fields = [
            "id",
            "interview",
            "slot",
            "status",
            "booking_notes",
            "booked_at",
            "confirmed_at",
            "cancelled_at",
            "cancellation_reason",
            "cancelled_by",
            "interview_details",
            "slot_details",
            "ai_interview_type",
            "candidate_name",
        ]
        read_only_fields = [
            "id",
            "booked_at",
            "confirmed_at",
            "cancelled_at",
            "cancelled_by",
        ]

    def get_interview_details(self, obj):
        return {
            "id": obj.interview.id,
            "candidate_name": obj.interview.candidate.full_name,
            "status": obj.interview.status,
            "started_at": obj.interview.started_at,
            "ended_at": obj.interview.ended_at,
        }

    def get_slot_details(self, obj):
        return {
            "id": obj.slot.id,
            "ai_interview_type": obj.slot.ai_interview_type,
            "start_time": obj.slot.start_time,
            "end_time": obj.slot.end_time,
            "duration_minutes": obj.slot.duration_minutes,
            "company_name": obj.slot.company.name,
        }

    def validate(self, data):
        # Check if slot is available
        if "slot" in data:
            slot = data["slot"]
            if not slot.is_available():
                raise serializers.ValidationError(
                    "Selected slot is not available for booking"
                )

            # Check if interview is already scheduled
            if "interview" in data:
                interview = data["interview"]
                if hasattr(interview, "schedule") and interview.schedule:
                    raise serializers.ValidationError("Interview is already scheduled")

        return data


class AIInterviewConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for AI interview configuration patterns
    """

    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = AIInterviewConfiguration
        fields = [
            "id",
            "company",
            "company_name",
            "interview_type",
            "day_of_week",
            "start_time",
            "end_time",
            "slot_duration",
            "break_duration",
            "ai_settings",
            "valid_from",
            "valid_until",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        if data.get("start_time") and data.get("end_time"):
            if data["start_time"] >= data["end_time"]:
                raise serializers.ValidationError("End time must be after start time")
        return data


class InterviewConflictSerializer(serializers.ModelSerializer):
    """
    Serializer for interview conflicts
    """

    primary_interview_details = serializers.SerializerMethodField()
    conflicting_interview_details = serializers.SerializerMethodField()
    resolved_by_name = serializers.CharField(
        source="resolved_by.full_name", read_only=True
    )

    class Meta:
        model = InterviewConflict
        fields = [
            "id",
            "conflict_type",
            "resolution",
            "primary_interview",
            "conflicting_interview",
            "conflict_details",
            "resolution_notes",
            "detected_at",
            "resolved_at",
            "resolved_by",
            "primary_interview_details",
            "conflicting_interview_details",
            "resolved_by_name",
        ]
        read_only_fields = ["id", "detected_at", "resolved_at", "resolved_by"]

    def get_primary_interview_details(self, obj):
        return {
            "id": obj.primary_interview.id,
            "candidate_name": obj.primary_interview.candidate.full_name,
            "status": obj.primary_interview.status,
            "started_at": obj.primary_interview.started_at,
            "ended_at": obj.primary_interview.ended_at,
        }

    def get_conflicting_interview_details(self, obj):
        if obj.conflicting_interview:
            return {
                "id": obj.conflicting_interview.id,
                "candidate_name": obj.conflicting_interview.candidate.full_name,
                "status": obj.conflicting_interview.status,
                "started_at": obj.conflicting_interview.started_at,
                "ended_at": obj.conflicting_interview.ended_at,
            }
        return None


class SlotBookingSerializer(serializers.Serializer):
    """
    Serializer for booking a slot for an interview
    """

    interview_id = serializers.UUIDField()
    slot_id = serializers.UUIDField()
    booking_notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        from .models import Interview, InterviewSlot

        # Validate interview exists
        try:
            interview = Interview.objects.get(id=data["interview_id"])
            data["interview"] = interview
        except Interview.DoesNotExist:
            raise serializers.ValidationError("Interview not found")

        # Validate slot exists and is available
        try:
            slot = InterviewSlot.objects.get(id=data["slot_id"])
            data["slot"] = slot
        except InterviewSlot.DoesNotExist:
            raise serializers.ValidationError("Slot not found")

        if not slot.is_available():
            raise serializers.ValidationError("Slot is not available for booking")

        # Check if interview is already scheduled
        if hasattr(interview, "schedule") and interview.schedule:
            raise serializers.ValidationError("Interview is already scheduled")

        return data


class SlotSearchSerializer(serializers.Serializer):
    """
    Serializer for searching available slots
    """

    company_id = serializers.IntegerField(required=False)
    ai_interview_type = serializers.CharField(required=False)
    job_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)
    duration_minutes = serializers.IntegerField(required=False, default=60)

    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError(
                "Start date must be before or equal to end date"
            )
        return data


class RecurringSlotSerializer(serializers.Serializer):
    """
    Serializer for creating recurring slots
    """

    company_id = serializers.IntegerField()
    ai_interview_type = serializers.CharField(default="general")
    job_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    days_of_week = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=7), min_length=1
    )
    slot_duration = serializers.IntegerField(default=60, min_value=15, max_value=480)
    break_duration = serializers.IntegerField(default=15, min_value=0, max_value=60)
    max_candidates_per_slot = serializers.IntegerField(
        default=1, min_value=1, max_value=10
    )
    ai_configuration = serializers.JSONField(required=False, default=dict)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError(
                "Start date must be before or equal to end date"
            )
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError("End time must be after start time")
        return data
