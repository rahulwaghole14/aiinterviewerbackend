import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Interview
from .serializers import InterviewSerializer, InterviewFeedbackSerializer


# ──────────────────────── Permissions ─────────────────────────
class IsAdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and (
                request.user.is_superuser or
                getattr(request.user, "role", "").lower() == "admin"
            )
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        if request.user.is_authenticated and (
            request.user.is_superuser or
            getattr(request.user, "role", "").lower() == "admin"
        ):
            return True
        raise PermissionDenied(detail="Only admins are allowed to perform this action.")


# ─────────────────────── Interview CRUD ViewSet ──────────────────────
class InterviewViewSet(viewsets.ModelViewSet):
    queryset = Interview.objects.select_related("candidate")
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "candidate"]
    search_fields = ["candidate__full_name"]
    ordering_fields = ["created_at", "started_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if (
            getattr(self.request.user, "role", "").lower() == "admin"
            or self.request.user.is_superuser
        ):
            return self.queryset
        return self.queryset.filter(candidate__recruiter=self.request.user)

    @action(detail=True, methods=["patch"], url_path="feedback", permission_classes=[IsAdminOnly])
    def edit_feedback(self, request, pk=None):
        interview = self.get_object()
        serializer = InterviewFeedbackSerializer(interview, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ─────────────────────── Status Summary APIView ────────────────────────
class InterviewStatusSummaryView(APIView):
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


# ─────────────────────── AI Interview Logic Views ────────────────────────
class StartAIInterviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        interview_id = request.data.get("interview_id")
        if not interview_id:
            return Response({"error": "interview_id is required"}, status=400)
        try:
            interview = Interview.objects.get(id=interview_id)
        except Interview.DoesNotExist:
            return Response({"error": "Interview not found"}, status=404)

        interview.status = Interview.Status.SCHEDULED
        interview.save()
        return Response({"message": "Interview started", "interview_id": str(interview.id)})


class RecordInterviewResponseView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        interview_id = request.data.get("interview_id")
        file = request.FILES.get("file")

        if not interview_id or not file:
            return Response({"error": "interview_id and file are required"}, status=400)

        try:
            interview = Interview.objects.get(id=interview_id)
        except Interview.DoesNotExist:
            return Response({"error": "Interview not found"}, status=404)

        # Save file to media/interview_videos/
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos')
        os.makedirs(upload_dir, exist_ok=True)

        filename = file.name.replace(" ", "_")
        file_path = os.path.join("interview_videos", filename)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        with default_storage.open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        interview.video_url = f"/media/{file_path}"
        interview.save()

        return Response({"message": "Response recorded", "video_url": interview.video_url})


class SubmitInterviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        interview_id = request.data.get("interview_id")
        if not interview_id:
            return Response({"error": "interview_id is required"}, status=400)
        try:
            interview = Interview.objects.get(id=interview_id)
        except Interview.DoesNotExist:
            return Response({"error": "Interview not found"}, status=404)

        interview.status = Interview.Status.COMPLETED
        interview.save()
        return Response({"message": "Interview submitted and marked as completed."})
