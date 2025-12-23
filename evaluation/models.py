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
    evaluation_pdf = models.FileField(upload_to='proctoring_pdfs/', null=True, blank=True, help_text="AI evaluation PDF report stored in database")

    class Meta:
        indexes = [
            models.Index(fields=['interview', 'created_at']),
            models.Index(fields=['overall_score', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Evaluation for {self.interview.candidate.full_name}"


class ProctoringPDF(models.Model):
    """
    Separate table to store proctoring PDF URLs
    One-to-one relationship with Interview
    """
    interview = models.OneToOneField(
        Interview, on_delete=models.CASCADE, related_name="proctoring_pdf", db_index=True
    )
    gcs_url = models.URLField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text="Google Cloud Storage public URL for proctoring PDF"
    )
    local_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Local file path for proctoring PDF (backup)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['interview', 'created_at']),
            models.Index(fields=['gcs_url']),
        ]
        ordering = ['-created_at']
        verbose_name = "Proctoring PDF"
        verbose_name_plural = "Proctoring PDFs"

    def __str__(self):
        return f"Proctoring PDF for Interview {self.interview.id}"


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
