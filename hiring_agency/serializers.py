from rest_framework import serializers
from .models import UserData, Role
import re
from datetime import date


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserData
        fields = '__all__'
        read_only_fields = ['created_by']

    def validate_email(self, value):
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Invalid email format.")
        return value

    def validate_name(self, value, field_name):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(f"{field_name} must be at least 2 characters long.")
        return value

    def validate_first_name(self, value):
        return self.validate_name(value, "First name")

    def validate_last_name(self, value):
        return self.validate_name(value, "Last name")

    def validate_phone_number(self, value):
        cleaned = re.sub(r"[^\d+]", "", value)
        if not re.match(r'^\+?\d{10,15}$', cleaned):
            raise serializers.ValidationError("Enter a valid international phone number (10–15 digits, optional '+').")
        return value

    def validate_role(self, value):
        valid_roles = [r[0] for r in Role.PUBLIC_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(f"Role must be one of: {', '.join(valid_roles)}")
        return value

    def validate_linkedin_url(self, value):
        if value and not value.startswith("http"):
            raise serializers.ValidationError("LinkedIn URL must be a valid link.")
        return value

    def validate_company_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Company name cannot be empty.")
        return value

    def validate_permission_granted(self, value):
        if value > date.today():
            raise serializers.ValidationError("Permission granted date cannot be in the future.")
        return value

    def validate(self, data):
        request = self.context.get('request')
        request_user = request.user if request else None

        if not request_user:
            return data  # Skip role validation if unauthenticated (shouldn't happen with permission_classes)

        creator_role = request_user.role.upper()
        new_role = data.get('role', '').upper()

        if new_role in ['RECRUITER', 'HIRING AGENCY']:
            if creator_role not in ['ADMIN', 'COMPANY']:
                raise serializers.ValidationError(
                    f"{creator_role} is not allowed to create users with role {new_role}."
                )
        elif new_role in ['ADMIN', 'COMPANY']:
            if creator_role != 'ADMIN' and creator_role != 'SUPER_ADMIN':
                raise serializers.ValidationError(
                    f"Only ADMIN or SUPER_ADMIN can create users with role {new_role}."
                )

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request:
            validated_data['created_by'] = request.user
        return super().create(validated_data)
