from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from .models import Company, Recruiter
from .serializers import (
    CompanySerializer,
    RecruiterSerializer,
    RecruiterCreateSerializer,
)
from utils.hierarchy_permissions import (
    CompanyHierarchyPermission,
    RecruiterHierarchyPermission,
    DataIsolationMixin,
)


class CompanyListCreateView(DataIsolationMixin, generics.ListCreateAPIView):
    queryset = Company.objects.all().order_by("-id")  # Show all companies, newest first
    serializer_class = CompanySerializer
    permission_classes = [CompanyHierarchyPermission]


class CompanyDetailView(DataIsolationMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [CompanyHierarchyPermission]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class RecruiterListView(DataIsolationMixin, generics.ListAPIView):
    queryset = Recruiter.objects.all().order_by(
        "-id"
    )  # Show all recruiters, newest first
    serializer_class = RecruiterSerializer
    permission_classes = [RecruiterHierarchyPermission]


class RecruiterCreateView(generics.CreateAPIView):
    serializer_class = RecruiterCreateSerializer
    permission_classes = [RecruiterHierarchyPermission]

    def perform_create(self, serializer):
        # The serializer handles all the creation logic
        # We don't need to override anything here
        serializer.save()


class RecruiterUpdateDeleteView(
    DataIsolationMixin, generics.RetrieveUpdateDestroyAPIView
):
    queryset = Recruiter.objects.all()
    serializer_class = RecruiterSerializer
    permission_classes = [RecruiterHierarchyPermission]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
