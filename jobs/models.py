from django.db import models
from django.core.validators import MinValueValidator


class Job(models.Model):
    class PositionLevel(models.TextChoices):
        IC = 'IC', 'Individual Contributor'
        MANAGER = 'Manager', 'Manager'

    job_title = models.CharField(max_length=255, db_index=True)
    company_name = models.CharField(max_length=255, db_index=True)
    spoc_email = models.EmailField()
    hiring_manager_email = models.EmailField()
    
    current_team_size_info = models.CharField(max_length=50, blank=True)
    number_to_hire = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    position_level = models.CharField(
        max_length=50,
        choices=PositionLevel.choices
    )

    current_process = models.TextField(blank=True)
    tech_stack_details = models.TextField()
    
    jd_file = models.FileField(upload_to='job_descriptions/', null=True, blank=True)
    jd_link = models.URLField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"
