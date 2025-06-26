from django.db import models

class Job(models.Model):
    POSITION_LEVEL_CHOICES = [
        ('IC', 'Individual Contributor'),
        ('Manager', 'Manager'),
    ]

    job_title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    spoc_email = models.EmailField()
    hiring_manager_email = models.EmailField()
    current_team_size = models.CharField(max_length=50)
    number_to_hire = models.PositiveIntegerField()
    position_level = models.CharField(max_length=50, choices=POSITION_LEVEL_CHOICES)
    current_process = models.TextField(blank=True)
    tech_stack_details = models.TextField()
    jd_file = models.FileField(upload_to='job_descriptions/', null=True, blank=True)
    jd_link = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.job_title
