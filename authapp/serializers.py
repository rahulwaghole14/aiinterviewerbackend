from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _
from authapp.models import Role
from authapp.models import CustomUser


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.CharField()
    username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "full_name",
            "company_name",
            "role",
            "password",
        )

    def validate_role(self, value):
        value_upper = value.strip().upper().replace(" ", "_")
        valid_roles = [choice[0] for choice in Role.choices]
        if value_upper not in valid_roles:
            raise serializers.ValidationError(
                f"'{value}' is not a valid role. Valid roles: {valid_roles}"
            )
        return value_upper

    def create(self, validated_data):
        password = validated_data.pop("password")

        # Set username to email if not provided
        if "username" not in validated_data or not validated_data["username"]:
            validated_data["username"] = validated_data["email"]

        # Handle company relationships for users with company_name
        if validated_data.get("company_name"):
            from companies.models import Company

            company_name = validated_data["company_name"]

            # Try to get existing company or create new one
            company, created = Company.objects.get_or_create(
                name=company_name,
                defaults={
                    "description": f"Company created during registration for {company_name}",
                    "is_active": True,
                },
            )

            # Set the company relationship
            validated_data["company"] = company

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()  # Not limited to EmailField
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email_or_username = data.get("email")
        password = data.get("password")

        user = None

        # Try email-based authentication first (custom backend), then username
        user = authenticate(
            request=self.context.get("request"), email=email_or_username, password=password
        )
        if not user:
            # Fallback: treat input as username
            user = authenticate(
                request=self.context.get("request"), username=email_or_username, password=password
            )

        if not user:
            raise serializers.ValidationError("Invalid email/username or password.")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        data["user"] = user
        return data
