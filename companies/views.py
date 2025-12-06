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
    
    def get_queryset(self):
        """
        Get companies from Company model and also sync unique company names from Jobs
        This ensures companies created during job creation appear in the dropdown
        """
        from jobs.models import Job
        
        # Get unique company names from Jobs that don't exist in Company model
        job_company_names = Job.objects.exclude(
            company_name__isnull=True
        ).exclude(
            company_name=''
        ).values_list('company_name', flat=True).distinct()
        
        existing_company_names = set(
            Company.objects.values_list('name', flat=True)
        )
        
        # Create Company records for job company names that don't exist
        # This sync happens on each request to ensure dropdown is always up-to-date
        for company_name in job_company_names:
            if company_name and company_name.strip():
                company_name_clean = company_name.strip()
                if company_name_clean not in existing_company_names:
                    Company.objects.get_or_create(
                        name=company_name_clean,
                        defaults={
                            'description': f'Company created automatically from job postings',
                            'is_active': True,
                        }
                    )
                    existing_company_names.add(company_name_clean)
        
        # Return all companies (including newly synced ones)
        return Company.objects.filter(is_active=True).order_by("-id")


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
