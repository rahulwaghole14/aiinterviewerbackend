from rest_framework import serializers
from .models import Job

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            'job_title',
            'company_name',
            'spoc_email',
            'hiring_manager_email',
            'current_team_size_info',
            'number_to_hire',
            'position_level',
            'tech_stack_details'
        ]
        read_only_fields = ['created_at']

class JobTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['job_title']
