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
    company = models.ForeignKey('companies.Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='hiring_agencies')
    company_name = models.CharField(max_length=255, blank=True, null=True)  # Keep for backward compatibility during migration
    linkedin_url = models.URLField(blank=True)
    permission_granted = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey('authapp.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.email} - {self.role}"
    
    def get_company_name(self):
        """Get company name from company relationship or fallback to company_name field"""
        if self.company:
            return self.company.name
        return self.company_name or "No Company"
