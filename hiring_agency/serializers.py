from rest_framework import serializers
from .models import UserData, Role
import re
from datetime import date


class UserDataSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    company_name = serializers.CharField(source='get_company_name', read_only=True)
    company = serializers.SerializerMethodField()  # Override the default company field
    # Add a writable field for company_name input
    input_company_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    def get_company_id(self, obj):
        """Get company ID, resolving from company_name if ForeignKey is null"""
        if obj.company:
            return obj.company.id
        elif obj.company_name and obj.company_name != "No Company":
            # Try to find the company by name and return its ID
            from companies.models import Company
            try:
                company = Company.objects.filter(name=obj.company_name).first()
                return company.id if company else None
            except:
                return None
        return None
    
    def get_company(self, obj):
        """Get company ID using the custom resolution logic"""
        return self.get_company_id(obj)
    
    class Meta:
        model = UserData
        fields = '__all__'
        read_only_fields = ['created_by']
        extra_kwargs = {
            'password': {'write_only': True}
        }

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
        password = validated_data.pop('password', None)
        request = self.context.get('request')
        if request:
            validated_data['created_by'] = request.user
        
        # Handle company relationship
        if request and request.user.role == "COMPANY":
            # If creator is a company user, set the company relationship
            validated_data['company'] = request.user.company
            # Also set company_name for backward compatibility
            if request.user.company:
                validated_data['company_name'] = request.user.company.name
        elif request and request.user.role == "ADMIN":
            # For admin users, resolve company from input_company_name if provided
            input_company_name = validated_data.pop('input_company_name', None)
            if input_company_name and input_company_name.strip():
                from companies.models import Company
                try:
                    company = Company.objects.filter(name=input_company_name.strip()).first()
                    if company:
                        validated_data['company'] = company
                        validated_data['company_name'] = company.name
                    else:
                        # If company doesn't exist, just set the company_name
                        validated_data['company_name'] = input_company_name.strip()
                except:
                    # If lookup fails, just set the company_name
                    validated_data['company_name'] = input_company_name.strip()
        
        user_data = UserData.objects.create(**validated_data)
        if password:
            user_data.password = password
            user_data.save()
        return user_data
    
    def update(self, instance, validated_data):
        """Handle partial updates for hiring agency users"""
        # Remove password from validated_data if present
        password = validated_data.pop('password', None)
        
        # Update the instance with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Handle password update if provided
        if password:
            instance.password = password
        
        instance.save()
        return instance
