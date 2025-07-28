from rest_framework import serializers
from .models import UserData, Role
import re

class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserData
        fields = '__all__'

    def validate_email(self, value):
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Invalid email format.")
        return value

    def validate_full_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Full name must be at least 2 characters long.")
        return value

    def validate_phone(self, value):
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
