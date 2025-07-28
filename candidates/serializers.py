# Updated serializers.py
from rest_framework import serializers
from candidates.models import Candidate
from utils.name_parser import parse_candidate_name
from resumes.models import Resume, extract_resume_fields


class CandidateSerializer(serializers.ModelSerializer):
    resume_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = [
            'id', 'recruiter', 'full_name', 'email', 'phone',
            'work_experience', 'domain', 'poc_email',
            'job_title', 'resume', 'resume_file_url', 'created_at',
        ]
        read_only_fields = fields

    def get_resume_file_url(self, obj):
        request = self.context.get('request')
        if obj.resume and obj.resume.file:
            return request.build_absolute_uri(obj.resume.file.url)
        return None


class CandidateListSerializer(serializers.ModelSerializer):
    resume_url = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = [
            "id", "full_name", "email", "phone", "status", "domain",
            "poc_email", "job_title","work_experience", "last_updated", "resume_url",
        ]

    def get_resume_url(self, obj):
        request = self.context.get("request")
        if obj.resume and obj.resume.file:
            return request.build_absolute_uri(obj.resume.file.url)
        return None
    
    def update(self, instance, validated_data):
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.email = validated_data.get('email', instance.email)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.work_experience = validated_data.get('work_experience', instance.work_experience)
        instance.domain = validated_data.get('domain', instance.domain)
        instance.poc_email = validated_data.get('poc_email', instance.poc_email)
        instance.job_title = validated_data.get('job_title', instance.job_title)
        instance.save()
        return instance


class CandidateCreateSerializer(serializers.ModelSerializer):
    resume_file = serializers.FileField(write_only=True)
    job_title = serializers.CharField(required=False, allow_blank=True, write_only=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    work_experience = serializers.IntegerField(required=False, allow_null=True)


    class Meta:
        model = Candidate
        fields = [
            'id', 'full_name', 'email', 'phone', 'work_experience', 'domain',
            'poc_email', 'job_title', 'resume_file',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        file = validated_data.pop('resume_file')
        user = self.context['request'].user

        temp_resume = Resume(user=user, file=file)
        temp_resume.save()
        parsed = extract_resume_fields(temp_resume.parsed_text)

        if not validated_data.get('full_name') and parsed.get('name'):
            validated_data['full_name'] = parse_candidate_name(parsed['name'])

        for f in ['email', 'phone', 'work_experience']:
            if not validated_data.get(f) and parsed.get(f):
                validated_data[f] = parsed[f]

        validated_data['resume'] = temp_resume
        validated_data['recruiter'] = user

        return Candidate.objects.create(**validated_data)

