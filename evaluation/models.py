from django.db import models
from interviews.models import Interview
from candidates.models import Candidate


class Evaluation(models.Model):
    interview = models.OneToOneField(
        Interview, on_delete=models.CASCADE, related_name="evaluation", db_index=True
    )
    overall_score = models.FloatField(db_index=True)
    traits = models.TextField(blank=True, null=True)
    suggestions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    details = models.JSONField(blank=True, null=True, default=dict, help_text="Extended AI evaluation details, proctoring warnings, and statistics.")

    class Meta:
        indexes = [
            models.Index(fields=['interview', 'created_at']),
            models.Index(fields=['overall_score', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Evaluation for {self.interview.candidate.full_name}"


class Feedback(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    interview = models.ForeignKey(
        Interview, on_delete=models.CASCADE, related_name="manual_feedbacks"
    )
    reviewer_name = models.CharField(max_length=255)
    comments = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.reviewer_name} for {self.candidate.full_name}"
