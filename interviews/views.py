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
    permission_classes = [IsAdminOrReadOnly]

    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["status", "job", "candidate"]
    search_fields      = ["candidate__full_name", "job__job_title"]
    ordering_fields    = ["created_at", "started_at"]
    ordering           = ["-created_at"]

    # non‑admin users only see their own candidates’ interviews
    def get_queryset(self):
        if (
            getattr(self.request.user, "role", "").lower() == "admin"
            or self.request.user.is_superuser
        ):
            return self.queryset
        return self.queryset.filter(candidate__recruiter=self.request.user)

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
        return Response(data)
