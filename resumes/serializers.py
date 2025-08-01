from rest_framework import serializers
from .models import Resume

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'file', 'parsed_text', 'uploaded_at']
        read_only_fields = ['parsed_text', 'uploaded_at']

class BulkResumeSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        max_length=10,  # Limit to 10 files at once
        help_text="Upload up to 10 resume files (PDF/DOCX)"
    )

class ResumeProcessingResultSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    filename = serializers.CharField()
    resume_id = serializers.UUIDField(required=False)
    error_message = serializers.CharField(required=False)
    extracted_data = serializers.DictField(required=False)
