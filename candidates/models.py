from django.db import models
from authapp.models import CustomUser
from jobs.models import Job
from resumes.models import Resume


class Candidate(models.Model):
    class Status(models.TextChoices):
        NEW                 = "NEW",               "New"
        REQUIRES_ACTION     = "REQUIRES_ACTION",   "Requires Action"
        PENDING_SCHEDULING  = "PENDING_SCHEDULING","Pending Scheduling"
        BR_IN_PROCESS       = "BR_IN_PROCESS",     "BR In Process"
        BR_EVALUATED        = "BR_EVALUATED",      "BR Evaluated"
        INTERNAL_INTERVIEWS = "INTERNAL_INTERVIEWS","Internal Interviews"
        OFFERED             = "OFFERED",           "Offered"
        HIRED               = "HIRED",             "Hired"
        REJECTED            = "REJECTED",          "Rejected"
        OFFER_REJECTED      = "OFFER_REJECTED",    "Offer Rejected"
        CANCELLED           = "CANCELLED",         "Cancelled"

    status = models.CharField(
        max_length=40,
        choices=Status.choices,
        default=Status.NEW,
    )




    recruiter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='candidates')
    job_title = models.CharField(max_length=255, blank=True)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='candidates')

    full_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    work_experience = models.PositiveIntegerField(null=True, blank=True)
    domain = models.CharField(max_length=100, blank=True)
    poc_email = models.EmailField(null=True, blank=True)

    status = models.CharField(max_length=40, choices=Status.choices, default=Status.NEW)
    last_updated = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name or self.email or f"Candidate {self.pk}"
