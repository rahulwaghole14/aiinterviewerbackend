from django.db import models
from django.core.validators import MinValueValidator


class Domain(models.Model):
    """
    Domain/Technology area model for categorizing jobs and candidates
    """
    name = models.CharField(max_length=100, unique=True, help_text="Domain name (e.g., 'Python Development', 'React Frontend')")
    description = models.TextField(blank=True, help_text="Description of the domain")
    is_active = models.BooleanField(default=True, help_text="Whether this domain is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Domain"
        verbose_name_plural = "Domains"

    def __str__(self):
        return self.name


class Job(models.Model):
    class PositionLevel(models.TextChoices):
        IC = 'IC', 'Individual Contributor'
        MANAGER = 'Manager', 'Manager'

    job_title = models.CharField(max_length=255, db_index=True)
    company_name = models.CharField(max_length=255, db_index=True)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='jobs', help_text="Domain/technology area for this job", null=True, blank=True)
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
    
    job_description = models.TextField(blank=True, help_text="Detailed job description, responsibilities, requirements, etc.")
    jd_file = models.FileField(upload_to='job_descriptions/', null=True, blank=True)
    jd_link = models.URLField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        domain_name = self.domain.name if self.domain else "No Domain"
        return f"{self.job_title} at {self.company_name} ({domain_name})"
