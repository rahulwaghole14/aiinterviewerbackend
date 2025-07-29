import uuid
from django.db import models
from candidates.models import Candidate
from jobs.models import Job

class Interview(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        REQUIRES_ACTION = "REQUIRES_ACTION", "Requires Action"
        PENDING_SCHEDULING = "PENDING_SCHEDULING", "Pending Scheduling"
        BR_IN_PROCESS = "BR_IN_PROCESS", "BR In Process"
        SCHEDULED = "SCHEDULED", "Scheduled"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"
        ON_HOLD = "ON_HOLD", "On Hold"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="interviews")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="interviews")
    interview_round = models.CharField(max_length=255)
    scheduled_at = models.DateTimeField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.NEW)
    feedback = models.TextField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.candidate.full_name} - {self.interview_round}"
