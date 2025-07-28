from django.db import models
from authapp.models import CustomUser

class Company(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Recruiter(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='recruiter_profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='recruiters')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.full_name} ({self.company.name})"
