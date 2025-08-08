from rest_framework import serializers
from .models import Company, Recruiter
from authapp.models import CustomUser, Role

class CompanySerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'email', 'password', 'description', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        company = Company.objects.create(**validated_data)
        if password:
            company.password = password
            company.save()
        return company

class RecruiterSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Recruiter
        fields = ['id', 'user', 'full_name', 'email', 'company', 'is_active']

class RecruiterCreateSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField()
    full_name = serializers.CharField()
    password = serializers.CharField(write_only=True)
    company_id = serializers.IntegerField(required=False)
    company_name = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    linkedin_url = serializers.URLField(required=False, allow_blank=True)

    def validate(self, data):
        # If username is not provided, use email as username
        if not data.get('username'):
            data['username'] = data['email']
        
        # If company_id is not provided, try to find company by name
        if not data.get('company_id') and data.get('company_name'):
            try:
                company = Company.objects.get(name=data['company_name'])
                data['company_id'] = company.id
            except Company.DoesNotExist:
                # Create company if it doesn't exist
                company = Company.objects.create(
                    name=data['company_name'],
                    description=f"Company created for recruiter {data['full_name']}",
                    is_active=True
                )
                data['company_id'] = company.id
        
        return data

    def create(self, validated_data):
        # Extract fields
        username = validated_data['username']
        email = validated_data['email']
        full_name = validated_data['full_name']
        password = validated_data['password']
        company_id = validated_data['company_id']
        
        # Create user
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            full_name=full_name,
            password=password,
            role=Role.RECRUITER
        )
        
        # Get company
        company = Company.objects.get(id=company_id)
        
        # Create recruiter
        recruiter = Recruiter.objects.create(user=user, company=company)
        
        return recruiter

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'username': instance.user.username,
            'email': instance.user.email,
            'full_name': instance.user.full_name,
            'role': instance.user.role,
            'company': instance.company.name,
            'is_active': instance.is_active
        }
