from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    COMPANY = 'COMPANY', 'Company'
    HIRING_AGENCY = 'HIRING_AGENCY', 'Hiring Agency'
    RECRUITER = 'RECRUITER', 'Recruiter'
    HR = 'HR', 'HR'
    TALENT_ACQUISITION = 'TALENT_ACQUISITION', 'Talent Acquisition Specialist'
    TECHNICAL_INTERVIEWER = 'TECHNICAL_INTERVIEWER', 'Technical Interviewer'
    TEAM_LEAD = 'TEAM_LEAD', 'Team Lead'
    DEPARTMENT_HEAD = 'DEPARTMENT_HEAD', 'Department Head'
    PROJECT_MANAGER = 'PROJECT_MANAGER', 'Project Manager'
    CTO = 'CTO', 'CTO'
    OTHERS = 'OTHERS', 'Others'

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.OTHERS)
    # Add company relationship for proper hierarchy
    company = models.ForeignKey('companies.Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def get_company_name(self):
        """Get company name from company relationship or fallback to company_name field"""
        if self.company:
            return self.company.name
        return self.company_name or "No Company"
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == Role.ADMIN
    
    def is_company(self):
        """Check if user is company user"""
        return self.role == Role.COMPANY
    
    def is_hiring_agency(self):
        """Check if user is hiring agency"""
        return self.role == Role.HIRING_AGENCY
    
    def is_recruiter(self):
        """Check if user is recruiter"""
        return self.role == Role.RECRUITER
