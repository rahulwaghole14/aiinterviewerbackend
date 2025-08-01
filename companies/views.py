from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import Company, Recruiter
from .serializers import (
    CompanySerializer,
    RecruiterSerializer,
    RecruiterCreateSerializer
)
from .permissions import AdminOnlyPermission, AdminOrReadOnlyPermission

class CompanyListCreateView(generics.ListCreateAPIView):
    queryset = Company.objects.filter(is_active=True)
    serializer_class = CompanySerializer
    permission_classes = [AdminOrReadOnlyPermission]

class CompanyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [AdminOrReadOnlyPermission]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class RecruiterListView(generics.ListAPIView):
    serializer_class = RecruiterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return Recruiter.objects.filter(is_active=True)
        elif user.role == "COMPANY":
            return Recruiter.objects.filter(company__name=user.company_name, is_active=True)
        return Recruiter.objects.none()

class RecruiterCreateView(generics.CreateAPIView):
    serializer_class = RecruiterCreateSerializer
    permission_classes = [AdminOnlyPermission]

class RecruiterUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Recruiter.objects.all()
    serializer_class = RecruiterSerializer
    permission_classes = [AdminOnlyPermission]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
