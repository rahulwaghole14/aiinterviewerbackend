from django.db import models
from authapp.models import CustomUser
from jobs.models import Job, Domain
from resumes.models import Resume


class CandidateDraft(models.Model):
    """
    Temporary storage for candidate data before final submission
    Supports the step-by-step candidate creation flow
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        EXTRACTED = "extracted", "Data Extracted"
        VERIFIED = "verified", "Verified"
        SUBMITTED = "submitted", "Submitted"

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="candidate_drafts"
    )
    domain = models.CharField(max_length=100, help_text="Domain/technology area")
    role = models.CharField(max_length=100, help_text="Job role/position")
    resume_file = models.FileField(
        upload_to="candidate_drafts/", help_text="Uploaded resume file"
    )

    # Extracted data from resume
    extracted_data = models.JSONField(
        default=dict, help_text="Data extracted from resume"
    )

    # User-verified/updated data
    verified_data = models.JSONField(default=dict, help_text="User-verified data")

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Draft {self.id} - {self.domain}/{self.role} ({self.status})"

    class Meta:
        ordering = ["-created_at"]


class Candidate(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED", "Interview Scheduled"
        INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED", "Interview Completed"
        AI_EVALUATED = "AI_EVALUATED", "AI Evaluated"
        MANUAL_EVALUATED = "MANUAL_EVALUATED", "Manual Evaluated"
        AI_MANUAL_EVALUATED = "AI_MANUAL_EVALUATED", "AI + Manual Evaluated"
        EVALUATED = "EVALUATED", "Evaluated"
        REQUIRES_ACTION = "REQUIRES_ACTION", "Requires Action"
        PENDING_SCHEDULING = "PENDING_SCHEDULING", "Pending Scheduling"
        BR_IN_PROCESS = "BR_IN_PROCESS", "BR In Process"
        BR_EVALUATED = "BR_EVALUATED", "BR Evaluated"
        INTERNAL_INTERVIEWS = "INTERNAL_INTERVIEWS", "Internal Interviews"
        OFFERED = "OFFERED", "Offered"
        HIRED = "HIRED", "Hired"
        REJECTED = "REJECTED", "Rejected"
        OFFER_REJECTED = "OFFER_REJECTED", "Offer Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    recruiter = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="candidates"
    )
    job = models.ForeignKey(
        Job, on_delete=models.SET_NULL, null=True, blank=True, related_name="candidates"
    )
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="candidates",
        null=True,
        blank=True,
    )
    domain = models.CharField(
        max_length=100, blank=True, help_text="Domain/technology area"
    )

    full_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    work_experience = models.PositiveIntegerField(null=True, blank=True)
    poc_email = models.EmailField(null=True, blank=True)

    status = models.CharField(
        max_length=40,
        choices=Status.choices,
        default=Status.NEW,
    )
    last_updated = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name or self.email or f"Candidate {self.pk}"
