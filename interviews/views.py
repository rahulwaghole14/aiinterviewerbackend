# interviews/views.py
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
    InterviewerAvailability, InterviewConflict
)
from .serializers import (
    InterviewSerializer, InterviewFeedbackSerializer,
    InterviewSlotSerializer, InterviewScheduleSerializer,
    InterviewerAvailabilitySerializer, InterviewConflictSerializer,
    SlotBookingSerializer, SlotSearchSerializer, RecurringSlotSerializer
)
from utils.hierarchy_permissions import DataIsolationMixin, InterviewHierarchyPermission
from utils.logger import log_interview_schedule, log_permission_denied, ActionLogger
from notifications.services import NotificationService


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
                
                # Send notification for interview scheduling
                try:
                    from interviews.models import Interview
                    interview = Interview.objects.get(id=interview_data.get('id'))
                    NotificationService.send_interview_scheduled_notification(interview)
                except Exception as e:
                    # Log notification failure but don't fail the request
                    ActionLogger.log_user_action(
                        user=request.user,
                        action='notification_failed',
                        details={'error': str(e), 'interview_id': interview_data.get('id')},
                        status='FAILED'
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


# ──────────────────────────────────────────────────────────
# Interview Slot Management Views
# ──────────────────────────────────────────────────────────

class InterviewListCreateView(DataIsolationMixin, generics.ListCreateAPIView):
    """
    List and create interviews
    """
    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer
    permission_classes = [InterviewHierarchyPermission]

    def get_queryset(self):
        """Apply data isolation based on user role"""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == "ADMIN":
            return queryset
        elif user.role == "COMPANY":
            return queryset.filter(candidate__recruiter__company_name=user.company_name)
        elif user.role in ["HIRING_AGENCY", "RECRUITER"]:
            return queryset.filter(candidate__recruiter=user)
        
        return Interview.objects.none()


class InterviewDetailView(DataIsolationMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an interview
    """
    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer
    permission_classes = [InterviewHierarchyPermission]

    def get_serializer_class(self):
        """Use different serializer for different operations"""
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
    ViewSet for managing interview slots
    """
    serializer_class = InterviewSlotSerializer
    permission_classes = [InterviewHierarchyPermission]

    def get_queryset(self):
        """Apply data isolation and filtering"""
        user = self.request.user
        queryset = InterviewSlot.objects.all()
        
        # Apply role-based filtering
        if user.role == "ADMIN":
            pass  # Admin sees all slots
        elif user.role == "COMPANY":
            queryset = queryset.filter(company__name=user.company_name)
        elif user.role in ["HIRING_AGENCY", "RECRUITER"]:
            queryset = queryset.filter(company__name=user.company_name)
        
        # Apply additional filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        interviewer_filter = self.request.query_params.get('interviewer_id')
        if interviewer_filter:
            queryset = queryset.filter(interviewer_id=interviewer_filter)
        
        company_filter = self.request.query_params.get('company_id')
        if company_filter:
            queryset = queryset.filter(company_id=company_filter)
        
        return queryset.order_by('start_time')

    def perform_create(self, serializer):
        """Set company automatically based on user"""
        user = self.request.user
        if user.role == "COMPANY":
            serializer.save(company=user.company)
        else:
            serializer.save()

    @action(detail=False, methods=['post'])
    def search_available(self, request):
        """
        Search for available slots based on criteria
        """
        serializer = SlotSearchSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Build query for available slots
            queryset = InterviewSlot.objects.filter(
                status='available',
                start_time__date__gte=data['start_date'],
                start_time__date__lte=data['end_date'],
                current_bookings__lt=models.F('max_candidates')
            )
            
            # Apply filters
            if data.get('company_id'):
                queryset = queryset.filter(company_id=data['company_id'])
            
            if data.get('interviewer_id'):
                queryset = queryset.filter(interviewer_id=data['interviewer_id'])
            
            if data.get('job_id'):
                queryset = queryset.filter(job_id=data['job_id'])
            
            if data.get('start_time') and data.get('end_time'):
                queryset = queryset.filter(
                    start_time__time__gte=data['start_time'],
                    end_time__time__lte=data['end_time']
                )
            
            # Apply data isolation
            user = request.user
            if user.role == "COMPANY":
                queryset = queryset.filter(company__name=user.company_name)
            elif user.role in ["HIRING_AGENCY", "RECRUITER"]:
                queryset = queryset.filter(company__name=user.company_name)
            
            slots = queryset.order_by('start_time')
            slot_serializer = InterviewSlotSerializer(slots, many=True)
            
            return Response({
                'slots': slot_serializer.data,
                'total_count': slots.count()
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def create_recurring(self, request):
        """
        Create recurring interview slots
        """
        serializer = RecurringSlotSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Get interviewer and company
            from authapp.models import CustomUser
            from companies.models import Company
            
            try:
                interviewer = CustomUser.objects.get(id=data['interviewer_id'])
                company = Company.objects.get(id=data['company_id'])
            except (CustomUser.DoesNotExist, Company.DoesNotExist):
                return Response(
                    {'error': 'Invalid interviewer or company ID'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            created_slots = []
            current_date = data['start_date']
            
            while current_date <= data['end_date']:
                # Check if this day of week is in the pattern
                if current_date.isoweekday() in data['days_of_week']:
                    # Create slots for this day
                    current_time = datetime.combine(current_date, data['start_time'])
                    end_time = datetime.combine(current_date, data['end_time'])
                    
                    while current_time + timedelta(minutes=data['slot_duration']) <= end_time:
                        slot_end_time = current_time + timedelta(minutes=data['slot_duration'])
                        
                        # Check for conflicts
                        conflict = InterviewSlot.objects.filter(
                            interviewer=interviewer,
                            start_time__lt=slot_end_time,
                            end_time__gt=current_time,
                            status__in=['available', 'booked']
                        ).exists()
                        
                        if not conflict:
                            slot = InterviewSlot.objects.create(
                                slot_type='recurring',
                                start_time=current_time,
                                end_time=slot_end_time,
                                duration_minutes=data['slot_duration'],
                                interviewer=interviewer,
                                company=company,
                                job_id=data.get('job_id'),
                                is_recurring=True,
                                recurring_pattern={
                                    'days_of_week': data['days_of_week'],
                                    'slot_duration': data['slot_duration'],
                                    'break_duration': data['break_duration']
                                },
                                notes=data.get('notes', ''),
                                max_candidates=data['max_candidates_per_slot']
                            )
                            created_slots.append(slot)
                        
                        # Move to next slot with break
                        current_time = slot_end_time + timedelta(minutes=data['break_duration'])
                
                current_date += timedelta(days=1)
            
            slot_serializer = InterviewSlotSerializer(created_slots, many=True)
            return Response({
                'message': f'Created {len(created_slots)} recurring slots',
                'slots': slot_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def book_slot(self, request, pk=None):
        """
        Book a specific slot
        """
        slot = self.get_object()
        
        if not slot.is_available():
            return Response(
                {'error': 'Slot is not available for booking'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if slot.book_slot():
            slot_serializer = InterviewSlotSerializer(slot)
            return Response({
                'message': 'Slot booked successfully',
                'slot': slot_serializer.data
            })
        
        return Response(
            {'error': 'Failed to book slot'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def release_slot(self, request, pk=None):
        """
        Release a booked slot
        """
        slot = self.get_object()
        
        if slot.release_slot():
            slot_serializer = InterviewSlotSerializer(slot)
            return Response({
                'message': 'Slot released successfully',
                'slot': slot_serializer.data
            })
        
        return Response(
            {'error': 'Failed to release slot'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class InterviewScheduleViewSet(DataIsolationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing interview schedules
    """
    serializer_class = InterviewScheduleSerializer
    permission_classes = [InterviewHierarchyPermission]

    def get_queryset(self):
        """Apply data isolation"""
        user = self.request.user
        queryset = InterviewSchedule.objects.all()
        
        if user.role == "ADMIN":
            return queryset
        elif user.role == "COMPANY":
            return queryset.filter(slot__company__name=user.company_name)
        elif user.role in ["HIRING_AGENCY", "RECRUITER"]:
            return queryset.filter(slot__company__name=user.company_name)
        
        return InterviewSchedule.objects.none()

    @action(detail=False, methods=['post'])
    def book_interview(self, request):
        """
        Book an interview to a slot
        """
        serializer = SlotBookingSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Create the schedule
            schedule = InterviewSchedule.objects.create(
                interview=data['interview'],
                slot=data['slot'],
                booking_notes=data.get('booking_notes', '')
            )
            
            # Book the slot
            data['slot'].book_slot()
            
            schedule_serializer = InterviewScheduleSerializer(schedule)
            return Response({
                'message': 'Interview scheduled successfully',
                'schedule': schedule_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def confirm_schedule(self, request, pk=None):
        """
        Confirm an interview schedule
        """
        schedule = self.get_object()
        schedule.confirm_schedule()
        
        schedule_serializer = InterviewScheduleSerializer(schedule)
        return Response({
            'message': 'Schedule confirmed successfully',
            'schedule': schedule_serializer.data
        })

    @action(detail=True, methods=['post'])
    def cancel_schedule(self, request, pk=None):
        """
        Cancel an interview schedule
        """
        schedule = self.get_object()
        reason = request.data.get('reason', '')
        cancelled_by = request.user
        
        schedule.cancel_schedule(reason=reason, cancelled_by=cancelled_by)
        
        schedule_serializer = InterviewScheduleSerializer(schedule)
        return Response({
            'message': 'Schedule cancelled successfully',
            'schedule': schedule_serializer.data
        })


class InterviewerAvailabilityViewSet(DataIsolationMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing interviewer availability
    """
    serializer_class = InterviewerAvailabilitySerializer
    permission_classes = [InterviewHierarchyPermission]

    def get_queryset(self):
        """Apply data isolation"""
        user = self.request.user
        queryset = InterviewerAvailability.objects.all()
        
        if user.role == "ADMIN":
            return queryset
        elif user.role == "COMPANY":
            return queryset.filter(company__name=user.company_name)
        elif user.role in ["HIRING_AGENCY", "RECRUITER"]:
            return queryset.filter(company__name=user.company_name)
        
        return InterviewerAvailability.objects.none()

    def perform_create(self, serializer):
        """Set company automatically based on user"""
        user = self.request.user
        if user.role == "COMPANY":
            serializer.save(company=user.company)
        else:
            serializer.save()


class InterviewConflictViewSet(DataIsolationMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing interview conflicts (read-only)
    """
    serializer_class = InterviewConflictSerializer
    permission_classes = [InterviewHierarchyPermission]

    def get_queryset(self):
        """Apply data isolation"""
        user = self.request.user
        queryset = InterviewConflict.objects.all()
        
        if user.role == "ADMIN":
            return queryset
        elif user.role == "COMPANY":
            return queryset.filter(
                primary_interview__candidate__recruiter__company_name=user.company_name
            )
        elif user.role in ["HIRING_AGENCY", "RECRUITER"]:
            return queryset.filter(
                primary_interview__candidate__recruiter=user
            )
        
        return InterviewConflict.objects.none()

    @action(detail=True, methods=['post'])
    def resolve_conflict(self, request, pk=None):
        """
        Resolve an interview conflict
        """
        conflict = self.get_object()
        resolution = request.data.get('resolution', 'resolved')
        notes = request.data.get('notes', '')
        
        conflict.resolution = resolution
        conflict.resolution_notes = notes
        conflict.resolved_at = timezone.now()
        conflict.resolved_by = request.user
        conflict.save()
        
        conflict_serializer = InterviewConflictSerializer(conflict)
        return Response({
            'message': 'Conflict resolved successfully',
            'conflict': conflict_serializer.data
        })


# ──────────────────────────────────────────────────────────
# Utility Views for Slot Management
# ──────────────────────────────────────────────────────────

class SlotAvailabilityView(generics.ListAPIView):
    """
    Get available slots for a specific date range
    """
    serializer_class = InterviewSlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get available slots based on query parameters"""
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        company_id = self.request.query_params.get('company_id')
        interviewer_id = self.request.query_params.get('interviewer_id')
        
        queryset = InterviewSlot.objects.filter(
            status='available',
            current_bookings__lt=models.F('max_candidates')
        )
        
        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_time__date__lte=end_date)
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        if interviewer_id:
            queryset = queryset.filter(interviewer_id=interviewer_id)
        
        # Apply data isolation
        user = self.request.user
        if user.role == "COMPANY":
            queryset = queryset.filter(company__name=user.company_name)
        elif user.role in ["HIRING_AGENCY", "RECRUITER"]:
            queryset = queryset.filter(company__name=user.company_name)
        
        return queryset.order_by('start_time')


class InterviewCalendarView(generics.ListAPIView):
    """
    Get interview calendar view with slots and schedules
    """
    serializer_class = InterviewScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get schedules for calendar view"""
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        queryset = InterviewSchedule.objects.filter(
            status__in=['pending', 'confirmed']
        )
        
        if start_date:
            queryset = queryset.filter(slot__start_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(slot__start_time__date__lte=end_date)
        
        # Apply data isolation
        user = self.request.user
        if user.role == "COMPANY":
            queryset = queryset.filter(slot__company__name=user.company_name)
        elif user.role in ["HIRING_AGENCY", "RECRUITER"]:
            queryset = queryset.filter(slot__company__name=user.company_name)
        
        return queryset.order_by('slot__start_time')
