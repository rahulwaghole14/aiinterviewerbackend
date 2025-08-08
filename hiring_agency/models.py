from django.db import models

class Role:
    ADMIN = 'Admin'
    COMPANY = 'Company'
    RECRUITER = 'Recruiter'
    HIRING_AGENCY = 'Hiring Agency'

    CHOICES = [
        (ADMIN, 'Admin'),
        (COMPANY, 'Company'),
        (RECRUITER, 'Recruiter'),
        (HIRING_AGENCY, 'Hiring Agency'),
    ]

    PUBLIC_CHOICES = [
        (COMPANY, 'Company'),
        (RECRUITER, 'Recruiter'),
        (HIRING_AGENCY, 'Hiring Agency'),
    ]

class UserData(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    role = models.CharField(max_length=50, choices=Role.CHOICES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    linkedin_url = models.URLField(blank=True)
    permission_granted = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey('authapp.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.email} - {self.role}"
