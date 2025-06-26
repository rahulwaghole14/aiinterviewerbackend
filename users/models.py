from django.contrib.auth.models import AbstractUser
from django.db import models

ROLES = [
    ('HR', 'HR'),
    ('Hiring Manager', 'Hiring Manager'),
    ('Recruiter', 'Recruiter'),
    ('Talent Acquisition Specialist', 'Talent Acquisition Specialist'),
    ('Technical Interviewer', 'Technical Interviewer'),
    ('Team Lead', 'Team Lead'),
    ('Department Head', 'Department Head'),
    ('Project Manager', 'Project Manager'),
    ('CTO', 'CTO'),
    ('Admin', 'Admin'),
    ('Others', 'Others'),
]

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, choices=ROLES, default='Others')
