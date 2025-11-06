from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import Domain, Job
from .serializers import (
    DomainSerializer,
    DomainListSerializer,
    JobSerializer,
    JobTitleSerializer,
)
from .permissions import DomainAdminOnlyPermission, JobDomainPermission
from utils.logger import ActionLogger
from notifications.services import NotificationService

# ────────────────────────────────────────────────────────────────
# Domain Management Views
# ────────────────────────────────────────────────────────────────


class DomainListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/domains/  -> list all domains
    POST /api/domains/  -> create new domain (admin only)
    """

    queryset = Domain.objects.filter(is_active=True).order_by("name")
    permission_classes = [DomainAdminOnlyPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]

    def get_serializer_class(self):
        return (
            DomainSerializer if self.request.method == "POST" else DomainListSerializer
        )

    def list(self, request, *args, **kwargs):
        """Log domain listing"""
        ActionLogger.log_user_action(
            user=request.user,
            action="domain_list",
            details={"count": self.get_queryset().count()},
            status="SUCCESS",
        )
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Log domain creation"""
        ActionLogger.log_user_action(
            user=request.user,
            action="domain_create",
            details={"domain_name": request.data.get("name")},
            status="SUCCESS",
        )
        return super().create(request, *args, **kwargs)


class DomainDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/domains/{id}/  -> get specific domain
    PUT    /api/domains/{id}/  -> update domain (admin only)
    DELETE /api/domains/{id}/  -> delete domain (admin only)
    """

    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = [DomainAdminOnlyPermission]

    def retrieve(self, request, *args, **kwargs):
        """Log domain retrieval"""
        ActionLogger.log_user_action(
            user=request.user,
            action="domain_retrieve",
            details={"domain_id": kwargs.get("pk")},
            status="SUCCESS",
        )
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Log domain update"""
        ActionLogger.log_user_action(
            user=request.user,
            action="domain_update",
            details={"domain_id": kwargs.get("pk")},
            status="SUCCESS",
        )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Log domain deletion (soft delete)"""
        domain = self.get_object()
        domain.is_active = False
        domain.save()

        ActionLogger.log_user_action(
            user=request.user,
            action="domain_delete",
            details={"domain_id": kwargs.get("pk"), "domain_name": domain.name},
            status="SUCCESS",
        )

        return Response(
            {"message": "Domain deactivated successfully"}, status=status.HTTP_200_OK
        )


class DomainActiveListView(generics.ListAPIView):
    """
    GET /api/domains/active/  -> list only active domains
    """

    queryset = Domain.objects.filter(is_active=True).order_by("name")
    serializer_class = DomainListSerializer
    permission_classes = [DomainAdminOnlyPermission]

    def list(self, request, *args, **kwargs):
        """Log active domain listing"""
        ActionLogger.log_user_action(
            user=request.user,
            action="domain_active_list",
            details={"count": self.get_queryset().count()},
            status="SUCCESS",
        )
        return super().list(request, *args, **kwargs)


# ────────────────────────────────────────────────────────────────
# Job Management Views (Updated with Domain Support)
# ────────────────────────────────────────────────────────────────


class JobListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/jobs/  -> list all jobs
    POST /api/jobs/  -> create new job (admin/company only, requires domain)
    """

    queryset = Job.objects.select_related("domain").all().order_by("-created_at")
    serializer_class = JobSerializer
    permission_classes = [JobDomainPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["company_name", "position_level", "domain"]
    search_fields = ["job_title", "tech_stack_details", "domain__name"]
    ordering_fields = ["created_at", "job_title", "domain__name"]

    def create(self, request, *args, **kwargs):
        """Log job creation with domain validation"""
        # Validate domain exists and is active
        domain_id = request.data.get("domain")
        
        # Handle NaN, None, empty string, or invalid domain_id
        if domain_id is None or domain_id == "" or (isinstance(domain_id, (int, float)) and (domain_id != domain_id or domain_id <= 0)):  # domain_id != domain_id checks for NaN
            return Response(
                {"error": "Domain is required for job creation", "received_domain": domain_id},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Convert to int if it's a string
            if isinstance(domain_id, str):
                domain_id = int(domain_id)
            domain = Domain.objects.get(id=domain_id, is_active=True)
        except (ValueError, TypeError):
            return Response(
                {"error": f"Invalid domain ID: {domain_id}. Must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Domain.DoesNotExist:
            return Response(
                {"error": f"Selected domain (ID: {domain_id}) does not exist or is inactive"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ActionLogger.log_user_action(
        #     user=request.user,
        #     action='job_create',
        #     details={
        #         'job_title': request.data.get('job_title'),
        #         'domain_id': domain_id,
        #         'domain_name': domain.name
        #     },
        #     status='SUCCESS'
        # )

        # Send notification for job creation
        # try:
        #     job = self.get_queryset().latest('created_at')
        #     NotificationService.send_job_created_notification(job)
        # except Exception as e:
        #     # Log notification failure but don't fail the request
        #     ActionLogger.log_user_action(
        #         user=request.user,
        #         action='notification_failed',
        #         details={'error': str(e), 'job_title': request.data.get('job_title')},
        #         status='FAILED'
        #     )

        # Call parent create method - DRF will handle ValidationError properly
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            # Return detailed validation errors
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Save the job
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/jobs/{id}/  -> get specific job
    PUT    /api/jobs/{id}/  -> update job
    DELETE /api/jobs/{id}/  -> delete job
    """

    queryset = Job.objects.select_related("domain").all()
    serializer_class = JobSerializer
    permission_classes = [JobDomainPermission]
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        """Log job update with domain validation"""
        job = self.get_object()

        # Validate domain if being updated
        domain_id = request.data.get("domain")
        if domain_id:
            try:
                domain = Domain.objects.get(id=domain_id, is_active=True)
            except Domain.DoesNotExist:
                return Response(
                    {"error": "Selected domain does not exist or is inactive"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Temporarily comment out ActionLogger to debug
        # ActionLogger.log_user_action(
        #     user=request.user,
        #     action='job_update',
        #     details={'job_id': kwargs.get('pk'), 'domain_id': domain_id},
        #     status='SUCCESS'
        # )

        return super().update(request, *args, **kwargs)


class JobTitleListView(generics.ListAPIView):
    """
    GET /api/jobs/titles/  -> list job titles with domain information
    """

    queryset = Job.objects.select_related("domain").all()
    serializer_class = JobTitleSerializer
    permission_classes = [JobDomainPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["domain"]
    search_fields = ["job_title", "domain__name"]


class JobsByDomainView(generics.ListAPIView):
    """
    GET /api/jobs/by-domain/{domain_id}/  -> list jobs by specific domain
    """

    serializer_class = JobSerializer
    permission_classes = [JobDomainPermission]

    def get_queryset(self):
        domain_id = self.kwargs.get("domain_id")
        return Job.objects.select_related("domain").filter(domain_id=domain_id)
