from rest_framework import serializers
from candidates.models import Candidate
from utils.name_parser import parse_candidate_name
from resumes.models import Resume, extract_resume_fields
from jobs.models import Job
  
class CandidateSerializer(serializers.ModelSerializer):
    resume_file_url = serializers.SerializerMethodField()
    job_title = serializers.CharField(required=False, allow_blank=True, write_only=True) 

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

class CandidateCreateSerializer(serializers.ModelSerializer):
    resume_file = serializers.FileField(write_only=True)
    job = serializers.CharField(required=False, allow_blank=True,  write_only=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Candidate
        fields = [
            'id',
            'full_name', 'email', 'phone',
            'work_experience', 'domain', 'poc_email',
            'job', 'resume_file',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        file = validated_data.pop('resume_file')
        user = self.context['request'].user

        job_title = validated_data.pop('job', None)
        job = None
        if job_title:
            try:
                job = Job.objects.get(job_title=job_title)
            except Job.DoesNotExist:
                raise serializers.ValidationError({"job": f"Job '{job_title}' not found."})

        resume = Resume.objects.create(user=user, file=file)
        parsed = extract_resume_fields(resume.parsed_text)

        if not validated_data.get('full_name') and parsed.get('name'):
            cleaned_name = parse_candidate_name(parsed['name'])
            validated_data['full_name'] = cleaned_name

        for f in ['email', 'phone', 'work_experience']:
            if not validated_data.get(f) and parsed.get(f):
                validated_data[f] = parsed[f]

        validated_data['resume'] = resume
        validated_data['recruiter'] = user
        validated_data['job'] = job

        return Candidate.objects.create(**validated_data)


class CandidateListSerializer(serializers.ModelSerializer):
    job_title   = serializers.CharField(source='job.job_title', read_only=True)
    resume_url = serializers.SerializerMethodField()

    class Meta:
        model  = Candidate
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "status",
            "domain",
            "poc_email",
            "job_title",
            "last_updated",
            "resume_url",
        ]

    def get_resume_url(self, obj):
            request = self.context.get("request")
            if obj.resume and obj.resume.file:
                return request.build_absolute_uri(obj.resume.file.url)
            return None
