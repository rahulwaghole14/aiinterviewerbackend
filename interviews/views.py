# interviews/views.py
import logging
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models

from rest_framework import generics, status, viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import (
    Interview, InterviewSlot, InterviewSchedule, 
    AIInterviewConfiguration, InterviewConflict
)
from .serializers import (
    InterviewSerializer, InterviewFeedbackSerializer,
    InterviewSlotSerializer, InterviewScheduleSerializer,
    AIInterviewConfigurationSerializer, InterviewConflictSerializer,
    SlotBookingSerializer, SlotSearchSerializer, RecurringSlotSerializer
)
from utils.hierarchy_permissions import DataIsolationMixin, InterviewHierarchyPermission
from utils.logger import log_interview_schedule, log_permission_denied, ActionLogger
from notifications.services import NotificationService

logger = logging.getLogger(__name__)


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
class PublicInterviewAccessView(APIView):
    """
    Public endpoint for candidates to access interviews via secure links
    No authentication required - uses secure link validation
    """
    permission_classes = []  # No authentication required
    
    def get(self, request, link_token):
        """Get interview details for candidate access"""
        try:
            # Decode the link token
            import base64
            decoded_token = base64.urlsafe_b64decode(link_token.encode('utf-8')).decode('utf-8')
            interview_id, signature = decoded_token.split(':', 1)
            
            # Get the interview
            interview = Interview.objects.get(id=interview_id)
            
            # Validate the link
            is_valid, message = interview.validate_interview_link(link_token)
            
            if not is_valid:
                return Response({
                    'error': message,
                    'status': 'invalid_link'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Return interview details for candidate
            response_data = {
                'interview_id': str(interview.id),
                'candidate_name': interview.candidate.full_name,
                'candidate_email': interview.candidate.email,
                'job_title': interview.job.job_title if interview.job else 'N/A',
                'company_name': interview.job.company_name if interview.job else 'N/A',
                'interview_round': interview.interview_round,
                'scheduled_date': interview.started_at.strftime('%B %d, %Y') if interview.started_at else 'TBD',
                'scheduled_time': interview.started_at.strftime('%I:%M %p') if interview.started_at else 'TBD',
                'duration_minutes': interview.duration_seconds // 60 if interview.duration_seconds else 60,
                'ai_interview_type': interview.ai_interview_type,
                'status': interview.status,
                'video_url': interview.video_url,
                'can_join': True,
                'message': 'You can now join your interview'
            }
            
            # Log the access attempt
            ActionLogger.log_user_action(
                user=None,  # No user for public access
                action='candidate_interview_access',
                details={
                    'interview_id': str(interview.id),
                    'candidate_email': interview.candidate.email,
                    'link_token': link_token[:20] + '...',  # Log partial token for security
                    'access_time': timezone.now().isoformat()
                },
                status='SUCCESS'
            )
            
            return Response(response_data)
            
        except Interview.DoesNotExist:
            return Response({
                'error': 'Interview not found',
                'status': 'not_found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in public interview access: {e}")
            return Response({
                'error': 'Invalid interview link',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, link_token):
        """Join the interview (start the interview session)"""
        try:
            # Decode the link token
            import base64
            decoded_token = base64.urlsafe_b64decode(link_token.encode('utf-8')).decode('utf-8')
            interview_id, signature = decoded_token.split(':', 1)
            
            # Get the interview
            interview = Interview.objects.get(id=interview_id)
            
            # Validate the link
            is_valid, message = interview.validate_interview_link(link_token)
            
            if not is_valid:
                return Response({
                    'error': message,
                    'status': 'invalid_link'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if interview can be started
            now = timezone.now()
            if interview.started_at and now < interview.started_at:
                return Response({
                    'error': f'Interview starts at {interview.started_at.strftime("%I:%M %p")}. Please wait.',
                    'status': 'not_started'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if interview.status == 'completed':
                return Response({
                    'error': 'This interview has already been completed',
                    'status': 'completed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Start the interview
            if not interview.started_at:
                interview.started_at = now
                interview.save()
            
            # Log the interview start
            ActionLogger.log_user_action(
                user=None,  # No user for public access
                action='candidate_interview_started',
                details={
                    'interview_id': str(interview.id),
                    'candidate_email': interview.candidate.email,
                    'start_time': now.isoformat()
                },
                status='SUCCESS'
            )
            
            return Response({
                'interview_id': str(interview.id),
                'candidate_name': interview.candidate.full_name,
                'ai_interview_type': interview.ai_interview_type,
                'started_at': interview.started_at.isoformat(),
                'status': 'started',
                'message': 'Interview started successfully',
                'ai_configuration': interview.schedule.slot.ai_configuration if interview.is_scheduled else {}
            })
            
        except Interview.DoesNotExist:
            return Response({
                'error': 'Interview not found',
                'status': 'not_found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error starting interview: {e}")
            return Response({
                'error': 'Failed to start interview',
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InterviewViewSet(DataIsolationMixin, viewsets.ModelViewSet):
    """
    /api/interviews/  → list, create
    /api/interviews/<pk>/  → retrieve, update, delete
    """
    queryset           = Interview.objects.select_related("candidate", "job")
    serializer_class   = InterviewSerializer
    permission_classes = [InterviewHierarchyPermission]

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
            ActionLogger.log_user_action(
                user=request.user,
                action='interview_create',
                details={'interview_id': response.data.get('id')},
                status='SUCCESS'
            )
            
            # Send notification to candidate when interview is created (only if interview is scheduled)
            try:
                interview_id = response.data.get('id')
                if interview_id:
                    from .models import Interview
                    interview = Interview.objects.get(id=interview_id)
                    # Only send notification if interview has a status that indicates it's scheduled
                    if interview.status in ['scheduled', 'confirmed']:
                        NotificationService.send_candidate_interview_scheduled_notification(interview)
            except Exception as e:
                # Log notification failure but don't fail the request
                ActionLogger.log_user_action(
                    user=request.user,
                    action='interview_notification_failed',
                    details={'interview_id': response.data.get('id'), 'error': str(e)},
                    status='FAILED'
                )
            
            return response
        except Exception as e:
            ActionLogger.log_user_action(
                user=request.user,
                action='interview_create',
                details={'error': str(e)},
                status='FAILED'
            )
            raise

    def update(self, request, *args, **kwargs):
        """Log interview update"""
        response = super().update(request, *args, **kwargs)
        ActionLogger.log_user_action(
            user=request.user,
            action='interview_update',
            details={'interview_id': kwargs.get('pk')},
            status='SUCCESS'
        )
        return response

    def partial_update(self, request, *args, **kwargs):
        """Log interview partial update"""
        response = super().partial_update(request, *args, **kwargs)
        ActionLogger.log_user_action(
            user=request.user,
            action='interview_partial_update',
            details={'interview_id': kwargs.get('pk')},
            status='SUCCESS'
        )
        return response

    def destroy(self, request, *args, **kwargs):
        """Log interview deletion"""
        ActionLogger.log_user_action(
            user=request.user,
            action='interview_delete',
            details={'interview_id': kwargs.get('pk')},
            status='SUCCESS'
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
        serializer = InterviewFeedbackSerializer(interview, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            ActionLogger.log_user_action(
                user=request.user,
                action='interview_feedback_update',
                details={'interview_id': pk},
                status='SUCCESS'
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
            action='interview_summary',
            details=summary,
            status='SUCCESS'
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
        if self.request.method in ['PUT', 'PATCH']:
            return InterviewSerializer
        return InterviewSerializer


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
            base_queryset = InterviewSlot.objects.filter(company=self.request.user.company)
        elif user_role in ["hiring_agency", "recruiter"]:
            base_queryset = InterviewSlot.objects.filter(company=self.request.user.company)
        else:
            base_queryset = InterviewSlot.objects.none()
        
        return base_queryset.order_by('-created_at')

    def perform_create(self, serializer):
        user_role = getattr(self.request.user, "role", "").lower()
        
        if user_role == "admin" or self.request.user.is_superuser:
            # Admin can create slots for any company - let the serializer handle it
            serializer.save()
        elif user_role == "company":
            # Company users can only create slots for their company
            if hasattr(self.request.user, 'company') and self.request.user.company:
                serializer.save(company=self.request.user.company)
            else:
                raise PermissionDenied("Company user must be associated with a company")
        else:
            raise PermissionDenied("You don't have permission to create interview slots")

    @action(detail=False, methods=['post'])
    def search_available(self, request):
        """
        Search for available slots based on criteria
        """
        serializer = SlotSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        queryset = self.get_queryset().filter(
            status='available',
            start_time__date__gte=data['start_date'],
            start_time__date__lte=data['end_date']
        )
        
        if data.get('company_id'):
            queryset = queryset.filter(company_id=data['company_id'])
        
        if data.get('ai_interview_type'):
            queryset = queryset.filter(ai_interview_type=data['ai_interview_type'])
        
        if data.get('job_id'):
            queryset = queryset.filter(job_id=data['job_id'])
        
        if data.get('start_time') and data.get('end_time'):
            queryset = queryset.filter(
                start_time__time__gte=data['start_time'],
                end_time__time__lte=data['end_time']
            )
        
        if data.get('duration_minutes'):
            queryset = queryset.filter(duration_minutes__gte=data['duration_minutes'])
        
        # Filter by availability
        available_slots = [slot for slot in queryset if slot.is_available()]
        
        page = self.paginate_queryset(available_slots)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(available_slots, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
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
            company = Company.objects.get(id=data['company_id'])
        except Company.DoesNotExist:
            return Response({"error": "Company not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create slots for each day in the pattern
        created_slots = []
        skipped_slots = []
        current_date = data['start_date']
        
        while current_date <= data['end_date']:
            if current_date.weekday() + 1 in data['days_of_week']:  # weekday() returns 0-6, we need 1-7
                # Create slot for this day
                slot_start = datetime.combine(current_date, data['start_time'])
                slot_end = datetime.combine(current_date, data['end_time'])
                
                # Make timezone-aware
                from django.utils import timezone
                slot_start = timezone.make_aware(slot_start)
                slot_end = timezone.make_aware(slot_end)
                
                # Check for conflicts - only check for exact time overlaps
                conflicting_slots = InterviewSlot.objects.filter(
                    company=company,
                    start_time__lt=slot_end,
                    end_time__gt=slot_start,
                    status__in=['available', 'booked']
                )
                
                if not conflicting_slots.exists():
                    try:
                        slot = InterviewSlot.objects.create(
                            slot_type='recurring',
                            start_time=slot_start,
                            end_time=slot_end,
                            duration_minutes=data['slot_duration'],
                            company=company,
                            job_id=data.get('job_id'),
                            ai_interview_type=data['ai_interview_type'],
                            ai_configuration=data.get('ai_configuration', {}),
                            is_recurring=True,
                            recurring_pattern={
                                'days_of_week': data['days_of_week'],
                                'start_time': data['start_time'].isoformat(),
                                'end_time': data['end_time'].isoformat(),
                                'slot_duration': data['slot_duration'],
                                'break_duration': data['break_duration']
                            },
                            notes=data.get('notes', ''),
                            max_candidates=data['max_candidates_per_slot']
                        )
                        created_slots.append(slot)
                    except Exception as e:
                        skipped_slots.append({
                            'date': current_date.isoformat(),
                            'reason': str(e)
                        })
                else:
                    skipped_slots.append({
                        'date': current_date.isoformat(),
                        'reason': 'Time conflict with existing slot'
                    })
            
            current_date += timedelta(days=1)
        
        serializer = self.get_serializer(created_slots, many=True)
        return Response({
            'message': f'Created {len(created_slots)} recurring slots',
            'created_slots': len(created_slots),
            'slots': serializer.data,
            'skipped_slots': skipped_slots
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def book_slot(self, request, pk=None):
        """
        Book a slot for an interview
        """
        slot = self.get_object()
        
        if slot.status != 'available':
            return Response({"error": "Slot is not available for booking"}, status=status.HTTP_400_BAD_REQUEST)
        
        interview_id = request.data.get('interview_id')
        if not interview_id:
            return Response({"error": "interview_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            interview = Interview.objects.get(id=interview_id)
        except Interview.DoesNotExist:
            return Response({"error": "Interview not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Create schedule
        schedule = InterviewSchedule.objects.create(
            interview=interview,
            slot=slot,
            booking_notes=request.data.get('booking_notes', ''),
            status='pending'
        )
        
        # Book the slot
        slot.book_slot()
        
        # Send notification to candidate when slot is booked
        try:
            from notifications.services import NotificationService
            NotificationService.send_candidate_interview_scheduled_notification(interview)
        except Exception as e:
            # Log notification failure but don't fail the request
            ActionLogger.log_user_action(
                user=request.user,
                action='slot_booking_notification_failed',
                details={'slot_id': slot.id, 'interview_id': interview.id, 'error': str(e)},
                status='FAILED'
            )
        
        serializer = InterviewScheduleSerializer(schedule)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def release_slot(self, request, pk=None):
        """
        Release a booking from a slot
        """
        slot = self.get_object()
        
        # First, cancel any active schedules for this slot
        active_schedules = slot.schedules.filter(status__in=['pending', 'confirmed'])
        for schedule in active_schedules:
            schedule.cancel_schedule(reason="Slot released by admin", cancelled_by=request.user)
        
        # Ensure the slot is available
        slot.refresh_from_db()
        if slot.current_bookings > 0:
            slot.release_slot()
        
        # Force the slot to be available
        slot.status = slot.Status.AVAILABLE
        slot.current_bookings = 0
        slot.save()
        
        return Response({
            'message': 'Slot released successfully',
            'slot_available': slot.is_available(),
            'current_bookings': slot.current_bookings,
            'max_candidates': slot.max_candidates
        })


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
            base_queryset = InterviewSchedule.objects.filter(slot__company=self.request.user.company)
        elif user_role in ["hiring_agency", "recruiter"]:
            base_queryset = InterviewSchedule.objects.filter(slot__company=self.request.user.company)
        else:
            base_queryset = InterviewSchedule.objects.none()
        
        return base_queryset.order_by('-booked_at')

    @action(detail=False, methods=['post'])
    def book_interview(self, request):
        """
        Book an interview to a slot
        """
        serializer = SlotBookingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        interview = data['interview']
        slot = data['slot']
        
        # Create the schedule
        schedule = InterviewSchedule.objects.create(
            interview=interview,
            slot=slot,
            booking_notes=data.get('booking_notes', ''),
            status='pending'
        )
        
        # Book the slot
        slot.book_slot()
        
        # Send notification to candidate when interview is scheduled
        try:
            from notifications.services import NotificationService
            NotificationService.send_candidate_interview_scheduled_notification(interview)
        except Exception as e:
            # Log notification failure but don't fail the request
            ActionLogger.log_user_action(
                user=request.user,
                action='interview_booking_notification_failed',
                details={'interview_id': interview.id, 'schedule_id': schedule.id, 'error': str(e)},
                status='FAILED'
            )
        
        serializer = self.get_serializer(schedule)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def confirm_schedule(self, request, pk=None):
        """
        Confirm an interview schedule
        """
        schedule = self.get_object()
        
        if schedule.status == 'cancelled':
            return Response({"error": "Cannot confirm a cancelled schedule"}, status=status.HTTP_400_BAD_REQUEST)
        
        schedule.confirm_schedule()
        
        # Send notification to candidate when schedule is confirmed
        try:
            from notifications.services import NotificationService
            NotificationService.send_candidate_interview_scheduled_notification(schedule.interview)
        except Exception as e:
            # Log notification failure but don't fail the request
            ActionLogger.log_user_action(
                user=request.user,
                action='schedule_confirmation_notification_failed',
                details={'schedule_id': schedule.id, 'error': str(e)},
                status='FAILED'
            )
        
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel_schedule(self, request, pk=None):
        """
        Cancel an interview schedule
        """
        schedule = self.get_object()
        reason = request.data.get('reason', '')
        
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
            base_queryset = AIInterviewConfiguration.objects.filter(company=self.request.user.company)
        elif user_role in ["hiring_agency", "recruiter"]:
            base_queryset = AIInterviewConfiguration.objects.filter(company=self.request.user.company)
        else:
            base_queryset = AIInterviewConfiguration.objects.none()
        
        return base_queryset.order_by('-created_at')

    def perform_create(self, serializer):
        user_role = getattr(self.request.user, "role", "").lower()
        
        if user_role == "admin" or self.request.user.is_superuser:
            # Admin can create configurations for any company
            pass
        elif user_role == "company":
            # Company users can only create configurations for their company
            serializer.save(company=self.request.user.company)
        else:
            raise PermissionDenied("You don't have permission to create AI interview configurations")


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
        
        return base_queryset.order_by('-detected_at')

    @action(detail=True, methods=['post'])
    def resolve_conflict(self, request, pk=None):
        """
        Resolve an interview conflict
        """
        conflict = self.get_object()
        resolution = request.data.get('resolution', 'resolved')
        notes = request.data.get('resolution_notes', '')
        
        if resolution not in ['rescheduled', 'cancelled', 'resolved']:
            return Response({"error": "Invalid resolution"}, status=status.HTTP_400_BAD_REQUEST)
        
        conflict.resolution = resolution
        conflict.resolution_notes = notes
        conflict.resolved_at = timezone.now()
        conflict.resolved_by = request.user
        conflict.save()
        
        serializer = self.get_serializer(conflict)
        return Response(serializer.data)


class SlotAvailabilityView(generics.ListAPIView):
    """
    Get available slots for a specific date range
    """
    serializer_class = InterviewSlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        company_id = self.request.query_params.get('company_id')
        ai_interview_type = self.request.query_params.get('ai_interview_type')
        
        queryset = InterviewSlot.objects.filter(status='available')
        
        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(start_time__date__lte=end_date)
        
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        
        if ai_interview_type:
            queryset = queryset.filter(ai_interview_type=ai_interview_type)
        
        # Apply data isolation
        user_role = getattr(self.request.user, "role", "").lower()
        
        if user_role == "admin" or self.request.user.is_superuser:
            pass  # Admin sees all
        elif user_role == "company":
            queryset = queryset.filter(company=self.request.user.company)
        elif user_role in ["hiring_agency", "recruiter"]:
            queryset = queryset.filter(company=self.request.user.company)
        else:
            queryset = InterviewSlot.objects.none()
        
        # Filter by availability
        available_slots = [slot for slot in queryset if slot.is_available()]
        return available_slots

    def list(self, request, *args, **kwargs):
        """
        Override list method to return the expected format
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'available_slots': serializer.data,
            'total_available': len(serializer.data)
        })


class InterviewCalendarView(generics.ListAPIView):
    """
    Get interview calendar view with slots and schedules
    """
    serializer_class = InterviewScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        queryset = InterviewSchedule.objects.select_related(
            'interview__candidate', 'slot__company'
        )
        
        if start_date:
            queryset = queryset.filter(slot__start_time__date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(slot__start_time__date__lte=end_date)
        
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
        
        return queryset.order_by('slot__start_time')

    def list(self, request, *args, **kwargs):
        """
        Override list method to return calendar format
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Get slot statistics
        from .models import InterviewSlot
        total_slots = InterviewSlot.objects.count()
        available_slots = InterviewSlot.objects.filter(status='available').count()
        booked_slots = InterviewSlot.objects.filter(status='booked').count()
        
        return Response({
            'calendar_data': serializer.data,
            'total_slots': total_slots,
            'available_slots': available_slots,
            'booked_slots': booked_slots
        })
