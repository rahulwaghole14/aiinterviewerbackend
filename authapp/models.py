from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.TextChoices):
    HR = 'HR', 'HR'
    HIRING_MANAGER = 'HIRING_MANAGER', 'Hiring Manager'
    RECRUITER = 'RECRUITER', 'Recruiter'
    TALENT_ACQUISITION = 'TALENT_ACQUISITION', 'Talent Acquisition Specialist'
    TECHNICAL_INTERVIEWER = 'TECHNICAL_INTERVIEWER', 'Technical Interviewer'
    TEAM_LEAD = 'TEAM_LEAD', 'Team Lead'
    DEPARTMENT_HEAD = 'DEPARTMENT_HEAD', 'Department Head'
    PROJECT_MANAGER = 'PROJECT_MANAGER', 'Project Manager'
    CTO = 'CTO', 'CTO'
    ADMIN = 'ADMIN', 'Admin'
    COMPANY = 'COMPANY', 'Company'  
    OTHERS = 'OTHERS', 'Others'

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.OTHERS)

    def __str__(self):
        return f"{self.username} ({self.role})"
