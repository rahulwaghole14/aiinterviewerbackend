from rest_framework import serializers
from .models import Domain, Job
from companies.models import Company


class DomainSerializer(serializers.ModelSerializer):
    """Serializer for Domain model"""

    class Meta:
        model = Domain
        fields = ["id", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DomainListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing domains"""

    class Meta:
        model = Domain
        fields = ["id", "name", "description", "is_active"]


class JobSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source="domain.name", read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "job_title",
            "company_name",
            "domain",
            "domain_name",
            "spoc_email",
            "hiring_manager_email",
            "current_team_size_info",
            "number_to_hire",
            "position_level",
            "current_process",
            "tech_stack_details",
            "coding_language",
            "job_description",
            "jd_file",
            "jd_link",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_domain(self, value):
        """Validate that the domain is active"""
        if not value.is_active:
            raise serializers.ValidationError(
                "Cannot assign an inactive domain to a job."
            )
        return value
    
    def validate_coding_language(self, value):
        """Ensure coding_language is always uppercase"""
        if value:
            value = value.upper()
            # Validate against allowed choices
            allowed_languages = ['PYTHON', 'JAVASCRIPT', 'JAVA', 'PHP', 'RUBY', 'CSHARP', 'SQL', 'C', 'CPP', 'GO', 'HTML']
            if value not in allowed_languages:
                raise serializers.ValidationError(
                    f"Invalid coding language: {value}. Must be one of: {', '.join(allowed_languages)}"
                )
        return value
    
    def create(self, validated_data):
        """Create job and automatically create/update Company record"""
        company_name = validated_data.get('company_name', '').strip()
        
        # Create or update Company record if company_name is provided
        if company_name:
            company, created = Company.objects.get_or_create(
                name=company_name,
                defaults={
                    'description': f'Company created automatically from job: {validated_data.get("job_title", "")}',
                    'is_active': True,
                }
            )
            # Update description if company already exists (to keep it active)
            if not created:
                company.is_active = True
                company.save()
        
        # Create the job
        job = Job.objects.create(**validated_data)
        return job
    
    def update(self, instance, validated_data):
        """Update job and automatically create/update Company record"""
        company_name = validated_data.get('company_name', '').strip()
        
        # Create or update Company record if company_name is provided
        if company_name:
            company, created = Company.objects.get_or_create(
                name=company_name,
                defaults={
                    'description': f'Company created automatically from job: {validated_data.get("job_title", instance.job_title)}',
                    'is_active': True,
                }
            )
            # Update description if company already exists (to keep it active)
            if not created:
                company.is_active = True
                company.save()
        
        # Update the job
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class JobTitleSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source="domain.name", read_only=True)

    class Meta:
        model = Job
        fields = ["id", "job_title", "domain_name"]
