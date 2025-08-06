# from django.contrib.auth.models import AbstractUser
# from django.db import models

# class Role:
#     HR = 'HR'
#     HIRING_MANAGER = 'Hiring Manager'
#     RECRUITER = 'Recruiter'
#     TALENT_ACQUISITION = 'Talent Acquisition Specialist'
#     TECHNICAL_INTERVIEWER = 'Technical Interviewer'
#     TEAM_LEAD = 'Team Lead'
#     DEPARTMENT_HEAD = 'Department Head'
#     PROJECT_MANAGER = 'Project Manager'
#     CTO = 'CTO'
#     ADMIN = 'Admin'
#     OTHERS = 'Others'

#     CHOICES = [
#         (HR, 'HR'),
#         (HIRING_MANAGER, 'Hiring Manager'),
#         (RECRUITER, 'Recruiter'),
#         (TALENT_ACQUISITION, 'Talent Acquisition Specialist'),
#         (TECHNICAL_INTERVIEWER, 'Technical Interviewer'),
#         (TEAM_LEAD, 'Team Lead'),
#         (DEPARTMENT_HEAD, 'Department Head'),
#         (PROJECT_MANAGER, 'Project Manager'),
#         (CTO, 'CTO'),
#         (ADMIN, 'Admin'),
#         (OTHERS, 'Others'),
#     ]

# class CustomUser(AbstractUser):
#     full_name = models.CharField(max_length=100)
#     company_name = models.CharField(max_length=100)
#     role = models.CharField(max_length=50, choices=Role.CHOICES, default=Role.OTHERS)

#     def __str__(self):
#         return f"{self.username} - {self.role}"
