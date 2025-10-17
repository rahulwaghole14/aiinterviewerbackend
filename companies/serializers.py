from rest_framework import serializers
from .models import Company, Recruiter
from authapp.models import CustomUser, Role


class CompanySerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Company
        fields = ["id", "name", "email", "password", "description", "is_active"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        company = Company.objects.create(**validated_data)
        if password:
            company.password = password
            company.save()
        return company


class RecruiterSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    # Add writable fields for user information
    new_full_name = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    new_email = serializers.EmailField(
        write_only=True, required=False, allow_blank=True
    )

    class Meta:
        model = Recruiter
        fields = [
            "id",
            "user",
            "full_name",
            "email",
            "company",
            "is_active",
            "new_full_name",
            "new_email",
        ]
        extra_kwargs = {
            "company": {"required": False},
            "is_active": {"required": False},
        }

    def update(self, instance, validated_data):
        """Handle partial updates for recruiter and related user"""
        # Extract user-related fields
        new_full_name = validated_data.pop("new_full_name", None)
        new_email = validated_data.pop("new_email", None)

        # Update user information if provided
        if new_full_name is not None:
            instance.user.full_name = new_full_name
            instance.user.save()

        if new_email is not None:
            instance.user.email = new_email
            instance.user.save()

        # Update recruiter fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Refresh the instance to ensure updated data is reflected
        instance.refresh_from_db()
        return instance


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
        if not data.get("username"):
            data["username"] = data["email"]

        # Ensure username is unique
        from authapp.models import CustomUser

        username = data["username"]
        email = data["email"]

        # Check if username already exists
        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError(f"Username '{username}' already exists")

        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(f"Email '{email}' already exists")

        # Get the request user to determine if they're a company user
        request = self.context.get("request")
        if request and request.user.role == "COMPANY":
            # For company users, use their company_id
            if request.user.company:
                data["company_id"] = request.user.company.id
            else:
                raise serializers.ValidationError(
                    "Company user must be associated with a company"
                )
        else:
            # For non-company users, validate that company_id is provided
            if not data.get("company_id"):
                raise serializers.ValidationError("company_id is required")

        # Verify that the company exists
        try:
            company = Company.objects.get(id=data["company_id"])
        except Company.DoesNotExist:
            raise serializers.ValidationError(
                f"Company with id {data['company_id']} does not exist"
            )

        return data

    def create(self, validated_data):
        # Extract fields
        username = validated_data["username"]
        email = validated_data["email"]
        full_name = validated_data["full_name"]
        password = validated_data["password"]
        company_id = validated_data["company_id"]

        # Get company
        company = Company.objects.get(id=company_id)

        # Create user
        user = CustomUser.objects.create(
            username=username,
            email=email,
            full_name=full_name,
            role=Role.RECRUITER,
            company=company,
        )
        user.set_password(password)
        user.save()

        # Create recruiter
        recruiter = Recruiter.objects.create(user=user, company=company)

        return recruiter

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "username": instance.user.username,
            "email": instance.user.email,
            "full_name": instance.user.full_name,
            "role": instance.user.role,
            "company": instance.company.name,
            "is_active": instance.is_active,
        }
