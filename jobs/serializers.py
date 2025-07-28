from rest_framework import serializers
from .models import Job

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['created_at']

    def validate(self, attrs):
        jd_file = attrs.get('jd_file')
        jd_link = attrs.get('jd_link')

        if not jd_file and not jd_link:
            raise serializers.ValidationError("Either a JD file or a JD link must be provided.")
        return attrs

    def validate_jd_file(self, value):
        if value:
            valid_extensions = ['.pdf', '.doc', '.docx']
            if not any(str(value).lower().endswith(ext) for ext in valid_extensions):
                raise serializers.ValidationError("JD file must be a PDF, DOC, or DOCX.")
        return value

class JobTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['job_title']
