# interviews/views.py
import logging
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.http import HttpResponse  # Added for HttpResponse

from rest_framework import generics, status, viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from .models import (
    Interview,
    InterviewSlot,
    InterviewSchedule,
    AIInterviewConfiguration,
    InterviewConflict,
)
from jobs.models import Job
from .serializers import (
    InterviewSerializer,
    InterviewFeedbackSerializer,
    InterviewSlotSerializer,
    InterviewScheduleSerializer,
    AIInterviewConfigurationSerializer,
    InterviewConflictSerializer,
    SlotBookingSerializer,
    SlotSearchSerializer,
    RecurringSlotSerializer,
)
from utils.hierarchy_permissions import DataIsolationMixin, InterviewHierarchyPermission
from utils.logger import log_interview_schedule, log_permission_denied, ActionLogger
from notifications.services import NotificationService

logger = logging.getLogger(__name__)

CODING_LANGUAGE_CHOICES = Job._meta.get_field("coding_language").choices
ALLOWED_CODING_LANGUAGES = {choice[0] for choice in CODING_LANGUAGE_CHOICES}


# ──────────────────────────── Permissions ────────────────────────────────
class IsAdminOnly(permissions.BasePermission):
    """
    Allow access only to authenticated users whose role == "admin"
    (case‑insensitive) OR who are Django superusers.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser
            or getattr(request.user, "role", "").lower() == "admin"
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
            request.user.is_superuser
            or getattr(request.user, "role", "").lower() == "admin"
        ):
            return True

        raise PermissionDenied(detail="Only admins are allowed to perform this action.")


# ───────────────────────────── ViewSet ────────────────────────────────────
class PublicInterviewAccessView(APIView):
    """
    Public endpoint for candidates to access interviews via secure links
    No authentication required - uses secure link validation
    """

    permission_classes = []  # No authentication required

    def get(self, request, link_token):
        """Get interview details and serve interactive interview interface"""
        try:
            # Debug logging
            print(
                f"DEBUG: PublicInterviewAccessView.get() called with link_token: {link_token}"
            )

            # Try to decode the link token - handle both long and short formats
            import base64

            try:
                # First try the long format (interview_id:signature)
                decoded_token = base64.urlsafe_b64decode(
                    link_token.encode("utf-8")
                ).decode("utf-8")
                interview_id, signature = decoded_token.split(":", 1)
                print(f"DEBUG: Using long format - interview_id: {interview_id}")
            except:
                # If that fails, try the short format (just interview_id)
                try:
                    # Add padding if needed
                    padded_token = (
                        link_token + "=" * (4 - len(link_token) % 4)
                        if len(link_token) % 4
                        else link_token
                    )
                    interview_id = base64.urlsafe_b64decode(
                        padded_token.encode("utf-8")
                    ).decode("utf-8")
                    print(f"DEBUG: Using short format - interview_id: {interview_id}")
                except Exception as e:
                    print(f"DEBUG: Failed to decode token: {e}")
                    return Response(
                        {
                            "error": "Invalid interview link format",
                            "status": "invalid_format",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Get the interview
            interview = Interview.objects.get(id=interview_id)
            print(f"DEBUG: Found interview: {interview.id}")
            print(f"DEBUG: Interview link: {interview.interview_link[:50]}...")

            # For short format, just check if the token matches
            if len(link_token) <= 40:  # Short format
                is_valid = interview.interview_link == link_token
                message = "Link is valid" if is_valid else "Invalid interview link"
            else:  # Long format - use full validation
                is_valid, message = interview.validate_interview_link(link_token)

            print(f"DEBUG: Validation result: {is_valid} - {message}")

            if not is_valid:
                print(f"DEBUG: Returning invalid link error: {message}")
                return Response(
                    {"error": message, "status": "invalid_link"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # REMOVED: Blocking access before scheduled time
            # The link is valid for 24 hours from scheduled time, so candidates can access it anytime within that window
            # The expiration check (24 hours) is already handled in validate_interview_link()

            # Check if user wants JSON response (for API calls)
            if request.headers.get("Accept") == "application/json":
                # Return JSON response for API calls
                response_data = {
                    "interview_id": str(interview.id),
                    "candidate_name": interview.candidate.full_name,
                    "candidate_email": interview.candidate.email,
                    "job_title": interview.job.job_title if interview.job else "N/A",
                    "company_name": (
                        interview.job.company_name if interview.job else "N/A"
                    ),
                    "interview_round": interview.interview_round,
                    "scheduled_date": (
                        interview.started_at.strftime("%B %d, %Y")
                        if interview.started_at
                        else "TBD"
                    ),
                    "scheduled_time": (
                        interview.started_at.strftime("%I:%M %p")
                        if interview.started_at
                        else "TBD"
                    ),
                    "duration_minutes": (
                        interview.duration_seconds // 60
                        if interview.duration_seconds
                        else 60
                    ),
                    "ai_interview_type": interview.ai_interview_type,
                    "status": interview.status,
                    "video_url": interview.video_url,
                    "can_join": True,
                    "message": "You can now join your interview",
                }
                return Response(response_data)

                # Redirect to the actual AI interview portal with video/audio capabilities
            from django.shortcuts import redirect
            from interview_app.models import InterviewSession

            # Create or get the AI interview session with a proper session key
            # Generate a short session key for the interview portal
            import uuid

            short_session_key = uuid.uuid4().hex

            ai_session, created = InterviewSession.objects.get_or_create(
                session_key=short_session_key,
                defaults={
                    "candidate_name": interview.candidate.full_name,
                    "candidate_email": interview.candidate.email,
                    "job_description": (
                        interview.job.tech_stack_details
                        if interview.job
                        else "Technical Role"
                    ),
                    "resume_text": getattr(interview.candidate, "resume_text", "")
                    or "Experienced professional seeking new opportunities.",
                    "language_code": "en",
                    "accent_tld": "com",
                    "scheduled_at": interview.started_at,
                    "status": "SCHEDULED",
                },
            )

            # Redirect to the actual AI interview portal
            from interview_app.utils import get_interview_url
            ai_interview_url = get_interview_url(short_session_key, request)
            return redirect(ai_interview_url)

            # Log the access attempt
            ActionLogger.log_user_action(
                user=None,  # No user for public access
                action="candidate_interview_access",
                details={
                    "interview_id": str(interview.id),
                    "candidate_email": interview.candidate.email,
                    "link_token": link_token[:20]
                    + "...",  # Log partial token for security
                    "access_time": timezone.now().isoformat(),
                },
                status="SUCCESS",
            )

            return HttpResponse(html_content, content_type="text/html")

        except Interview.DoesNotExist:
            return Response(
                {"error": "Interview not found", "status": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error in public interview access: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": f"Invalid interview link: {str(e)}", "status": "error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def post(self, request, link_token):
        """Join the interview (start the interview session)"""
        try:
            # Decode the link token
            import base64

            decoded_token = base64.urlsafe_b64decode(link_token.encode("utf-8")).decode(
                "utf-8"
            )
            interview_id, signature = decoded_token.split(":", 1)

            # Get the interview
            interview = Interview.objects.get(id=interview_id)

            # Validate the link
            is_valid, message = interview.validate_interview_link(link_token)

            if not is_valid:
                return Response(
                    {"error": message, "status": "invalid_link"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if interview can be started
            now = timezone.now()
            if interview.started_at and now < interview.started_at:
                return Response(
                    {
                        "error": f'Interview starts at {interview.started_at.strftime("%I:%M %p")}. Please wait.',
                        "status": "not_started",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if interview.status == "completed":
                return Response(
                    {
                        "error": "This interview has already been completed",
                        "status": "completed",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Start the interview
            if not interview.started_at:
                interview.started_at = now
                interview.save()

            # Log the interview start
            ActionLogger.log_user_action(
                user=None,  # No user for public access
                action="candidate_interview_started",
                details={
                    "interview_id": str(interview.id),
                    "candidate_email": interview.candidate.email,
                    "start_time": now.isoformat(),
                },
                status="SUCCESS",
            )

            # Create AI interview session if not exists
            from ai_interview.services import ai_interview_service
            from ai_interview.models import AIInterviewSession

            ai_session, created = AIInterviewSession.objects.get_or_create(
                interview=interview,
                defaults={
                    "status": "ACTIVE",
                    "model_name": "gemini-1.5-flash-latest",
                    "model_version": "1.0",
                    "ai_configuration": {
                        "language_code": "en",
                        "accent_tld": "com",
                        "candidate_name": interview.candidate.full_name,
                        "candidate_email": interview.candidate.email,
                        "job_description": (
                            interview.job.description if interview.job else ""
                        ),
                        "resume_text": getattr(interview.candidate, "resume_text", "")
                        or "",
                    },
                    "session_started_at": timezone.now(),
                },
            )

            return Response(
                {
                    "interview_id": str(interview.id),
                    "candidate_name": interview.candidate.full_name,
                    "ai_interview_type": interview.ai_interview_type,
                    "started_at": interview.started_at.isoformat(),
                    "status": "started",
                    "message": "Interview started successfully",
                    "ai_configuration": (
                        interview.schedule.slot.ai_configuration
                        if interview.is_scheduled
                        else {}
                    ),
                    "ai_session_id": str(ai_session.id),
                    "ai_interview_ready": True,
                }
            )

        except Interview.DoesNotExist:
            return Response(
                {"error": "Interview not found", "status": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error starting interview: {e}")
            return Response(
                {"error": "Failed to start interview", "status": "error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InterviewViewSet(DataIsolationMixin, viewsets.ModelViewSet):
    """
    /api/interviews/  → list, create
    /api/interviews/<pk>/  → retrieve, update, delete

    Query Parameters:
    - candidate_id: Filter interviews by candidate ID
    - status: Filter by interview status
    - job: Filter by job ID
    - candidate: Filter by candidate ID (alternative)
    """

    queryset = Interview.objects.select_related(
        "candidate", 
        "job", 
        "evaluation",  # OneToOne relationship - select_related is sufficient
        "candidate__recruiter"
    )
    serializer_class = InterviewSerializer
    permission_classes = [InterviewHierarchyPermission]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "job", "candidate"]
    search_fields = ["candidate__full_name", "job__job_title"]
    ordering_fields = ["created_at", "started_at"]
    ordering = ["-created_at"]

    # non‑admin users only see their own candidates' interviews
    def get_queryset(self):
        queryset = self.queryset

        # Apply data isolation based on user role
        if (
            getattr(self.request.user, "role", "").lower() == "admin"
            or self.request.user.is_superuser
        ):
            pass  # Admin sees all interviews
        else:
            queryset = queryset.filter(candidate__recruiter=self.request.user)

        # Apply candidate_id filtering if provided
        candidate_id = self.request.query_params.get("candidate_id")
        if candidate_id:
            try:
                candidate_id = int(candidate_id)
                queryset = queryset.filter(candidate_id=candidate_id)
            except (ValueError, TypeError):
                # If candidate_id is not a valid integer, return empty queryset
                queryset = Interview.objects.none()

        return queryset

    def list(self, request, *args, **kwargs):
        """Log interview listing"""
        ActionLogger.log_user_action(
            user=request.user,
            action="interview_list",
            details={"count": self.get_queryset().count()},
            status="SUCCESS",
        )
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Log interview retrieval"""
        ActionLogger.log_user_action(
            user=request.user,
            action="interview_retrieve",
            details={"interview_id": kwargs.get("pk")},
            status="SUCCESS",
        )
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Log interview creation"""
        try:
            response = super().create(request, *args, **kwargs)
            ActionLogger.log_user_action(
                user=request.user,
                action="interview_create",
                details={"interview_id": response.data.get("id")},
                status="SUCCESS",
            )

            # Send notification to candidate when interview is created (only if interview is scheduled)
            try:
                interview_id = response.data.get("id")
                if interview_id:
                    from .models import Interview

                    interview = Interview.objects.get(id=interview_id)
                    # Only send notification if interview has a status that indicates it's scheduled
                    if interview.status in ["scheduled", "confirmed"]:
                        NotificationService.send_candidate_interview_scheduled_notification(
                            interview
                        )
            except Exception as e:
                # Log notification failure but don't fail the request
                ActionLogger.log_user_action(
                    user=request.user,
                    action="interview_notification_failed",
                    details={"interview_id": response.data.get("id"), "error": str(e)},
                    status="FAILED",
                )

            return response
        except Exception as e:
            ActionLogger.log_user_action(
                user=request.user,
                action="interview_create",
                details={"error": str(e)},
                status="FAILED",
            )
            raise

    def perform_create(self, serializer):
        candidate = serializer.validated_data.get("candidate")
        job = serializer.validated_data.get("job") or getattr(candidate, "job", None)

        if not job:
            raise ValidationError(
                {"job": "A job with a configured coding language is required before scheduling an interview."}
            )

        if not job.coding_language:
            raise ValidationError(
                {"job": f"Job '{job.job_title}' is missing a coding language. Please update the job before scheduling."}
            )

        serializer.save(job=job)

    def perform_update(self, serializer):
        candidate = serializer.validated_data.get("candidate") or serializer.instance.candidate
        job = serializer.validated_data.get("job")

        if not job and candidate and getattr(candidate, "job", None):
            job = candidate.job

        if not job:
            raise ValidationError(
                {"job": "A job with a configured coding language is required before scheduling an interview."}
            )

        if not job.coding_language:
            raise ValidationError(
                {"job": f"Job '{job.job_title}' is missing a coding language. Please update the job before scheduling."}
            )

        serializer.save(job=job)

    def update(self, request, *args, **kwargs):
        """Log interview update"""
        response = super().update(request, *args, **kwargs)
        ActionLogger.log_user_action(
            user=request.user,
            action="interview_update",
            details={"interview_id": kwargs.get("pk")},
            status="SUCCESS",
        )
        return response

    def partial_update(self, request, *args, **kwargs):
        """Log interview partial update"""
        response = super().partial_update(request, *args, **kwargs)
        ActionLogger.log_user_action(
            user=request.user,
            action="interview_partial_update",
            details={"interview_id": kwargs.get("pk")},
            status="SUCCESS",
        )
        return response

    def destroy(self, request, *args, **kwargs):
        """Log interview deletion"""
        ActionLogger.log_user_action(
            user=request.user,
            action="interview_delete",
            details={"interview_id": kwargs.get("pk")},
            status="SUCCESS",
        )
        return super().destroy(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["patch"],
        url_path="feedback",
        permission_classes=[IsAdminOnly],
    )
    def edit_feedback(self, request, pk=None):
        """
        PATCH /api/interviews/<id>/feedback/
        Admin‑only endpoint to update interview feedback.
        """
        interview = self.get_object()
        serializer = InterviewFeedbackSerializer(
            interview, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            ActionLogger.log_user_action(
                user=request.user,
                action="interview_feedback_update",
                details={"interview_id": pk},
                status="SUCCESS",
            )
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InterviewStatusSummaryView(APIView):
    """
    GET /api/interviews/summary/  → { "scheduled": 5, "completed": 2, ... }
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get interview status summary"""
        user_role = getattr(request.user, "role", "").lower()

        if user_role == "admin" or request.user.is_superuser:
            # Admin sees all interviews
            queryset = Interview.objects.all()
        else:
            # Others see only their candidates' interviews
            queryset = Interview.objects.filter(candidate__recruiter=request.user)

        summary = {
            "scheduled": queryset.filter(status="scheduled").count(),
            "completed": queryset.filter(status="completed").count(),
            "error": queryset.filter(status="error").count(),
            "total": queryset.count(),
        }

        ActionLogger.log_user_action(
            user=request.user,
            action="interview_summary",
            details=summary,
            status="SUCCESS",
        )

        return Response(summary)


class InterviewListCreateView(DataIsolationMixin, generics.ListCreateAPIView):
    """
    List and create interviews
    """

    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer
    permission_classes = [InterviewHierarchyPermission]

    def get_queryset(self):
        user_role = getattr(self.request.user, "role", "").lower()

        if user_role == "admin" or self.request.user.is_superuser:
            return Interview.objects.all()
        else:
            return Interview.objects.filter(candidate__recruiter=self.request.user)


class InterviewDetailView(DataIsolationMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an interview
    """

    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer
    permission_classes = [InterviewHierarchyPermission]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return InterviewSerializer
        return InterviewSerializer


class InterviewGenerateLinkView(DataIsolationMixin, generics.GenericAPIView):
    """
    Generate a secure interview link for the candidate
    """

    queryset = Interview.objects.all()
    permission_classes = [InterviewHierarchyPermission]

    def post(self, request, pk=None):
        """
        Generate a secure interview link for the candidate
        """
        interview = self.get_object()

        try:
            link_token = interview.generate_interview_link()
            if link_token:
                ActionLogger.log_user_action(
                    user=request.user,
                    action="interview_link_generated",
                    details={
                        "interview_id": str(interview.id),
                        "candidate_email": interview.candidate.email,
                        "link_expires_at": (
                            interview.link_expires_at.isoformat()
                            if interview.link_expires_at
                            else None
                        ),
                    },
                    status="SUCCESS",
                )

                return Response(
                    {
                        "link_token": link_token,
                        "interview_url": f"{request.build_absolute_uri('/')}api/interviews/public/{link_token}/",
                        "expires_at": (
                            interview.link_expires_at.isoformat()
                            if interview.link_expires_at
                            else None
                        ),
                        "message": "Interview link generated successfully",
                    }
                )
            else:
                return Response(
                    {
                        "error": "Could not generate interview link. Interview must have a start time."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            ActionLogger.log_user_action(
                user=request.user,
                action="interview_link_generation_failed",
                details={"interview_id": str(interview.id), "error": str(e)},
                status="FAILED",
            )

            return Response(
                {"error": f"Failed to generate interview link: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InterviewFeedbackView(generics.UpdateAPIView):
    """
    Update interview feedback (admin only)
    """

    queryset = Interview.objects.all()
    serializer_class = InterviewFeedbackSerializer
    permission_classes = [InterviewHierarchyPermission]


class InterviewSlotViewSet(DataIsolationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing AI interview slots
    """

    serializer_class = InterviewSlotSerializer
    permission_classes = [InterviewHierarchyPermission]

    def get_queryset(self):
        user_role = getattr(self.request.user, "role", "").lower()

        if user_role == "admin" or self.request.user.is_superuser:
            base_queryset = InterviewSlot.objects.all()
        elif user_role == "company":
            base_queryset = InterviewSlot.objects.filter(
                company=self.request.user.company
            )
        elif user_role in ["hiring_agency", "recruiter"]:
            base_queryset = InterviewSlot.objects.filter(
                company=self.request.user.company
            )
        else:
            base_queryset = InterviewSlot.objects.none()

        # Filter by status if provided in query parameters
        status = self.request.query_params.get("status")
        if status:
            base_queryset = base_queryset.filter(status=status)
            # For available status, show all slots for the date (not just future ones)
            # This allows the TimeSlotPicker to display created slots as unavailable
            # if status == 'available':
            #     from django.utils import timezone
            #     base_queryset = base_queryset.filter(start_time__gt=timezone.now())

        # Filter by date if provided in query parameters
        date = self.request.query_params.get("date")
        if date:
            base_queryset = base_queryset.filter(interview_date=date)

        return base_queryset.order_by("-created_at")

    def perform_create(self, serializer):
        user_role = getattr(self.request.user, "role", "").lower()

        # Log the ai_configuration being saved
        validated_data = serializer.validated_data
        if 'ai_configuration' in validated_data:
            ai_config = validated_data.get('ai_configuration', {})
            print(f"📋 Saving InterviewSlot with ai_configuration: {ai_config}")
            if isinstance(ai_config, dict) and 'question_count' in ai_config:
                print(f"✅ question_count found in ai_configuration: {ai_config['question_count']}")

        if user_role == "admin" or self.request.user.is_superuser:
            # Admin can create slots for any company - let the serializer handle it
            slot = serializer.save()
            # Verify question_count was saved
            if slot.ai_configuration and isinstance(slot.ai_configuration, dict):
                print(f"✅ Slot created with ai_configuration: {slot.ai_configuration}")
                if 'question_count' in slot.ai_configuration:
                    print(f"✅ question_count successfully saved: {slot.ai_configuration['question_count']}")
                else:
                    print(f"⚠️ WARNING: question_count NOT found in saved slot.ai_configuration")
                    print(f"   Available keys: {list(slot.ai_configuration.keys())}")
        elif user_role == "company":
            # Company users can only create slots for their company
            if hasattr(self.request.user, "company") and self.request.user.company:
                slot = serializer.save(company=self.request.user.company)
                # Verify question_count was saved
                if slot.ai_configuration and isinstance(slot.ai_configuration, dict):
                    print(f"✅ Slot created with ai_configuration: {slot.ai_configuration}")
                    if 'question_count' in slot.ai_configuration:
                        print(f"✅ question_count successfully saved: {slot.ai_configuration['question_count']}")
                    else:
                        print(f"⚠️ WARNING: question_count NOT found in saved slot.ai_configuration")
                        print(f"   Available keys: {list(slot.ai_configuration.keys())}")
            else:
                raise PermissionDenied("Company user must be associated with a company")
        else:
            raise PermissionDenied(
                "You don't have permission to create interview slots"
            )

    @action(detail=False, methods=["post"])
    def search_available(self, request):
        """
        Search for available slots based on criteria
        """
        serializer = SlotSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        queryset = self.get_queryset().filter(
            status="available",
            interview_date__gte=data["start_date"],
            interview_date__lte=data["end_date"],
        )

        if data.get("company_id"):
            queryset = queryset.filter(company_id=data["company_id"])

        if data.get("ai_interview_type"):
            queryset = queryset.filter(ai_interview_type=data["ai_interview_type"])

        if data.get("job_id"):
            queryset = queryset.filter(job_id=data["job_id"])

        if data.get("start_time") and data.get("end_time"):
            queryset = queryset.filter(
                start_time__gte=data["start_time"], end_time__lte=data["end_time"]
            )

        if data.get("duration_minutes"):
            queryset = queryset.filter(duration_minutes__gte=data["duration_minutes"])

        # Filter by availability
        available_slots = [slot for slot in queryset if slot.is_available()]

        page = self.paginate_queryset(available_slots)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(available_slots, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def create_recurring(self, request):
        """
        Create recurring slots based on pattern
        """
        serializer = RecurringSlotSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Get company
        try:
            from companies.models import Company

            company = Company.objects.get(id=data["company_id"])
        except Company.DoesNotExist:
            return Response(
                {"error": "Company not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create slots for each day in the pattern
        created_slots = []
        skipped_slots = []
        current_date = data["start_date"]

        while current_date <= data["end_date"]:
            if (
                current_date.weekday() + 1 in data["days_of_week"]
            ):  # weekday() returns 0-6, we need 1-7
                # Create slot for this day
                slot_start = datetime.combine(current_date, data["start_time"])
                slot_end = datetime.combine(current_date, data["end_time"])

                # Make timezone-aware
                from django.utils import timezone

                slot_start = timezone.make_aware(slot_start)
                slot_end = timezone.make_aware(slot_end)

                # Check for conflicts - check for time overlaps on the same date
                from datetime import datetime

                slot_date = datetime.combine(current_date, slot_start).date()

                conflicting_slots = InterviewSlot.objects.filter(
                    company=company,
                    interview_date=slot_date,
                    start_time__lt=slot_end,
                    end_time__gt=slot_start,
                    status__in=["available", "booked"],
                )

                if not conflicting_slots.exists():
                    try:
                        slot = InterviewSlot.objects.create(
                            slot_type="recurring",
                            interview_date=current_date,
                            start_time=slot_start.time(),
                            end_time=slot_end.time(),
                            duration_minutes=data["slot_duration"],
                            company=company,
                            job_id=data.get("job_id"),
                            ai_interview_type=data["ai_interview_type"],
                            ai_configuration=data.get("ai_configuration", {}),
                            is_recurring=True,
                            recurring_pattern={
                                "days_of_week": data["days_of_week"],
                                "start_time": data["start_time"].isoformat(),
                                "end_time": data["end_time"].isoformat(),
                                "slot_duration": data["slot_duration"],
                                "break_duration": data["break_duration"],
                            },
                            notes=data.get("notes", ""),
                            max_candidates=data["max_candidates_per_slot"],
                        )
                        created_slots.append(slot)
                    except Exception as e:
                        skipped_slots.append(
                            {"date": current_date.isoformat(), "reason": str(e)}
                        )
                else:
                    skipped_slots.append(
                        {
                            "date": current_date.isoformat(),
                            "reason": "Time conflict with existing slot",
                        }
                    )

            current_date += timedelta(days=1)

        serializer = self.get_serializer(created_slots, many=True)
        return Response(
            {
                "message": f"Created {len(created_slots)} recurring slots",
                "created_slots": len(created_slots),
                "slots": serializer.data,
                "skipped_slots": skipped_slots,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def book_slot(self, request, pk=None):
        """
        Book a slot for an interview
        """
        slot = self.get_object()
        
        # Debug logging
        import json
        print(f"\n{'='*70}")
        print(f"DEBUG: book_slot called for slot {pk}")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request content_type: {request.content_type}")
        print(f"DEBUG: Request data type: {type(request.data)}")
        print(f"DEBUG: Request data: {request.data}")
        print(f"DEBUG: User: {request.user.email if request.user.is_authenticated else 'Anonymous'}")
        print(f"{'='*70}\n")
        
        # Try to get data from request body if request.data is empty
        request_body = None
        try:
            if hasattr(request, 'body') and request.body:
                request_body = json.loads(request.body.decode('utf-8'))
                print(f"DEBUG: Parsed request body from raw body: {request_body}")
        except Exception as e:
            print(f"DEBUG: Could not parse request body: {e}")
        
        # DRF should automatically parse JSON, but sometimes request.data is empty
        # Try to use request.data first, then fallback to parsed body
        if request.data and (isinstance(request.data, dict) and len(request.data) > 0):
            data_source = request.data
            print(f"DEBUG: Using request.data as data_source")
        elif request_body:
            data_source = request_body
            print(f"DEBUG: Using request_body as data_source (request.data was empty)")
        else:
            data_source = request.data if request.data else {}
            print(f"DEBUG: Using request.data as fallback (may be empty)")
        
        print(f"DEBUG: Final data_source: {data_source}")
        print(f"DEBUG: data_source type: {type(data_source)}")
        print(f"DEBUG: Slot current_bookings: {slot.current_bookings}, max_candidates: {slot.max_candidates}, status: {slot.status}")

        # Try to get interview_id from multiple sources
        interview_id = None
        booking_notes = ""
        
        # Try data_source first (most reliable - this is the parsed JSON)
        if isinstance(data_source, dict):
            interview_id = data_source.get("interview_id") or data_source.get("interview")
            booking_notes = data_source.get("booking_notes", "")
            print(f"DEBUG: Found in data_source: interview_id={interview_id}, booking_notes={booking_notes}")
        
        # Fallback to request.data (DRF parsed)
        if not interview_id and isinstance(request.data, dict) and len(request.data) > 0:
            interview_id = request.data.get("interview_id") or request.data.get("interview")
            if not booking_notes:
                booking_notes = request.data.get("booking_notes", "")
            print(f"DEBUG: Found in request.data: interview_id={interview_id}, booking_notes={booking_notes}")
        
        # Fallback to request_body (manually parsed)
        if not interview_id and request_body and isinstance(request_body, dict):
            interview_id = request_body.get("interview_id") or request_body.get("interview")
            if not booking_notes:
                booking_notes = request_body.get("booking_notes", "")
            print(f"DEBUG: Found in request_body: interview_id={interview_id}, booking_notes={booking_notes}")
        
        # Try to get from query parameters as last resort
        if not interview_id:
            interview_id = request.query_params.get("interview_id")
            print(f"DEBUG: Found in query_params: interview_id={interview_id}")
        
        print(f"DEBUG: FINAL interview_id: {interview_id}")
        print(f"DEBUG: FINAL booking_notes: {booking_notes}")
        print(f"DEBUG: data_source keys: {list(data_source.keys()) if isinstance(data_source, dict) else 'N/A'}")
        print(f"DEBUG: request.data keys: {list(request.data.keys()) if isinstance(request.data, dict) else 'N/A'}")
        print(f"DEBUG: request_body keys: {list(request_body.keys()) if isinstance(request_body, dict) and request_body else 'N/A'}")
        print(f"DEBUG: Content-Type header: {request.META.get('CONTENT_TYPE', 'NOT SET')}")
        
        if not interview_id:
            error_msg = "interview_id is required in request body"
            print(f"DEBUG: ERROR - {error_msg}")
            print(f"DEBUG: Full request.data: {request.data}")
            print(f"DEBUG: Full request_body: {request_body}")
            print(f"DEBUG: Full data_source: {data_source}")
            print(f"DEBUG: Request META: {dict(request.META.get('CONTENT_TYPE', ''))}")
            return Response(
                {
                    "error": error_msg, 
                    "received_data": dict(data_source) if isinstance(data_source, dict) else str(data_source),
                    "request_data": dict(request.data) if isinstance(request.data, dict) else str(request.data),
                    "request_body": dict(request_body) if isinstance(request_body, dict) else str(request_body),
                    "help": "Please send interview_id in the request body as JSON: {\"interview_id\": \"<uuid>\", \"booking_notes\": \"optional notes\"}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            interview = Interview.objects.get(id=interview_id)
            print(f"DEBUG: Found interview: {interview.id}, candidate: {interview.candidate.email if interview.candidate else 'N/A'}")
            
            # CRITICAL: Validate candidate email exists before proceeding
            if not interview.candidate:
                return Response(
                    {"error": "Interview has no associated candidate"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not interview.candidate.email:
                return Response(
                    {"error": "Candidate email is missing - cannot send interview notification"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Interview.DoesNotExist:
            error_msg = f"Interview not found with id: {interview_id}"
            print(f"DEBUG: {error_msg}")
            return Response(
                {"error": error_msg, "interview_id_provided": str(interview_id)}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            error_msg = f"Error retrieving interview: {str(e)}"
            print(f"DEBUG: {error_msg}")
            return Response(
                {"error": error_msg, "interview_id_provided": str(interview_id)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure interview is linked to a job so we have a coding language source
        if not interview.job:
            job_source = None
            if slot.job:
                job_source = slot.job
                print(f"DEBUG: Using job from slot {slot.id}: {slot.job.id}")
            elif interview.candidate and getattr(interview.candidate, "job", None):
                job_source = interview.candidate.job
                print(f"DEBUG: Using job from candidate {interview.candidate.id}: {job_source.id}")

            if job_source:
                interview.job = job_source
                interview.save(update_fields=["job"])
                print(f"✅ Linked interview {interview.id} to job {job_source.id}")
            else:
                return Response(
                    {
                        "error": (
                            "Coding language not configured: this interview is not linked to any job. "
                            "Please assign a job with a coding language before scheduling."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not interview.job.coding_language:
            return Response(
                {
                    "error": (
                        f"Job '{interview.job.job_title}' is missing a coding language. "
                        "Update the job to set coding_language before scheduling."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


        # Check if interview already has a schedule for this slot
        existing_schedule = InterviewSchedule.objects.filter(
            interview=interview,
            slot=slot
        ).first()
        
        if existing_schedule:
            # Update existing schedule (allow rescheduling to same slot)
            print(f"DEBUG: Interview {interview.id} already has schedule {existing_schedule.id} for slot {slot.id} - updating")
            existing_schedule.booking_notes = booking_notes
            existing_schedule.status = "pending"
            existing_schedule.save()
            schedule = existing_schedule
            # Don't call slot.book_slot() again - slot is already booked
            print(f"DEBUG: Skipping slot.book_slot() - schedule already exists for this slot")
        else:
            # Check if slot has capacity BEFORE creating schedule
            # CRITICAL: Frontend may have already updated slot.current_bookings via PUT request
            # So we need to check if a schedule can be created even if slot appears full
            current_bookings = slot.current_bookings or 0
            max_candidates = slot.max_candidates or 1
            
            # Check if this interview already has a schedule for a different slot
            other_schedule = InterviewSchedule.objects.filter(interview=interview).exclude(slot=slot).first()
            
            # Check if slot appears full (current_bookings >= max_candidates)
            if current_bookings >= max_candidates:
                # Check if this interview is the one that booked the slot (by checking slot's schedules)
                slot_schedules = InterviewSchedule.objects.filter(slot=slot)
                interview_has_schedule_for_slot = slot_schedules.filter(interview=interview).exists()
                
                if interview_has_schedule_for_slot:
                    # This interview already has a schedule for this slot - just update it
                    schedule = slot_schedules.filter(interview=interview).first()
                    schedule.booking_notes = booking_notes
                    schedule.status = "pending"
                    schedule.save()
                    print(f"DEBUG: Found existing schedule for this interview+slot - updated")
                elif other_schedule:
                    # Interview has schedule for different slot - allow updating to this slot
                    print(f"DEBUG: Interview has schedule for different slot - updating to new slot")
                    other_schedule.slot = slot
                    other_schedule.booking_notes = booking_notes
                    other_schedule.status = "pending"
                    other_schedule.save()
                    schedule = other_schedule
                    # Don't call slot.book_slot() - slot might already be booked by frontend
                    print(f"DEBUG: Updated schedule to new slot - not calling slot.book_slot()")
                else:
                    # Slot appears full but no schedule exists for this interview
                    # This could mean:
                    # 1. Frontend updated slot but no schedule created yet (race condition)
                    # 2. Slot is actually booked by another interview
                    # 
                    # Strategy: Allow creating schedule if slot.current_bookings == max_candidates
                    # and no other interview has a schedule for this slot
                    # (This handles the case where frontend updated slot but book_slot hasn't created schedule yet)
                    other_interviews_with_schedule = slot_schedules.exclude(interview=interview).count()
                    
                    if other_interviews_with_schedule == 0:
                        # No other interviews have schedule - frontend must have updated slot for this interview
                        # Allow creating schedule (frontend already booked the slot)
                        print(f"DEBUG: Slot appears full but no schedules exist - frontend likely updated it")
                        print(f"DEBUG: Creating schedule (frontend already booked slot)")
                        schedule = InterviewSchedule.objects.create(
                            interview=interview,
                            slot=slot,
                            booking_notes=booking_notes,
                            status="pending",
                        )
                        # Don't call slot.book_slot() - frontend already did it
                        print(f"DEBUG: Created schedule {schedule.id} - slot already booked by frontend")
                    else:
                        # Slot is fully booked by other interviews
                        error_msg = f"Slot is fully booked (current_bookings={current_bookings} >= max_candidates={max_candidates}) by other interviews"
                        print(f"DEBUG: {error_msg}")
                        return Response(
                            {"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
            else:
                # Slot has capacity - create new schedule and book the slot
                schedule = InterviewSchedule.objects.create(
                    interview=interview,
                    slot=slot,
                    booking_notes=booking_notes,
                    status="pending",
                )
                # Book the slot (increments current_bookings and updates status if needed)
                # Only if slot hasn't been booked yet by frontend
                if slot.current_bookings < max_candidates:
                    slot.book_slot()
                    print(f"DEBUG: Created new schedule {schedule.id} and called slot.book_slot()")
                else:
                    print(f"DEBUG: Created new schedule {schedule.id} but slot already booked (frontend updated it)")

        # IMPORTANT: ALWAYS update interview started_at and ended_at from slot date + time
        # This ensures times match the slot even if interview was created with different times
        # Combine slot.interview_date with slot.start_time and slot.end_time to create proper DateTime objects
        # IMPORTANT: Interpret slot times in IST (Asia/Kolkata) since that's likely where users are
        from datetime import datetime
        from django.utils import timezone as tz
        import pytz
        
        if slot.interview_date and slot.start_time and slot.end_time:
            # Combine date and time - assume slot times are in IST (India Standard Time)
            ist = pytz.timezone('Asia/Kolkata')
            start_datetime_naive = datetime.combine(slot.interview_date, slot.start_time)
            end_datetime_naive = datetime.combine(slot.interview_date, slot.end_time)
            
            # Localize to IST (treat slot times as IST)
            start_datetime = ist.localize(start_datetime_naive)
            end_datetime = ist.localize(end_datetime_naive)
            
            # Convert to UTC for storage (Django stores in UTC)
            start_datetime_utc = start_datetime.astimezone(pytz.UTC)
            end_datetime_utc = end_datetime.astimezone(pytz.UTC)
            
            # ALWAYS update interview times to match slot (stored in UTC) - overwrite any existing values
            # Also set interview.slot directly for easier access (in addition to InterviewSchedule)
            interview.started_at = start_datetime_utc
            interview.ended_at = end_datetime_utc
            interview.status = Interview.Status.SCHEDULED
            interview.slot = slot  # Set slot directly for easier access
            interview.save(update_fields=["started_at", "ended_at", "status", "slot"])

        # Auto-create InterviewSession from database and send email (if not exists)
        try:
            from interview_app.models import InterviewSession
            import secrets
            
            # Only create if session_key doesn't exist
            if not interview.session_key:
                candidate = interview.candidate
                job = interview.job
                
                if candidate:
                    if job and getattr(job, 'coding_language', None):
                        coding_language = str(job.coding_language).upper()
                    else:
                        raise ValueError("Interview job missing coding_language; cannot create coding session.")
                    
                    # Get scheduled time (already set above)
                    scheduled_at = interview.started_at
                    if not scheduled_at:
                        if slot.interview_date and slot.start_time:
                            ist = pytz.timezone('Asia/Kolkata')
                            start_dt = datetime.combine(slot.interview_date, slot.start_time)
                            scheduled_at = ist.localize(start_dt).astimezone(pytz.UTC)
                    
                    if not scheduled_at:
                        scheduled_at = timezone.now()
                    
                    # Extract resume text
                    resume_text = ""
                    if candidate.resume:
                        try:
                            if hasattr(candidate.resume, 'parsed_text') and candidate.resume.parsed_text:
                                resume_text = candidate.resume.parsed_text
                            elif hasattr(candidate.resume, 'file') and candidate.resume.file:
                                from interview_app.views import get_text_from_file
                                resume_text = get_text_from_file(candidate.resume.file) or ""
                        except Exception as e:
                            print(f"Warning: Could not extract resume text: {e}")
                            resume_text = f"Resume for {candidate.full_name or 'Candidate'}"
                    
                    # Build job description (handle job being None)
                    if job:
                        job_description = job.job_description or f"Job Title: {job.job_title}\nCompany: {job.company_name}"
                        if job.domain:
                            job_description += f"\nDomain: {job.domain.name}"
                    elif candidate.job:
                        job_description = candidate.job.job_description or f"Job Title: {candidate.job.job_title}\nCompany: {candidate.job.company_name}"
                    else:
                        job_description = "Interview Position"
                    
                    # Generate session key
                    session_key = secrets.token_hex(16)
                    
                    # Create InterviewSession
                    session = InterviewSession.objects.create(
                        candidate_name=candidate.full_name or "Candidate",
                        candidate_email=candidate.email or "",
                        job_description=job_description,
                        resume_text=resume_text,
                        session_key=session_key,
                        scheduled_at=scheduled_at,
                        status='SCHEDULED',
                        language_code='en-IN',
                        accent_tld='co.in'
                    )
                    
                    # Update Interview with session_key
                    interview.session_key = session_key
                    interview.save(update_fields=['session_key'])
                    
                    print(f"✅ InterviewSession created for interview {interview.id}, session_key: {session_key}")
                    
            # Send email notification using NotificationService (asynchronously to prevent timeout)
            if interview.candidate and interview.candidate.email:
                import threading
                def send_email_async():
                    try:
                        from notifications.services import NotificationService
                        result = NotificationService.send_candidate_interview_scheduled_notification(interview)
                        if result:
                            print(f"✅ Email sent successfully via NotificationService for interview {interview.id}")
                            logger.info(f"✅ Email sent successfully for interview {interview.id} to {interview.candidate.email}")
                        else:
                            print(f"⚠️ Email sending returned False for interview {interview.id}")
                            logger.warning(f"⚠️ Email sending returned False for interview {interview.id}")
                    except Exception as e:
                        error_msg = str(e)
                        print(f"❌ NotificationService email failed for interview {interview.id}: {error_msg}")
                        logger.error(f"❌ Email sending failed for interview {interview.id}: {error_msg}")
                        import traceback
                        traceback.print_exc()
                
                # Start email sending in background thread
                email_thread = threading.Thread(target=send_email_async, daemon=True)
                email_thread.start()
                print(f"📧 Email sending started in background thread for interview {interview.id}")
                logger.info(f"📧 Email sending started in background for interview {interview.id}")
            else:
                print(f"\n{'='*70}")
                print(f"⚠️ WARNING: Cannot send email - candidate or email missing")
                print(f"⚠️ Interview ID: {interview.id}")
                print(f"⚠️ Candidate: {'EXISTS' if interview.candidate else 'MISSING'}")
                print(f"⚠️ Email: {interview.candidate.email if interview.candidate else 'N/A'}")
                print(f"{'='*70}\n")
                logger.warning(f"⚠️ Cannot send email for interview {interview.id} - candidate or email missing")
                    
        except Exception as e:
            print(f"⚠️ Auto-creation of InterviewSession failed: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"⚠️ Auto-creation of InterviewSession failed: {e}")

        print(f"DEBUG: Schedule created successfully: {schedule.id}")
        print(f"DEBUG: Interview: {interview.id}, Status: {interview.status}")
        print(f"DEBUG: Interview started_at: {interview.started_at}, ended_at: {interview.ended_at}")
        print(f"DEBUG: Interview session_key: {interview.session_key}")
        print(f"DEBUG: About to send email notification...")
        print(f"{'='*70}\n")
        
        serializer = InterviewScheduleSerializer(schedule)
        response_data = serializer.data
        
        # Log successful booking
        print(f"\n{'='*70}")
        print(f"SUCCESS: Slot booking completed for interview {interview.id}")
        print(f"SUCCESS: Schedule ID: {schedule.id}")
        print(f"SUCCESS: Session Key: {interview.session_key}")
        print(f"{'='*70}\n")
        
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def release_slot(self, request, pk=None):
        """
        Release a booking from a slot
        """
        slot = self.get_object()

        # First, cancel any active schedules for this slot
        active_schedules = slot.schedules.filter(status__in=["pending", "confirmed"])
        for schedule in active_schedules:
            schedule.cancel_schedule(
                reason="Slot released by admin", cancelled_by=request.user
            )

        # Ensure the slot is available
        slot.refresh_from_db()
        if slot.current_bookings > 0:
            slot.release_slot()

        # Force the slot to be available
        slot.status = slot.Status.AVAILABLE
        slot.current_bookings = 0
        slot.save()

        return Response(
            {
                "message": "Slot released successfully",
                "slot_available": slot.is_available(),
                "current_bookings": slot.current_bookings,
                "max_candidates": slot.max_candidates,
            }
        )


class InterviewScheduleViewSet(DataIsolationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing AI interview schedules
    """

    serializer_class = InterviewScheduleSerializer
    permission_classes = [InterviewHierarchyPermission]

    def get_queryset(self):
        user_role = getattr(self.request.user, "role", "").lower()

        if user_role == "admin" or self.request.user.is_superuser:
            base_queryset = InterviewSchedule.objects.all()
        elif user_role == "company":
            base_queryset = InterviewSchedule.objects.filter(
                slot__company=self.request.user.company
            )
        elif user_role in ["hiring_agency", "recruiter"]:
            base_queryset = InterviewSchedule.objects.filter(
                slot__company=self.request.user.company
            )
        else:
            base_queryset = InterviewSchedule.objects.none()

        return base_queryset.order_by("-booked_at")

    @action(detail=False, methods=["post"])
    def book_interview(self, request):
        """
        Book an interview to a slot
        """
        serializer = SlotBookingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        interview = data["interview"]
        slot = data["slot"]

        # Check if interview already has a schedule
        existing_schedule = getattr(interview, "schedule", None)
        if existing_schedule:
            # Update existing schedule
            existing_schedule.slot = slot
            existing_schedule.booking_notes = data.get("booking_notes", "")
            existing_schedule.status = "pending"
            existing_schedule.save()
            schedule = existing_schedule
        else:
            # Create new schedule
            schedule = InterviewSchedule.objects.create(
                interview=interview,
                slot=slot,
                booking_notes=data.get("booking_notes", ""),
                status="pending",
            )

        # Book the slot
        slot.book_slot()

        # IMPORTANT: ALWAYS update interview started_at and ended_at from slot date + time
        # This ensures times match the slot even if interview was created with different times
        # Combine slot.interview_date with slot.start_time and slot.end_time to create proper DateTime objects
        # IMPORTANT: Interpret slot times in IST (Asia/Kolkata) since that's likely where users are
        from datetime import datetime, date, time as time_type
        from django.utils import timezone as tz
        import pytz
        
        if slot.interview_date and slot.start_time and slot.end_time:
            # Combine date and time - assume slot times are in IST (India Standard Time)
            ist = pytz.timezone('Asia/Kolkata')
            start_datetime_naive = datetime.combine(slot.interview_date, slot.start_time)
            end_datetime_naive = datetime.combine(slot.interview_date, slot.end_time)
            
            # Localize to IST (treat slot times as IST)
            start_datetime = ist.localize(start_datetime_naive)
            end_datetime = ist.localize(end_datetime_naive)
            
            # Convert to UTC for storage (Django stores in UTC)
            start_datetime_utc = start_datetime.astimezone(pytz.UTC)
            end_datetime_utc = end_datetime.astimezone(pytz.UTC)
            
            # ALWAYS update interview times to match slot (stored in UTC) - overwrite any existing values
            # Also set interview.slot directly for easier access (in addition to InterviewSchedule)
            interview.started_at = start_datetime_utc
            interview.ended_at = end_datetime_utc
            interview.status = Interview.Status.SCHEDULED
            interview.slot = slot  # Set slot directly for easier access
            interview.save(update_fields=["started_at", "ended_at", "status", "slot"])
        
        # Send notification to candidate when interview is scheduled
        try:
            from notifications.services import NotificationService

            NotificationService.send_candidate_interview_scheduled_notification(
                interview
            )
        except Exception as e:
            # Log notification failure but don't fail the request
            ActionLogger.log_user_action(
                user=request.user,
                action="interview_booking_notification_failed",
                details={
                    "interview_id": interview.id,
                    "schedule_id": schedule.id,
                    "error": str(e),
                },
                status="FAILED",
            )

        # Auto-create InterviewSession from database (if not exists)
        try:
            from interview_app.models import InterviewSession
            import secrets
            
            # Only create if session_key doesn't exist
            if not interview.session_key:
                candidate = interview.candidate
                job = interview.job
                
                if candidate and job:
                    # Get coding language from job
                    coding_language = getattr(job, 'coding_language', 'PYTHON')
                    
                    # Get scheduled time
                    scheduled_at = interview.started_at
                    if not scheduled_at:
                        slot = interview.schedule.slot if hasattr(interview, 'schedule') and interview.schedule else None
                        if slot and slot.interview_date and slot.start_time:
                            import pytz
                            from datetime import datetime
                            ist = pytz.timezone('Asia/Kolkata')
                            start_dt = datetime.combine(slot.interview_date, slot.start_time)
                            scheduled_at = ist.localize(start_dt).astimezone(pytz.UTC)
                    
                    if not scheduled_at:
                        scheduled_at = timezone.now()
                    
                    # Extract resume text
                    resume_text = ""
                    if candidate.resume:
                        try:
                            if hasattr(candidate.resume, 'parsed_text') and candidate.resume.parsed_text:
                                resume_text = candidate.resume.parsed_text
                            elif hasattr(candidate.resume, 'file') and candidate.resume.file:
                                from interview_app.views import get_text_from_file
                                resume_text = get_text_from_file(candidate.resume.file) or ""
                        except Exception as e:
                            print(f"Warning: Could not extract resume text: {e}")
                            resume_text = f"Resume for {candidate.full_name or 'Candidate'}"
                    
                    # Build job description
                    job_description = job.job_description or f"Job Title: {job.job_title}\nCompany: {job.company_name}"
                    if job.domain:
                        job_description += f"\nDomain: {job.domain.name}"
                    
                    # Generate session key
                    session_key = secrets.token_hex(16)
                    
                    # Create InterviewSession
                    session = InterviewSession.objects.create(
                        candidate_name=candidate.full_name or "Candidate",
                        candidate_email=candidate.email or "",
                        job_description=job_description,
                        resume_text=resume_text,
                        session_key=session_key,
                        scheduled_at=scheduled_at,
                        status='SCHEDULED',
                        language_code='en-IN',
                        accent_tld='co.in'
                    )
                    
                    # Update Interview with session_key
                    interview.session_key = session_key
                    interview.save(update_fields=['session_key'])
                    
                    # Send email notification using NotificationService (already handled above)
                    # Email is sent via NotificationService.send_candidate_interview_scheduled_notification
                    # which is called earlier in this function
                    print(f"✅ InterviewSession created for interview {interview.id}")
        except Exception as e:
            print(f"⚠️ Auto-creation of InterviewSession failed: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail the booking if InterviewSession creation fails

        serializer = self.get_serializer(schedule)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=["post"])
    def create_interview_session(self, request):
        """
        Create InterviewSession from database (Candidate, Job, InterviewSchedule)
        This replaces file-based scheduling with database-driven scheduling
        """
        try:
            from interview_app.models import InterviewSession
            from resumes.models import Resume
            import secrets
            
            interview_id = request.data.get('interview_id')
            if not interview_id:
                return Response(
                    {"error": "interview_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Fetch Interview from database
            try:
                interview = Interview.objects.select_related(
                    'candidate', 'job', 'slot'
                ).prefetch_related('schedule').get(id=interview_id)
            except Interview.DoesNotExist:
                return Response(
                    {"error": "Interview not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Fetch candidate details
            candidate = interview.candidate
            if not candidate:
                return Response(
                    {"error": "Candidate not found for this interview"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Fetch job details
            job = interview.job
            if not job:
                return Response(
                    {"error": "Job not found for this interview"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get coding language from job (default to PYTHON if not set)
            coding_language = getattr(job, 'coding_language', 'PYTHON')
            
            # Get scheduled time from interview or schedule
            scheduled_at = interview.started_at
            if not scheduled_at and hasattr(interview, 'schedule') and interview.schedule:
                # Combine slot date and time
                slot = interview.schedule.slot
                if slot.interview_date and slot.start_time:
                    import pytz
                    from datetime import datetime
                    ist = pytz.timezone('Asia/Kolkata')
                    start_datetime_naive = datetime.combine(slot.interview_date, slot.start_time)
                    scheduled_at = ist.localize(start_datetime_naive).astimezone(pytz.UTC)
            
            if not scheduled_at:
                from django.utils import timezone
                scheduled_at = timezone.now()
            
            # Get resume text if available
            resume_text = ""
            if candidate.resume:
                try:
                    resume = candidate.resume
                    # Try to read resume file
                    if hasattr(resume, 'file') and resume.file:
                        from interview_app.views import get_text_from_file
                        resume_text = get_text_from_file(resume.file) or ""
                    # Or use extracted text if available
                    elif hasattr(resume, 'extracted_text'):
                        resume_text = resume.extracted_text or ""
                except Exception as e:
                    print(f"Warning: Could not extract resume text: {e}")
                    resume_text = f"Resume for {candidate.full_name}"
            
            # Build job description from job
            job_description = job.job_description or f"Job Title: {job.job_title}\nCompany: {job.company_name}"
            if job.domain:
                job_description += f"\nDomain: {job.domain.name}"
            
            # Generate session key
            session_key = secrets.token_hex(16)
            
            # Create InterviewSession
            session = InterviewSession.objects.create(
                candidate_name=candidate.full_name or "Candidate",
                candidate_email=candidate.email or "",
                job_description=job_description,
                resume_text=resume_text,
                session_key=session_key,
                scheduled_at=scheduled_at,
                status='SCHEDULED',
                language_code='en-IN',
                accent_tld='co.in'
            )
            
            # Update Interview with session_key for reference
            interview.session_key = session_key
            interview.save(update_fields=['session_key'])
            
            # Generate interview link using utility function
            from interview_app.utils import get_interview_url
            interview_link = get_interview_url(session_key, request)
            
            # Send email notification using NotificationService
            email_sent = False
            try:
                from notifications.services import NotificationService
                email_sent = NotificationService.send_candidate_interview_scheduled_notification(interview)
                if email_sent:
                    print(f"✅ Email sent to {candidate.email}")
                else:
                    print(f"⚠️ Email sending failed for {candidate.email} - check email configuration")
            except Exception as e:
                print(f"⚠️ Email sending failed: {e}")
                import traceback
                traceback.print_exc()
            
            return Response({
                "success": True,
                "interview_link": interview_link,
                "session_key": session_key,
                "session_id": str(session.id),
                "candidate_name": candidate.full_name,
                "candidate_email": candidate.email,
                "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
                "coding_language": coding_language,
                "email_sent": email_sent if 'email_sent' in locals() else False
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Error creating interview session: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Failed to create interview session: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def confirm_schedule(self, request, pk=None):
        """
        Confirm an interview schedule
        """
        schedule = self.get_object()

        if schedule.status == "cancelled":
            return Response(
                {"error": "Cannot confirm a cancelled schedule"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedule.confirm_schedule()

        # Send notification to candidate when schedule is confirmed
        try:
            from notifications.services import NotificationService

            NotificationService.send_candidate_interview_scheduled_notification(
                schedule.interview
            )
        except Exception as e:
            # Log notification failure but don't fail the request
            ActionLogger.log_user_action(
                user=request.user,
                action="schedule_confirmation_notification_failed",
                details={"schedule_id": schedule.id, "error": str(e)},
                status="FAILED",
            )

        serializer = self.get_serializer(schedule)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel_schedule(self, request, pk=None):
        """
        Cancel an interview schedule
        """
        schedule = self.get_object()
        reason = request.data.get("reason", "")

        schedule.cancel_schedule(reason=reason, cancelled_by=request.user)
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)


class AIInterviewConfigurationViewSet(DataIsolationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing AI interview configurations
    """

    serializer_class = AIInterviewConfigurationSerializer
    permission_classes = [InterviewHierarchyPermission]

    def get_queryset(self):
        user_role = getattr(self.request.user, "role", "").lower()

        if user_role == "admin" or self.request.user.is_superuser:
            base_queryset = AIInterviewConfiguration.objects.all()
        elif user_role == "company":
            base_queryset = AIInterviewConfiguration.objects.filter(
                company=self.request.user.company
            )
        elif user_role in ["hiring_agency", "recruiter"]:
            base_queryset = AIInterviewConfiguration.objects.filter(
                company=self.request.user.company
            )
        else:
            base_queryset = AIInterviewConfiguration.objects.none()

        return base_queryset.order_by("-created_at")

    def perform_create(self, serializer):
        user_role = getattr(self.request.user, "role", "").lower()

        if user_role == "admin" or self.request.user.is_superuser:
            # Admin can create configurations for any company
            pass
        elif user_role == "company":
            # Company users can only create configurations for their company
            serializer.save(company=self.request.user.company)
        else:
            raise PermissionDenied(
                "You don't have permission to create AI interview configurations"
            )


class InterviewConflictViewSet(DataIsolationMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing interview conflicts (read-only)
    """

    serializer_class = InterviewConflictSerializer
    permission_classes = [InterviewHierarchyPermission]

    def get_queryset(self):
        user_role = getattr(self.request.user, "role", "").lower()

        if user_role == "admin" or self.request.user.is_superuser:
            base_queryset = InterviewConflict.objects.all()
        elif user_role == "company":
            base_queryset = InterviewConflict.objects.filter(
                primary_interview__schedule__slot__company=self.request.user.company
            )
        elif user_role in ["hiring_agency", "recruiter"]:
            base_queryset = InterviewConflict.objects.filter(
                primary_interview__schedule__slot__company=self.request.user.company
            )
        else:
            base_queryset = InterviewConflict.objects.none()

        return base_queryset.order_by("-detected_at")

    @action(detail=True, methods=["post"])
    def resolve_conflict(self, request, pk=None):
        """
        Resolve an interview conflict
        """
        conflict = self.get_object()
        resolution = request.data.get("resolution", "resolved")
        notes = request.data.get("resolution_notes", "")

        if resolution not in ["rescheduled", "cancelled", "resolved"]:
            return Response(
                {"error": "Invalid resolution"}, status=status.HTTP_400_BAD_REQUEST
            )

        conflict.resolution = resolution
        conflict.resolution_notes = notes
        conflict.resolved_at = timezone.now()
        conflict.resolved_by = request.user
        conflict.save()

        serializer = self.get_serializer(conflict)
        return Response(serializer.data)


class SlotAvailabilityView(generics.ListAPIView):
    """
    Get available slots with comprehensive filtering options

    Query Parameters:
    - date: Single date filter (YYYY-MM-DD)
    - company: Company filter by ID
    - company_id: Alternative company filter by ID
    - start_date: Date range start (YYYY-MM-DD)
    - end_date: Date range end (YYYY-MM-DD)
    - ai_interview_type: Filter by interview type (technical, behavioral, etc.)
    """

    serializer_class = InterviewSlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get all query parameters
        date = self.request.query_params.get("date")
        company = self.request.query_params.get("company")
        company_id = self.request.query_params.get("company_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        ai_interview_type = self.request.query_params.get("ai_interview_type")

        # Start with available slots
        queryset = InterviewSlot.objects.filter(status="available")

        # Date filtering - support both single date and date range
        if date:
            # Single date filter
            queryset = queryset.filter(interview_date=date)
        else:
            # Date range filtering
            if start_date:
                queryset = queryset.filter(interview_date__gte=start_date)

            if end_date:
                queryset = queryset.filter(interview_date__lte=end_date)

        # Company filtering - support both 'company' and 'company_id' parameters
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        elif company:
            queryset = queryset.filter(company_id=company)

        # AI interview type filtering
        if ai_interview_type:
            queryset = queryset.filter(ai_interview_type=ai_interview_type)

        # Apply data isolation based on user role
        user_role = getattr(self.request.user, "role", "").lower()

        if user_role == "admin" or self.request.user.is_superuser:
            pass  # Admin sees all slots
        elif user_role == "company":
            queryset = queryset.filter(company=self.request.user.company)
        elif user_role in ["hiring_agency", "recruiter"]:
            queryset = queryset.filter(company=self.request.user.company)
        else:
            queryset = InterviewSlot.objects.none()

        # Filter by actual availability (check if slot is truly available)
        available_slots = [slot for slot in queryset if slot.is_available()]
        return available_slots

    def list(self, request, *args, **kwargs):
        """
        Override list method to return the expected format
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Transform data to match the requested response format
        available_slots = []
        for slot_data in serializer.data:
            slot_info = {
                "id": slot_data["id"],
                "start_time": slot_data["start_time"],
                "end_time": slot_data["end_time"],
                "ai_interview_type": slot_data["ai_interview_type"],
                "company": slot_data["company"],
                "status": slot_data["status"],
                "current_bookings": slot_data["current_bookings"],
                "max_candidates": slot_data["max_candidates"],
            }
            available_slots.append(slot_info)

        return Response(
            {
                "available_slots": available_slots,
                "total_available": len(available_slots),
            }
        )


class InterviewCalendarView(generics.ListAPIView):
    """
    Get interview calendar view with slots and schedules
    """

    serializer_class = InterviewScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        queryset = InterviewSchedule.objects.select_related(
            "interview__candidate", "slot__company"
        )

        if start_date:
            queryset = queryset.filter(slot__interview_date__gte=start_date)

        if end_date:
            queryset = queryset.filter(slot__interview_date__lte=end_date)

        # Apply data isolation
        user_role = getattr(self.request.user, "role", "").lower()

        if user_role == "admin" or self.request.user.is_superuser:
            pass  # Admin sees all
        elif user_role == "company":
            queryset = queryset.filter(slot__company=self.request.user.company)
        elif user_role in ["hiring_agency", "recruiter"]:
            queryset = queryset.filter(slot__company=self.request.user.company)
        else:
            queryset = InterviewSchedule.objects.none()

        return queryset.order_by("slot__start_time")

    def list(self, request, *args, **kwargs):
        """
        Override list method to return calendar format
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Get slot statistics
        from .models import InterviewSlot

        total_slots = InterviewSlot.objects.count()
        available_slots = InterviewSlot.objects.filter(status="available").count()
        booked_slots = InterviewSlot.objects.filter(status="booked").count()

        return Response(
            {
                "calendar_data": serializer.data,
                "total_slots": total_slots,
                "available_slots": available_slots,
                "booked_slots": booked_slots,
            }
        )
