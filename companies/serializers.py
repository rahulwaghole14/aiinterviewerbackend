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
    username = serializers.CharField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    password = serializers.CharField(write_only=True)
    company_id = serializers.IntegerField()

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            role=Role.RECRUITER
        )
        company = Company.objects.get(id=validated_data['company_id'])
        return Recruiter.objects.create(user=user, company=company)

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
