# interviews/serializers.py
from datetime import time, datetime, timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import (
    Interview, InterviewSlot, InterviewSchedule, 
    InterviewerAvailability, InterviewConflict
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
    candidate_name = serializers.CharField(
        source="candidate.full_name", read_only=True
    )
    job_title = serializers.CharField(
        source="job.job_title", read_only=True
    )
    is_scheduled = serializers.BooleanField(read_only=True)
    interviewer_name = serializers.CharField(source='interviewer.full_name', read_only=True)

    class Meta:
        model  = Interview
        fields = [
            "id",
            "candidate", "candidate_name",
            # "job",
            "job_title",
            "status",
            "interview_round", "feedback",
            "started_at", "ended_at",
            "video_url",
            "created_at", "updated_at",
            "is_scheduled",
            "interviewer_name",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "candidate_name",
            "job_title",
            "is_scheduled",
            "interviewer_name",
        ]
        extra_kwargs = {
            'candidate': {'required': False},
            'started_at': {'required': False},
            'ended_at': {'required': False},
            'status': {'required': False},
            'interview_round': {'required': False},
            'feedback': {'required': False},
            'video_url': {'required': False},
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
        # Only validate time constraints if we're updating time fields
        if 'started_at' in data or 'ended_at' in data:
            start_dt = data.get("started_at") or getattr(self.instance, "started_at", None)
            end_dt   = data.get("ended_at")   or getattr(self.instance, "ended_at", None)

            if not start_dt or not end_dt:
                raise serializers.ValidationError(
                    "Both 'started_at' and 'ended_at' must be provided when updating time fields."
                )

            # Time window bounds (24‑hour clock, UTC)
            min_time = time(8, 0)   # 08:00
            max_time = time(22, 0)  # 22:00

            start_t = start_dt.time()
            end_t   = end_dt.time()

            if not (min_time <= start_t <= max_time):
                raise serializers.ValidationError(
                    "started_at must be between 08:00 and 22:00 UTC."
                )
            if not (min_time <= end_t <= max_time):
                raise serializers.ValidationError(
                    "ended_at must be between 08:00 and 22:00 UTC."
                )
            if end_dt <= start_dt:
                raise serializers.ValidationError(
                    "ended_at must be after started_at."
                )

        return data


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    """
    Used exclusively by the /api/interviews/<id>/feedback/ PATCH endpoint.
    Allows admin to update interview_round and feedback text.
    """
    class Meta:
        model  = Interview
        fields = ["interview_round", "feedback"]


# ──────────────────────────────────────────────────────────
# Interview Slot Management Serializers
# ──────────────────────────────────────────────────────────

class InterviewSlotSerializer(serializers.ModelSerializer):
    """
    Serializer for interview slots
    """
    interviewer_name = serializers.CharField(source='interviewer.full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    job_title = serializers.CharField(source='job.job_title', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    available_spots = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSlot
        fields = [
            'id', 'slot_type', 'status', 'start_time', 'end_time', 'duration_minutes',
            'interviewer', 'interviewer_name', 'company', 'company_name', 'job', 'job_title',
            'is_recurring', 'recurring_pattern', 'notes', 'max_candidates', 'current_bookings',
            'is_available', 'available_spots', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_available', 'available_spots']

    def get_available_spots(self, obj):
        """Calculate available spots in the slot"""
        return max(0, obj.max_candidates - obj.current_bookings)

    def validate(self, data):
        """Additional validation for slot creation"""
        # Ensure slot is in the future
        if 'start_time' in data and data['start_time'] <= timezone.now():
            raise serializers.ValidationError("Slot start time must be in the future")
        
        return data


class InterviewScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for interview schedules
    """
    interview_details = serializers.SerializerMethodField()
    slot_details = serializers.SerializerMethodField()
    interviewer_name = serializers.CharField(source='slot.interviewer.full_name', read_only=True)
    candidate_name = serializers.CharField(source='interview.candidate.full_name', read_only=True)

    class Meta:
        model = InterviewSchedule
        fields = [
            'id', 'interview', 'slot', 'status', 'booking_notes',
            'booked_at', 'confirmed_at', 'cancelled_at',
            'cancellation_reason', 'cancelled_by',
            'interview_details', 'slot_details', 'interviewer_name', 'candidate_name'
        ]
        read_only_fields = ['id', 'booked_at', 'confirmed_at', 'cancelled_at', 'cancelled_by']

    def get_interview_details(self, obj):
        """Get interview details"""
        return {
            'id': obj.interview.id,
            'candidate_name': obj.interview.candidate.full_name,
            'status': obj.interview.status,
            'interview_round': obj.interview.interview_round
        }

    def get_slot_details(self, obj):
        """Get slot details"""
        return {
            'id': obj.slot.id,
            'start_time': obj.slot.start_time,
            'end_time': obj.slot.end_time,
            'interviewer_name': obj.slot.interviewer.full_name
        }

    def validate(self, data):
        """Validate schedule creation"""
        interview = data.get('interview')
        slot = data.get('slot')
        
        if interview and slot:
            # Check if interview already has a schedule
            if hasattr(interview, 'schedule'):
                raise serializers.ValidationError("Interview already has a schedule")
            
            # Check if slot is available
            if not slot.is_available():
                raise serializers.ValidationError("Selected slot is not available")
            
            # Check if candidate is available (no overlapping interviews)
            candidate_conflicts = InterviewSchedule.objects.filter(
                interview__candidate=interview.candidate,
                slot__start_time__lt=slot.end_time,
                slot__end_time__gt=slot.start_time,
                status__in=['pending', 'confirmed']
            ).exists()
            
            if candidate_conflicts:
                raise serializers.ValidationError("Candidate has a conflicting interview at this time")
        
        return data


class InterviewerAvailabilitySerializer(serializers.ModelSerializer):
    """
    Serializer for interviewer availability patterns
    """
    interviewer_name = serializers.CharField(source='interviewer.full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = InterviewerAvailability
        fields = [
            'id', 'interviewer', 'interviewer_name', 'company', 'company_name',
            'day_of_week', 'start_time', 'end_time', 'slot_duration', 'break_duration',
            'is_available', 'max_slots_per_day', 'valid_from', 'valid_until',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InterviewConflictSerializer(serializers.ModelSerializer):
    """
    Serializer for interview conflicts
    """
    primary_interview_details = serializers.SerializerMethodField()
    conflicting_interview_details = serializers.SerializerMethodField()
    resolved_by_name = serializers.CharField(source='resolved_by.full_name', read_only=True)

    class Meta:
        model = InterviewConflict
        fields = [
            'id', 'conflict_type', 'resolution', 'primary_interview', 'conflicting_interview',
            'conflict_details', 'resolution_notes', 'detected_at', 'resolved_at', 'resolved_by',
            'primary_interview_details', 'conflicting_interview_details', 'resolved_by_name'
        ]
        read_only_fields = ['id', 'detected_at', 'resolved_at', 'resolved_by']

    def get_primary_interview_details(self, obj):
        """Get primary interview details"""
        return {
            'id': obj.primary_interview.id,
            'candidate_name': obj.primary_interview.candidate.full_name,
            'started_at': obj.primary_interview.started_at,
            'ended_at': obj.primary_interview.ended_at
        }

    def get_conflicting_interview_details(self, obj):
        """Get conflicting interview details"""
        if obj.conflicting_interview:
            return {
                'id': obj.conflicting_interview.id,
                'candidate_name': obj.conflicting_interview.candidate.full_name,
                'started_at': obj.conflicting_interview.started_at,
                'ended_at': obj.conflicting_interview.ended_at
            }
        return None


# ──────────────────────────────────────────────────────────
# Slot Management Utility Serializers
# ──────────────────────────────────────────────────────────

class SlotBookingSerializer(serializers.Serializer):
    """
    Serializer for booking a slot for an interview
    """
    interview_id = serializers.UUIDField()
    slot_id = serializers.UUIDField()
    booking_notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """Validate slot booking"""
        from .models import Interview, InterviewSlot
        
        try:
            interview = Interview.objects.get(id=data['interview_id'])
            slot = InterviewSlot.objects.get(id=data['slot_id'])
        except (Interview.DoesNotExist, InterviewSlot.DoesNotExist):
            raise serializers.ValidationError("Invalid interview or slot ID")
        
        # Check if slot is available
        if not slot.is_available():
            raise serializers.ValidationError("Selected slot is not available")
        
        # Check if interview already has a schedule
        if hasattr(interview, 'schedule'):
            raise serializers.ValidationError("Interview already has a schedule")
        
        data['interview'] = interview
        data['slot'] = slot
        return data


class SlotSearchSerializer(serializers.Serializer):
    """
    Serializer for searching available slots
    """
    company_id = serializers.IntegerField(required=False)
    interviewer_id = serializers.IntegerField(required=False)
    job_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)
    duration_minutes = serializers.IntegerField(required=False, default=60)

    def validate(self, data):
        """Validate search parameters"""
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("Start date must be before end date")
        
        if 'start_time' in data and 'end_time' in data:
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("Start time must be before end time")
        
        return data


class RecurringSlotSerializer(serializers.Serializer):
    """
    Serializer for creating recurring slots
    """
    interviewer_id = serializers.IntegerField()
    company_id = serializers.IntegerField()
    job_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    days_of_week = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=7),
        min_length=1
    )
    slot_duration = serializers.IntegerField(default=60, min_value=15, max_value=480)
    break_duration = serializers.IntegerField(default=15, min_value=0, max_value=60)
    max_candidates_per_slot = serializers.IntegerField(default=1, min_value=1, max_value=10)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """Validate recurring slot creation"""
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("Start date must be before end date")
        
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("Start time must be before end time")
        
        # Validate days of week
        for day in data['days_of_week']:
            if day < 1 or day > 7:
                raise serializers.ValidationError("Invalid day of week")
        
        return data
