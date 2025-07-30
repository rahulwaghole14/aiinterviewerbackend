from rest_framework import serializers
from django.contrib.auth import get_user_model
from authapp.models import Role

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.CharField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'full_name', 'company_name', 'role', 'password')

    def validate_role(self, value):
        value_upper = value.strip().upper().replace(" ", "_")
        valid_roles = [choice[0] for choice in Role.choices]
        if value_upper not in valid_roles:
            raise serializers.ValidationError(f"'{value}' is not a valid role. Valid roles: {valid_roles}")
        return value_upper

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
