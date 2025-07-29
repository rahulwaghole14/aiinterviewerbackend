from rest_framework import serializers
from .models import UserData, Role
import re
from datetime import date


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserData
        fields = '__all__'

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
            raise serializers.ValidationError(
                "Enter a valid international phone number (10–15 digits, optional '+')."
            )
        return value

    def validate_role(self, value):
        valid_roles = [r[0] for r in Role.CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(f"Role must be one of: {', '.join(valid_roles)}")
        return value

    def validate_permission_granted(self, value):
        if value > date.today():
            raise serializers.ValidationError("Permission granted date cannot be in the future.")
        return value
