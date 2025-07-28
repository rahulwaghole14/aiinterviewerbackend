from django.db import models

class Role:
    ADMIN = 'Admin'
    SOURCING_PARTNER = 'Sourcing Partner'
    RECRUITER = 'Recruiter'

    CHOICES = [
        (ADMIN, 'Admin'),
        (SOURCING_PARTNER, 'Sourcing Partner'),
        (RECRUITER, 'Recruiter'),
    ]

class UserData(models.Model):
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    company_name = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=Role.CHOICES)
    linkedin_url = models.URLField(blank=True, null=True)
    permission_granted = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.email}"
