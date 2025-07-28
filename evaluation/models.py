from django.db import models
from interviews.models import Interview
from candidates.models import Candidate

class Evaluation(models.Model):
    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, related_name="evaluation")
    overall_score = models.FloatField()
    traits = models.TextField(blank=True, null=True)
    suggestions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluation for {self.interview.candidate.full_name}"


class Feedback(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name="manual_feedbacks")
    reviewer_name = models.CharField(max_length=255)
    comments = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.reviewer_name} for {self.candidate.full_name}"
