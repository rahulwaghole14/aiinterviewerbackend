from rest_framework import serializers
from .models import Domain, Job


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


class JobTitleSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source="domain.name", read_only=True)

    class Meta:
        model = Job
        fields = ["id", "job_title", "domain_name"]
