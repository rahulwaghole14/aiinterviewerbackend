from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import CustomUser, Role


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'full_name', 'company_name', 'role', 'password']
        extra_kwargs = {
            'username': {'read_only': True}  # Automatically set to email
        }

    def validate_role(self, value):
        if value not in dict(Role.CHOICES):
            raise serializers.ValidationError("Invalid role selected.")
        return value

    def create(self, validated_data):
        try:
            validated_data['username'] = validated_data['email']
            return CustomUser.objects.create_user(**validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'error': e.messages})
        except Exception as e:
            raise serializers.ValidationError({'error': str(e)})


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'company_name', 'role', 'username']
        read_only_fields = ['id', 'email', 'role', 'username']
