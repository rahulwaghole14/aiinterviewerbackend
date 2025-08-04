# candidates/views.py
from django.db.models import Count
from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models      import Candidate, CandidateDraft
from .serializers import (
    CandidateCreateSerializer,   # serializer for POST / PUT / PATCH
    CandidateListSerializer,     # serializer for GET (list / detail)
    # New step-by-step serializers
    DomainRoleSelectionSerializer,
    DataExtractionSerializer,
    CandidateVerificationSerializer,
    CandidateSubmissionSerializer
)
from utils.hierarchy_permissions import ResumeHierarchyPermission, DataIsolationMixin
from utils.logger import ActionLogger
from resumes.models import Resume, extract_resume_fields
from utils.name_parser import parse_candidate_name

# ────────────────────────────────────────────────────────────────
# Step-by-Step Candidate Creation Views
# ────────────────────────────────────────────────────────────────

class DomainRoleSelectionView(APIView):
    """
    Step 1: Select domain and role
    POST /api/candidates/select-domain/
    """
    permission_classes = [ResumeHierarchyPermission]
    
    def post(self, request):
        """Create a new draft with domain and role selection"""
        serializer = DomainRoleSelectionSerializer(data=request.data)
        if serializer.is_valid():
            # Create draft with domain and role
            draft = CandidateDraft.objects.create(
                user=request.user,
                domain=serializer.validated_data['domain'],
                role=serializer.validated_data['role'],
                status=CandidateDraft.Status.DRAFT
            )
            
            # Log domain/role selection
            ActionLogger.log_user_action(
                user=request.user,
                action='domain_role_selection',
                details={
                    'draft_id': draft.id,
                    'domain': draft.domain,
                    'role': draft.role
                },
                status='SUCCESS'
            )
            
            return Response({
                'message': 'Domain and role selected successfully',
                'draft_id': draft.id,
                'domain': draft.domain,
                'role': draft.role,
                'next_step': 'upload_resume'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DataExtractionView(APIView):
    """
    Step 2: Upload resume and extract data
    POST /api/candidates/extract-data/
    """
    permission_classes = [ResumeHierarchyPermission]
    
    def post(self, request):
        """Upload resume and extract data"""
        serializer = DataExtractionSerializer(data=request.data)
        if serializer.is_valid():
            domain = serializer.validated_data['domain']
            role = serializer.validated_data['role']
            resume_file = serializer.validated_data['resume_file']
            
            # Find or create draft
            try:
                draft = CandidateDraft.objects.get(
                    user=request.user,
                    domain=domain,
                    role=role,
                    status=CandidateDraft.Status.DRAFT
                )
            except CandidateDraft.DoesNotExist:
                return Response({
                    'error': 'No draft found. Please select domain and role first.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save resume file to draft
            draft.resume_file = resume_file
            draft.save()
            
            # Extract data from resume
            try:
                # Create temporary resume object for text extraction
                temp_resume = Resume.objects.create(user=request.user, file=resume_file)
                
                # Extract data
                extracted_data = {}
                if temp_resume.parsed_text:
                    extracted_data = extract_resume_fields(temp_resume.parsed_text)
                    
                    # Clean name if extracted
                    if extracted_data.get('name'):
                        extracted_data['name'] = parse_candidate_name(extracted_data['name'])
                
                # Update draft with extracted data
                draft.extracted_data = extracted_data
                draft.verified_data = extracted_data.copy()  # Initialize verified data
                draft.status = CandidateDraft.Status.EXTRACTED
                draft.save()
                
                # Clean up temporary resume
                temp_resume.delete()
                
                # Log data extraction
                ActionLogger.log_user_action(
                    user=request.user,
                    action='resume_data_extraction',
                    details={
                        'draft_id': draft.id,
                        'filename': resume_file.name,
                        'extracted_fields': list(extracted_data.keys())
                    },
                    status='SUCCESS'
                )
                
                return Response({
                    'message': 'Resume uploaded and data extracted successfully',
                    'draft_id': draft.id,
                    'extracted_data': extracted_data,
                    'next_step': 'verify_data'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                # Log extraction error
                ActionLogger.log_user_action(
                    user=request.user,
                    action='resume_data_extraction',
                    details={
                        'draft_id': draft.id,
                        'filename': resume_file.name,
                        'error': str(e)
                    },
                    status='FAILED'
                )
                return Response({
                    'error': f'Failed to extract data from resume: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CandidateVerificationView(APIView):
    """
    Step 3 & 4: Preview and update extracted data
    GET  /api/candidates/verify/{draft_id}/
    PUT  /api/candidates/verify/{draft_id}/
    """
    permission_classes = [ResumeHierarchyPermission]
    
    def get(self, request, draft_id):
        """Get draft data for verification"""
        try:
            draft = CandidateDraft.objects.get(
                id=draft_id,
                user=request.user,
                status__in=[CandidateDraft.Status.EXTRACTED, CandidateDraft.Status.VERIFIED]
            )
            
            serializer = CandidateVerificationSerializer(draft, context={'request': request})
            
            return Response({
                'message': 'Draft data retrieved for verification',
                'draft': serializer.data,
                'next_step': 'submit_candidate'
            }, status=status.HTTP_200_OK)
            
        except CandidateDraft.DoesNotExist:
            return Response({
                'error': 'Draft not found or not accessible'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, draft_id):
        """Update verified data"""
        try:
            draft = CandidateDraft.objects.get(
                id=draft_id,
                user=request.user,
                status__in=[CandidateDraft.Status.EXTRACTED, CandidateDraft.Status.VERIFIED]
            )
            
            serializer = CandidateVerificationSerializer(
                draft, 
                data=request.data, 
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                updated_draft = serializer.save()
                
                return Response({
                    'message': 'Data verified and updated successfully',
                    'draft': CandidateVerificationSerializer(updated_draft, context={'request': request}).data,
                    'next_step': 'submit_candidate'
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except CandidateDraft.DoesNotExist:
            return Response({
                'error': 'Draft not found or not accessible'
            }, status=status.HTTP_404_NOT_FOUND)

class CandidateSubmissionView(APIView):
    """
    Step 5: Final submission
    POST /api/candidates/submit/{draft_id}/
    """
    permission_classes = [ResumeHierarchyPermission]
    
    def post(self, request, draft_id):
        """Submit candidate from draft"""
        try:
            draft = CandidateDraft.objects.get(
                id=draft_id,
                user=request.user,
                status=CandidateDraft.Status.VERIFIED
            )
            
            # Validate submission confirmation
            serializer = CandidateSubmissionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            if not serializer.validated_data.get('confirm_submission'):
                return Response({
                    'error': 'Submission confirmation required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create final resume object
            resume = Resume.objects.create(
                user=request.user,
                file=draft.resume_file
            )
            
            # Create candidate from verified data
            verified_data = draft.verified_data
            candidate = Candidate.objects.create(
                recruiter=request.user,
                resume=resume,
                domain=draft.domain,
                full_name=verified_data.get('name', ''),
                email=verified_data.get('email', ''),
                phone=verified_data.get('phone', ''),
                work_experience=verified_data.get('work_experience'),
                status=Candidate.Status.NEW
            )
            
            # Update draft status
            draft.status = CandidateDraft.Status.SUBMITTED
            draft.save()
            
            # Log successful submission
            ActionLogger.log_user_action(
                user=request.user,
                action='candidate_submission',
                details={
                    'draft_id': draft.id,
                    'candidate_id': candidate.id,
                    'domain': draft.domain,
                    'role': draft.role
                },
                status='SUCCESS'
            )
            
            return Response({
                'message': 'Candidate submitted successfully',
                'candidate_id': candidate.id,
                'domain': draft.domain,
                'role': draft.role,
                'next_step': 'schedule_interview'
            }, status=status.HTTP_201_CREATED)
            
        except CandidateDraft.DoesNotExist:
            return Response({
                'error': 'Draft not found or not ready for submission'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Log submission error
            ActionLogger.log_user_action(
                user=request.user,
                action='candidate_submission',
                details={
                    'draft_id': draft_id,
                    'error': str(e)
                },
                status='FAILED'
            )
            return Response({
                'error': f'Failed to submit candidate: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

# ────────────────────────────────────────────────────────────────
# Existing Views (Updated with DataIsolationMixin)
# ────────────────────────────────────────────────────────────────

class CandidateListCreateView(DataIsolationMixin, generics.ListCreateAPIView):
    """
    GET  /api/candidates/  → list candidates
    POST /api/candidates/  → create candidate (legacy method)
    """
    queryset           = Candidate.objects.select_related("job")
    permission_classes = [ResumeHierarchyPermission]

    # optional ordering / search helpers
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ["created_at", "updated_at"]
    search_fields   = ["full_name", "email", "domain"]

    def get_serializer_class(self):
        # write operations use the create serializer, reads use the list serializer
        return CandidateCreateSerializer if self.request.method == "POST" else CandidateListSerializer

    def list(self, request, *args, **kwargs):
        """Log candidate listing"""
        ActionLogger.log_user_action(
            user=request.user,
            action='candidate_list',
            details={'count': self.get_queryset().count()},
            status='SUCCESS'
        )
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Log candidate creation"""
        ActionLogger.log_user_action(
            user=request.user,
            action='candidate_create',
            details={'method': 'legacy_direct_creation'},
            status='SUCCESS'
        )
        return super().create(request, *args, **kwargs)


class CandidateDetailView(DataIsolationMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/candidates/<pk>/  → retrieve
    PATCH  /api/candidates/<pk>/  → partial update
    PUT    /api/candidates/<pk>/  → update
    DELETE /api/candidates/<pk>/  → delete
    """
    queryset           = Candidate.objects.select_related("job")
    permission_classes = [ResumeHierarchyPermission]

    def get_serializer_class(self):
        # PUT / PATCH use write serializer; GET uses read serializer
        return (
            CandidateCreateSerializer
            if self.request.method in ("PUT", "PATCH")
            else CandidateListSerializer
        )

    def retrieve(self, request, *args, **kwargs):
        """Log candidate retrieval"""
        ActionLogger.log_user_action(
            user=request.user,
            action='candidate_retrieve',
            details={'candidate_id': kwargs.get('pk')},
            status='SUCCESS'
        )
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Log candidate update"""
        ActionLogger.log_user_action(
            user=request.user,
            action='candidate_update',
            details={'candidate_id': kwargs.get('pk')},
            status='SUCCESS'
        )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Log candidate deletion"""
        ActionLogger.log_user_action(
            user=request.user,
            action='candidate_delete',
            details={'candidate_id': kwargs.get('pk')},
            status='SUCCESS'
        )
        return super().destroy(request, *args, **kwargs)


# ────────────────────────────────────────────────────────────────
# Summary view (kept exactly as you specified)
# ────────────────────────────────────────────────────────────────
class CandidateSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    _pill_codes = [
        "REQUIRES_ACTION",
        "PENDING_SCHEDULING",
        "BR_IN_PROCESS",
        "BR_EVALUATED",
        "INTERNAL_INTERVIEWS",
        "OFFERED",
        "HIRED",
        "REJECTED",
        "OFFER_REJECTED",
        "CANCELLED",
    ]

    def get(self, request, *args, **kwargs):
        """
        GET /api/candidates/summary/  → simple count per status
        """
        summary = (
            Candidate.objects.values("status")
            .annotate(count=Count("id"))
            .order_by()
        )
        # e.g.  [{"status": "invited", "count": 10}, ...]
        return Response(summary)
