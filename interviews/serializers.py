# interviews/serializers.py
from datetime import time

from rest_framework import serializers
from .models import Interview


class InterviewSerializer(serializers.ModelSerializer):
    """
    Main read / write serializer for Interview.
    Adds two read‑only convenience fields:
      • candidate_name – Candidate.full_name
      • job_title       – Job.job_title

    Includes a custom validate() that restricts the scheduled
    window to **08:00 – 22:00 UTC** for both start and end times.
    """
    candidate_name = serializers.CharField(
        source="candidate.full_name", read_only=True
    )
    job_title = serializers.CharField(
        source="job.job_title", read_only=True
    )

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
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "candidate_name",
            "job_title",
        ]

    # ──────────────────────────────────────────────────────────
    # Custom validation: 08:00 – 22:00 UTC scheduling window
    # ──────────────────────────────────────────────────────────
    def validate(self, data):
        """
        Ensure both started_at and ended_at fall between 08:00 and 22:00 UTC.

        If this is a partial update (PATCH), keep the existing
        instance’s values where the client omitted a field.
        """
        start_dt = data.get("started_at") or getattr(self.instance, "started_at", None)
        end_dt   = data.get("ended_at")   or getattr(self.instance, "ended_at", None)

        if not start_dt or not end_dt:
            raise serializers.ValidationError(
                "Both 'started_at' and 'ended_at' must be provided."
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
