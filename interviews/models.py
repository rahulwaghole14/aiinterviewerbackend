# interviews/models.py
import uuid
from django.db import models
from django.utils import timezone
from candidates.models import Candidate
from jobs.models import Job


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

    def __str__(self):
        return f"Interview {self.id} — {self.candidate.full_name}"
