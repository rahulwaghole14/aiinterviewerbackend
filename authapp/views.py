from rest_framework.views import APIView
from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from rest_framework.permissions import IsAuthenticated
from .serializers import LoginSerializer

from .serializers import RegisterSerializer

User = get_user_model()


# 1. Registration View
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# 2. Role-Based Login (Base Class)
class RoleBasedLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    allowed_role = None

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if self.allowed_role and user.role.upper() != self.allowed_role.upper():
            return Response({"detail": f"Only {self.allowed_role} users can login here."}, status=status.HTTP_403_FORBIDDEN)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": getattr(user, "full_name", ""),
                "role": getattr(user, "role", ""),
                "company_name": getattr(user, "company_name", "")
            }
        })


# 3. Role-Specific Login Views
class AdminLoginView(RoleBasedLoginView):
    allowed_role = "ADMIN"

class CompanyLoginView(RoleBasedLoginView):
    allowed_role = "COMPANY"

class RecruiterLoginView(RoleBasedLoginView):
    allowed_role = "RECRUITER"


# 4. Profile View
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": getattr(user, "full_name", ""),
            "role": user.get_role_display() if hasattr(user, "get_role_display") else user.role,
            "company_name": getattr(user, "company_name", "")
        })


# 5. Role-Based User Creation View
class CreateUserByRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_user = request.user
        target_role = request.data.get("role", "").strip().upper().replace(" ", "_")

        if current_user.role.upper() == "ADMIN" and target_role != "COMPANY":
            return Response({"error": "Admin can only create COMPANY users."}, status=403)
        if current_user.role.upper() == "COMPANY" and target_role != "RECRUITER":
            return Response({"error": "Company users can only create RECRUITER users."}, status=403)
        if current_user.role.upper() not in ["ADMIN", "COMPANY"]:
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


# 6. Logout View
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)
        except:
            return Response({"error": "Token not found or already deleted."}, status=status.HTTP_400_BAD_REQUEST)

class CustomLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": getattr(user, "full_name", ""),
                "role": user.role,
                "company_name": getattr(user, "company_name", "")
            }
        })
