from rest_framework.views import APIView
from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model

from .serializers import RegisterSerializer

User = get_user_model()

# 1. Basic RegisterView (Fixes ImportError)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

# 2. Role-Based Login View
class RoleBasedLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    allowed_role = None  # Must be set by subclass

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if self.allowed_role and user.role != self.allowed_role:
            return Response({"detail": f"Only {self.allowed_role} users can login here."}, status=status.HTTP_403_FORBIDDEN)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "company_name": user.company_name
            }
        })

class AdminLoginView(RoleBasedLoginView):
    allowed_role = "ADMIN"

class CompanyLoginView(RoleBasedLoginView):
    allowed_role = "COMPANY"

class RecruiterLoginView(RoleBasedLoginView):
    allowed_role = "RECRUITER"

# 3. Profile View
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "company_name": user.company_name
        })

# 4. Register user by role (optional if used at /auth/register-user/)
class CreateUserByRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_user = request.user
        target_role = request.data.get("role", "").strip().upper().replace(" ", "_")

        if current_user.role == "ADMIN" and target_role != "COMPANY":
            return Response({"error": "Admin can only create COMPANY users."}, status=403)
        if current_user.role == "COMPANY" and target_role != "RECRUITER":
            return Response({"error": "Company users can only create RECRUITER users."}, status=403)
        if current_user.role not in ["ADMIN", "COMPANY"]:
            return Response({"error": "You are not authorized to create users."}, status=403)

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": f"{target_role} created successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            }, status=201)
        return Response(serializer.errors, status=400)
    
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)
        except:
            return Response({"error": "Token not found or already deleted."}, status=status.HTTP_400_BAD_REQUEST)

