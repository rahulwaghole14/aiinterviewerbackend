from django.db import models
from users.models import CustomUser
from jobs.models import Job
from resumes.models import Resume


class Candidate(models.Model):
    recruiter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='candidates')
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, related_name='candidates')

    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    work_experience = models.PositiveIntegerField(null=True, blank=True)

    domain = models.CharField(max_length=100, blank=True)
    poc_email = models.EmailField(null=True, blank=True)

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='candidates')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
