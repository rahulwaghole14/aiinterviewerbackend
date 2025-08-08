# candidates/views.py
from django.db.models import Count
from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
import uuid
import os

from .models      import Candidate, CandidateDraft
from .serializers import (
    CandidateCreateSerializer,   # serializer for POST / PUT / PATCH
    CandidateListSerializer,     # serializer for GET (list / detail)
    CandidateUpdateSerializer,   # serializer for PUT / PATCH updates
    # New step-by-step serializers
    DomainRoleSelectionSerializer,
    DataExtractionSerializer,
    CandidateVerificationSerializer,
    CandidateSubmissionSerializer,
    # New bulk candidate serializers
    BulkCandidateCreationSerializer,
    BulkCandidateSubmissionSerializer
)
from utils.hierarchy_permissions import ResumeHierarchyPermission, DataIsolationMixin
from utils.logger import ActionLogger
from notifications.services import NotificationService
from resumes.models import Resume, extract_resume_fields
from utils.name_parser import parse_candidate_name
from jobs.models import Job

# ────────────────────────────────────────────────────────────────
# Enhanced Bulk Candidate Creation Views
# ────────────────────────────────────────────────────────────────

class BulkCandidateCreationView(APIView):
    """
    Bulk candidate creation from multiple resume files with two-step flow support
    POST /api/candidates/bulk-create/?step=extract (for data extraction and preview)
    POST /api/candidates/bulk-create/?step=submit (for final candidate creation)
    """
    permission_classes = [ResumeHierarchyPermission]

    def post(self, request):
        """Handle bulk candidate creation with two-step flow"""
        step = request.query_params.get('step', 'create')  # Default to direct creation
        
        if step == 'extract':
            return self._extract_data(request)
        elif step == 'submit':
            return self._submit_candidates(request)
        else:
            # Default behavior - direct creation (backward compatibility)
            return self._create_candidates_directly(request)

    def _extract_data(self, request):
        """Step 1: Extract data from resumes for preview/editing"""
        serializer = BulkCandidateCreationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        domain = serializer.validated_data['domain']
        role = serializer.validated_data['role']
        resume_files = serializer.validated_data['resume_files']

        extracted_candidates = []
        failed_extractions = 0

        # Log bulk extraction start
        ActionLogger.log_user_action(
            user=request.user,
            action='bulk_candidate_extraction_start',
            details={
                'domain': domain,
                'role': role,
                'file_count': len(resume_files)
            },
            status='SUCCESS'
        )

        # Process each resume file
        for resume_file in resume_files:
            try:
                extracted_data = self._extract_candidate_data(resume_file, request.user)
                if extracted_data:
                    # Try to get the resume_url if the file has a url attribute
                    resume_url = None
                    unique_filename = extracted_data.pop('unique_resume_filename', None)
                    if unique_filename:
                        resume_url = request.build_absolute_uri(f'/media/resumes/{unique_filename}')
                    extracted_candidates.append({
                        'filename': resume_file.name,
                        'extracted_data': extracted_data,
                        'resume_url': resume_url,
                        'can_edit': True
                    })
                else:
                    failed_extractions += 1
                    extracted_candidates.append({
                        'filename': resume_file.name,
                        'error': 'Failed to extract data from resume',
                        'extracted_data': {},
                        'resume_url': None,
                        'can_edit': False
                    })

            except Exception as e:
                failed_extractions += 1
                extracted_candidates.append({
                    'filename': resume_file.name,
                    'error': str(e),
                    'extracted_data': {},
                    'resume_url': None,
                    'can_edit': False
                })

        # Log extraction completion
        ActionLogger.log_user_action(
            user=request.user,
            action='bulk_candidate_extraction_complete',
            details={
                'domain': domain,
                'role': role,
                'total_files': len(resume_files),
                'successful_extractions': len(extracted_candidates) - failed_extractions,
                'failed_extractions': failed_extractions
            },
            status='SUCCESS'
        )

        response_data = {
            'message': f'Data extraction completed: {len(extracted_candidates) - failed_extractions} successful, {failed_extractions} failed',
            'domain': domain,
            'role': role,
            'extracted_candidates': extracted_candidates,
            'summary': {
                'total_files': len(resume_files),
                'successful_extractions': len(extracted_candidates) - failed_extractions,
                'failed_extractions': failed_extractions
            },
            'next_step': 'review_and_edit'
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def _submit_candidates(self, request):
        """Step 2: Create candidates from edited data, associating resumes"""
        domain = request.data.get('domain')
        role = request.data.get('role')
        candidates_data = request.data.get('candidates', [])
        poc_email = request.data.get('poc_email')  # Get global poc_email for all candidates
        if not domain or not role or not candidates_data:
            return Response({
                'error': 'Missing required fields: domain, role, or candidates data'
            }, status=status.HTTP_400_BAD_REQUEST)
        results = []
        successful_creations = 0
        failed_creations = 0
        ActionLogger.log_user_action(
            user=request.user,
            action='bulk_candidate_submission_start',
            details={
                'domain': domain,
                'role': role,
                'candidate_count': len(candidates_data)
            },
            status='SUCCESS'
        )
        from resumes.models import Resume
        for candidate_info in candidates_data:
            try:
                filename = candidate_info.get('filename')
                edited_data = candidate_info.get('edited_data', {})
                unique_resume_filename = edited_data.get('unique_resume_filename')
                resume_obj = None
                if unique_resume_filename:
                    try:
                        resume_obj = Resume.objects.get(file=f"resumes/{unique_resume_filename}")
                    except Resume.DoesNotExist:
                        resume_obj = None
                if not filename or not edited_data:
                    failed_creations += 1
                    results.append({
                        'filename': filename or 'Unknown',
                        'status': 'failed',
                        'error': 'Missing filename or edited data'
                    })
                    continue
                candidate = self._create_candidate_from_data(edited_data, domain, role, request.user, resume=resume_obj, poc_email=poc_email)
                if isinstance(candidate, str):
                    failed_creations += 1
                    results.append({
                        'filename': filename,
                        'status': 'failed',
                        'error': candidate  # Specific error message
                    })
                elif candidate:
                    successful_creations += 1
                    results.append({
                        'filename': filename,
                        'status': 'success',
                        'candidate_id': candidate.id,
                        'candidate_name': candidate.full_name,
                        'resume_url': request.build_absolute_uri(candidate.resume.file.url) if candidate.resume else None
                    })
                else:
                    failed_creations += 1
                    results.append({
                        'filename': filename,
                        'status': 'failed',
                        'error': 'Unknown error during candidate creation'
                    })
            except Exception as e:
                failed_creations += 1
                results.append({
                    'filename': candidate_info.get('filename', 'Unknown'),
                    'status': 'failed',
                    'error': str(e)
                })
        ActionLogger.log_user_action(
            user=request.user,
            action='bulk_candidate_submission_complete',
            details={
                'domain': domain,
                'role': role,
                'total_candidates': len(candidates_data),
                'successful_creations': successful_creations,
                'failed_creations': failed_creations
            },
            status='SUCCESS'
        )
        response_data = {
            'message': f'Candidate creation completed: {successful_creations} successful, {failed_creations} failed',
            'results': results,
            'summary': {
                'total_candidates': len(candidates_data),
                'successful_creations': successful_creations,
                'failed_creations': failed_creations
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def _create_candidates_directly(self, request):
        """Original behavior - direct creation (backward compatibility)"""
        serializer = BulkCandidateCreationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        domain = serializer.validated_data['domain']
        role = serializer.validated_data['role']
        resume_files = serializer.validated_data['resume_files']
        poc_email = request.data.get('poc_email')  # Get poc_email from request data

        created_candidates = []
        failed_creations = 0

        # Log bulk creation start
        ActionLogger.log_user_action(
            user=request.user,
            action='bulk_candidate_creation_start',
            details={
                'domain': domain,
                'role': role,
                'file_count': len(resume_files)
            },
            status='SUCCESS'
        )

        # Process each resume file
        for resume_file in resume_files:
            try:
                candidate = self._process_single_candidate(resume_file, domain, role, request.user, poc_email=poc_email)
                if candidate:
                    created_candidates.append({
                        'id': candidate.id,
                        'name': candidate.full_name,
                        'email': candidate.email,
                        'resume_url': request.build_absolute_uri(candidate.resume.file.url) if candidate.resume else None
                    })
                else:
                    failed_creations += 1

            except Exception as e:
                failed_creations += 1
                ActionLogger.log_user_action(
                    user=request.user,
                    action='candidate_creation_failed',
                    details={
                        'filename': resume_file.name,
                        'error': str(e)
                    },
                    status='FAILED'
                )

        # Log creation completion
        ActionLogger.log_user_action(
            user=request.user,
            action='bulk_candidate_creation_complete',
            details={
                'domain': domain,
                'role': role,
                'total_files': len(resume_files),
                'successful_creations': len(created_candidates),
                'failed_creations': failed_creations
            },
            status='SUCCESS'
        )

        # Send notification
        if created_candidates:
            NotificationService.send_bulk_candidate_creation_notification(
                user=request.user,
                successful_count=len(created_candidates),
                domain=domain,
                role=role
            )

        response_data = {
            'message': f'Bulk candidate creation completed: {len(created_candidates)} successful, {failed_creations} failed',
            'created_candidates': created_candidates,
            'summary': {
                'total_files': len(resume_files),
                'successful_creations': len(created_candidates),
                'failed_creations': failed_creations
            }
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    def _extract_candidate_data(self, resume_file: UploadedFile, user):
        """Extract candidate data from a single resume file, saving with a unique name"""
        try:
            # Generate a unique filename
            ext = os.path.splitext(resume_file.name)[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            unique_path = os.path.join('resumes', unique_filename)

            # Save the file to the media/resumes/ directory
            from django.core.files.storage import default_storage
            saved_path = default_storage.save(unique_path, resume_file)

            # Create temporary resume object for text extraction
            from resumes.models import Resume
            temp_resume = Resume.objects.create(user=user, file=saved_path)

            import time
            time.sleep(0.1)  # Small delay to ensure file is saved
            temp_resume.refresh_from_db()

            extracted_data = {}
            if temp_resume.parsed_text:
                extracted_data = extract_resume_fields(temp_resume.parsed_text)
                if extracted_data.get('name'):
                    extracted_data['name'] = parse_candidate_name(extracted_data['name'])

            # Save the unique filename for use in resume_url
            extracted_data['unique_resume_filename'] = unique_filename

            # Clean up temporary resume
            temp_resume.delete()

            return extracted_data
        except Exception as e:
            ActionLogger.log_user_action(
                user=user,
                action='resume_extraction_failed',
                details={
                    'filename': resume_file.name,
                    'error': str(e)
                },
                status='FAILED'
            )
            return None

    def _create_candidate_from_data(self, candidate_data: dict, domain: str, role: str, user, resume=None, poc_email=None):
        """Create candidate from edited data, associating with a Resume object if provided"""
        try:
            candidate_info = {
                'full_name': candidate_data.get('name', 'Unknown'),
                'email': candidate_data.get('email', ''),
                'phone': candidate_data.get('phone', ''),
                'work_experience': candidate_data.get('work_experience', 0),
                'domain': domain,
                'recruiter': user,
                'resume': resume,
                'poc_email': poc_email or candidate_data.get('poc_email', '')  # Use global poc_email or individual poc_email
            }
            candidate = Candidate.objects.create(**candidate_info)
            try:
                job = Job.objects.get(domain__name__iexact=domain, job_title__iexact=role)
                candidate.job = job
                candidate.save()
            except Job.DoesNotExist:
                pass
            return candidate
        except Exception as e:
            ActionLogger.log_user_action(
                user=user,
                action='candidate_creation_failed',
                details={
                    'error': str(e)
                },
                status='FAILED'
            )
            return str(e)

    def _process_single_candidate(self, resume_file: UploadedFile, domain: str, role: str, user, poc_email=None):
        """Process a single resume file and create candidate"""
        try:
            # Create resume object
            resume = Resume.objects.create(user=user, file=resume_file)

            # Extract data from resume
            extracted_data = {}
            if resume.parsed_text:
                extracted_data = extract_resume_fields(resume.parsed_text)

                # Clean name if extracted
                if extracted_data.get('name'):
                    extracted_data['name'] = parse_candidate_name(extracted_data['name'])

            # Create candidate with extracted data
            candidate_data = {
                'full_name': extracted_data.get('name', 'Unknown'),
                'email': extracted_data.get('email', ''),
                'phone': extracted_data.get('phone', ''),
                'work_experience': extracted_data.get('experience', 0),
                'domain': domain,
                'recruiter': user,
                'resume': resume,
                'poc_email': poc_email or extracted_data.get('poc_email', '')
            }

            # Create candidate
            candidate = Candidate.objects.create(**candidate_data)

            # Associate with job if domain/role match exists
            try:
                job = Job.objects.get(domain__name__iexact=domain, job_title__iexact=role)
                candidate.job = job
                candidate.save()
            except Job.DoesNotExist:
                pass  # Job not found, candidate created without job association

            return candidate

        except Exception as e:
            ActionLogger.log_user_action(
                user=user,
                action='candidate_creation_failed',
                details={
                    'filename': resume_file.name,
                    'error': str(e)
                },
                status='FAILED'
            )
            return None

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
            
            # Send notification for candidate addition
            NotificationService.send_candidate_added_notification(candidate, request.user)
            
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
        # PUT / PATCH use update serializer; GET uses read serializer
        return (
            CandidateUpdateSerializer
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
