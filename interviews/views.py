# interviews/views.py
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models      import Interview
from .serializers import InterviewSerializer, InterviewFeedbackSerializer
from .permissions import HiringAgencyOrRecruiterInterviewPermission
from utils.logger import log_interview_schedule, log_permission_denied, ActionLogger


# ──────────────────────────── Permissions ────────────────────────────────
class IsAdminOnly(permissions.BasePermission):
    """
    Allow access only to authenticated users whose role == "admin"
    (case‑insensitive) OR who are Django superusers.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.is_superuser or
                getattr(request.user, "role", "").lower() == "admin"
            )
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    SAFE methods → any authenticated user.
    WRITE methods → admin / superuser only.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        if request.user.is_authenticated and (
            request.user.is_superuser or
            getattr(request.user, "role", "").lower() == "admin"
        ):
            return True

        raise PermissionDenied(detail="Only admins are allowed to perform this action.")


# ───────────────────────────── ViewSet ────────────────────────────────────
class InterviewViewSet(viewsets.ModelViewSet):
    """
    /api/interviews/  → list, create
    /api/interviews/<pk>/  → retrieve, update, delete
    """
    queryset           = Interview.objects.select_related("candidate", "job")
    serializer_class   = InterviewSerializer
    permission_classes = [HiringAgencyOrRecruiterInterviewPermission]

    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["status", "job", "candidate"]
    search_fields      = ["candidate__full_name", "job__job_title"]
    ordering_fields    = ["created_at", "started_at"]
    ordering           = ["-created_at"]

    # non‑admin users only see their own candidates' interviews
    def get_queryset(self):
        if (
            getattr(self.request.user, "role", "").lower() == "admin"
            or self.request.user.is_superuser
        ):
            return self.queryset
        return self.queryset.filter(candidate__recruiter=self.request.user)

    def list(self, request, *args, **kwargs):
        """Log interview listing"""
        ActionLogger.log_user_action(
            user=request.user,
            action='interview_list',
            details={'count': self.get_queryset().count()},
            status='SUCCESS'
        )
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Log interview retrieval"""
        ActionLogger.log_user_action(
            user=request.user,
            action='interview_retrieve',
            details={'interview_id': kwargs.get('pk')},
            status='SUCCESS'
        )
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Log interview creation"""
        try:
            response = super().create(request, *args, **kwargs)
            
            # Log successful interview creation
            if response.status_code == 201:
                interview_data = response.data
                log_interview_schedule(
                    user=request.user,
                    interview_id=interview_data.get('id'),
                    candidate_id=interview_data.get('candidate'),
                    job_id=interview_data.get('job'),
                    status='SUCCESS',
                    details={
                        'scheduled_at': interview_data.get('scheduled_at'),
                        'status': interview_data.get('status'),
                        'ip_address': request.META.get('REMOTE_ADDR')
                    }
                )
            
            return response
            
        except Exception as e:
            # Log interview creation failure
            ActionLogger.log_user_action(
                user=request.user,
                action='interview_create',
                details={'error': str(e)},
                status='FAILED'
            )
            raise

    def update(self, request, *args, **kwargs):
        """Log interview update"""
        ActionLogger.log_user_action(
            user=request.user,
            action='interview_update',
            details={
                'interview_id': kwargs.get('pk'),
                'update_data': request.data
            },
            status='SUCCESS'
        )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Log interview partial update"""
        ActionLogger.log_user_action(
            user=request.user,
            action='interview_partial_update',
            details={
                'interview_id': kwargs.get('pk'),
                'update_data': request.data
            },
            status='SUCCESS'
        )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Log interview deletion"""
        ActionLogger.log_user_action(
            user=request.user,
            action='interview_delete',
            details={'interview_id': kwargs.get('pk')},
            status='SUCCESS'
        )
        return super().destroy(request, *args, **kwargs)

    # admin‑only PATCH /api/interviews/<pk>/feedback/
    @action(
        detail=True,
        methods=["patch"],
        url_path="feedback",
        permission_classes=[IsAdminOnly],
    )
    def edit_feedback(self, request, pk=None):
        interview  = self.get_object()
        serializer = InterviewFeedbackSerializer(
            interview, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Log feedback update
        ActionLogger.log_user_action(
            user=request.user,
            action='interview_feedback_update',
            details={
                'interview_id': pk,
                'feedback_data': request.data
            },
            status='SUCCESS'
        )
        
        return Response(serializer.data)


# ─────────────────────── Status Summary endpoint ─────────────────────────
class InterviewStatusSummaryView(APIView):
    """
    GET /api/interviews/summary/  → { "scheduled": 5, "completed": 2, ... }
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Interview.objects.all()
        if (
            getattr(request.user, "role", "").lower() != "admin"
            and not request.user.is_superuser
        ):
            qs = qs.filter(candidate__recruiter=request.user)

        summary = qs.values("status").annotate(count=Count("id"))
        data = {row["status"]: row["count"] for row in summary}
        
        # Log summary request
        ActionLogger.log_user_action(
            user=request.user,
            action='interview_summary',
            details={'summary': data},
            status='SUCCESS'
        )
        
        return Response(data)
