# interviews/views.py
import logging
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.http import HttpResponse # Added for HttpResponse

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
        """Get interview details and serve interactive interview interface"""
        try:
            # Debug logging
            print(f"DEBUG: PublicInterviewAccessView.get() called with link_token: {link_token}")
            
            # Try to decode the link token - handle both long and short formats
            import base64
            try:
                # First try the long format (interview_id:signature)
                decoded_token = base64.urlsafe_b64decode(link_token.encode('utf-8')).decode('utf-8')
                interview_id, signature = decoded_token.split(':', 1)
                print(f"DEBUG: Using long format - interview_id: {interview_id}")
            except:
                # If that fails, try the short format (just interview_id)
                try:
                    # Add padding if needed
                    padded_token = link_token + '=' * (4 - len(link_token) % 4) if len(link_token) % 4 else link_token
                    interview_id = base64.urlsafe_b64decode(padded_token.encode('utf-8')).decode('utf-8')
                    print(f"DEBUG: Using short format - interview_id: {interview_id}")
                except Exception as e:
                    print(f"DEBUG: Failed to decode token: {e}")
                    return Response({
                        'error': 'Invalid interview link format',
                        'status': 'invalid_format'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
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
            
            # Check if user wants JSON response (for API calls)
            if request.headers.get('Accept') == 'application/json':
                # Return JSON response for API calls
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
                return Response(response_data)
            
                        # Redirect to the actual AI interview portal with video/audio capabilities
            from django.shortcuts import redirect
            from ai_platform.interview_app.models import InterviewSession
            
            # Create or get the AI interview session
            ai_session, created = InterviewSession.objects.get_or_create(
                session_key=link_token,
                defaults={
                    'candidate_name': interview.candidate.full_name,
                    'candidate_email': interview.candidate.email,
                    'job_description': interview.job.tech_stack_details if interview.job else 'Technical Role',
                    'resume_text': getattr(interview.candidate, 'resume_text', '') or 'Experienced professional seeking new opportunities.',
                    'language_code': 'en',
                    'accent_tld': 'com',
                    'scheduled_at': interview.started_at,
                    'status': 'SCHEDULED'
                }
            )
            
            # Redirect to the actual AI interview portal
            ai_interview_url = f"{request.build_absolute_uri('/')}interview_app/?session_key={link_token}"
            return redirect(ai_interview_url)
            
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
            
            return HttpResponse(html_content, content_type='text/html')
            
        except Interview.DoesNotExist:
            return Response({
                'error': 'Interview not found',
                'status': 'not_found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in public interview access: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({
                'error': f'Invalid interview link: {str(e)}',
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
            
            # Create AI interview session if not exists
            from ai_interview.services import ai_interview_service
            from ai_interview.models import AIInterviewSession
            
            ai_session, created = AIInterviewSession.objects.get_or_create(
                interview=interview,
                defaults={
                    'status': 'ACTIVE',
                    'model_name': 'gemini-1.5-flash-latest',
                    'model_version': '1.0',
                    'ai_configuration': {
                        'language_code': 'en',
                        'accent_tld': 'com',
                        'candidate_name': interview.candidate.full_name,
                        'candidate_email': interview.candidate.email,
                        'job_description': interview.job.description if interview.job else '',
                        'resume_text': getattr(interview.candidate, 'resume_text', '') or '',
                    },
                    'session_started_at': timezone.now()
                }
            )
            
            return Response({
                'interview_id': str(interview.id),
                'candidate_name': interview.candidate.full_name,
                'ai_interview_type': interview.ai_interview_type,
                'started_at': interview.started_at.isoformat(),
                'status': 'started',
                'message': 'Interview started successfully',
                'ai_configuration': interview.schedule.slot.ai_configuration if interview.is_scheduled else {},
                'ai_session_id': str(ai_session.id),
                'ai_interview_ready': True
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
    
    Query Parameters:
    - candidate_id: Filter interviews by candidate ID
    - status: Filter by interview status
    - job: Filter by job ID
    - candidate: Filter by candidate ID (alternative)
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
        candidate_id = self.request.query_params.get('candidate_id')
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
                    action='interview_link_generated',
                    details={
                        'interview_id': str(interview.id),
                        'candidate_email': interview.candidate.email,
                        'link_expires_at': interview.link_expires_at.isoformat() if interview.link_expires_at else None
                    },
            status='SUCCESS'
        )
        
                return Response({
                    'link_token': link_token,
                    'interview_url': f"{request.build_absolute_uri('/')}api/interviews/public/{link_token}/",
                    'expires_at': interview.link_expires_at.isoformat() if interview.link_expires_at else None,
                    'message': 'Interview link generated successfully'
                })
            else:
                return Response({
                    'error': 'Could not generate interview link. Interview must have a start time.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            ActionLogger.log_user_action(
                user=request.user,
                action='interview_link_generation_failed',
                details={
                    'interview_id': str(interview.id),
                    'error': str(e)
                },
                status='FAILED'
            )
            
            return Response({
                'error': f'Failed to generate interview link: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        date = self.request.query_params.get('date')
        company = self.request.query_params.get('company')
        company_id = self.request.query_params.get('company_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        ai_interview_type = self.request.query_params.get('ai_interview_type')
        
        # Start with available slots
        queryset = InterviewSlot.objects.filter(status='available')
        
        # Date filtering - support both single date and date range
        if date:
            # Single date filter
            queryset = queryset.filter(start_time__date=date)
        else:
            # Date range filtering
            if start_date:
                queryset = queryset.filter(start_time__date__gte=start_date)
            
            if end_date:
                queryset = queryset.filter(start_time__date__lte=end_date)
        
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
                "id": slot_data['id'],
                "start_time": slot_data['start_time'],
                "end_time": slot_data['end_time'],
                "ai_interview_type": slot_data['ai_interview_type'],
                "company": slot_data['company'],
                "status": slot_data['status'],
                "current_bookings": slot_data['current_bookings'],
                "max_candidates": slot_data['max_candidates']
            }
            available_slots.append(slot_info)
        
        return Response({
            'available_slots': available_slots,
            'total_available': len(available_slots)
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
