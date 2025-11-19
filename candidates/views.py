from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Candidate, CandidateDraft
from .serializers import (
    CandidateSerializer,
    CandidateListSerializer,
    CandidateCreateSerializer,
    CandidateUpdateSerializer,
    DomainRoleSelectionSerializer,
    DataExtractionSerializer,
    CandidateVerificationSerializer,
    CandidateSubmissionSerializer,
    BulkCandidateCreationSerializer,
)
from jobs.models import Job, Domain
from utils.hierarchy_permissions import DataIsolationMixin, HierarchyPermission
from utils.logger import ActionLogger
from resumes.utils import extract_resume_fields
import PyPDF2
import io


class CandidateListCreateView(DataIsolationMixin, generics.ListCreateAPIView):
    """
    List and create candidates
    """
    queryset = Candidate.objects.select_related('job', 'recruiter').all()
    permission_classes = [HierarchyPermission]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CandidateCreateSerializer
        return CandidateListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Apply data isolation is handled by DataIsolationMixin
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """Log candidate listing"""
        ActionLogger.log_user_action(
            user=request.user,
            action="candidate_list",
            details={"count": self.get_queryset().count()},
            status="SUCCESS",
        )
        return super().list(request, *args, **kwargs)


class CandidateDetailView(DataIsolationMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a candidate
    """
    queryset = Candidate.objects.select_related('job', 'recruiter').all()
    serializer_class = CandidateSerializer
    permission_classes = [HierarchyPermission]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CandidateUpdateSerializer
        return CandidateSerializer


class CandidateSummaryView(APIView):
    """
    Get summary statistics for candidates
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        queryset = Candidate.objects.all()
        
        # Apply data isolation
        if not (getattr(request.user, "role", "").lower() == "admin" or request.user.is_superuser):
            queryset = queryset.filter(recruiter=request.user)
        
        summary = {
            'total': queryset.count(),
            'by_status': {},
            'by_job': {},
        }
        
        for status_code, status_label in Candidate.Status.choices:
            summary['by_status'][status_code] = queryset.filter(status=status_code).count()
        
        return Response(summary)


class DomainRoleSelectionView(APIView):
    """
    Step 1: Select domain and role for candidate creation
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = DomainRoleSelectionSerializer(data=request.data)
        if serializer.is_valid():
            # Create a draft for this step
            draft = CandidateDraft.objects.create(
                user=request.user,
                domain=serializer.validated_data['domain'],
                role=serializer.validated_data['role'],
                status=CandidateDraft.Status.DRAFT
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
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = DataExtractionSerializer(data=request.data)
        if serializer.is_valid():
            resume_file = serializer.validated_data['resume_file']
            domain = serializer.validated_data['domain']
            role = serializer.validated_data['role']
            
            # Extract text from PDF
            try:
                pdf_reader = PyPDF2.PdfReader(resume_file)
                resume_text = ""
                for page in pdf_reader.pages:
                    resume_text += page.extract_text()
            except Exception as e:
                return Response({'error': f'Failed to extract text from PDF: {str(e)}'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Extract fields from text
            extracted_data = extract_resume_fields(resume_text)
            
            # Create or update draft
            draft = CandidateDraft.objects.create(
                user=request.user,
                domain=domain,
                role=role,
                resume_file=resume_file,
                extracted_data=extracted_data,
                status=CandidateDraft.Status.EXTRACTED
            )
            
            return Response({
                'message': 'Resume uploaded and data extracted successfully',
                'draft_id': draft.id,
                'extracted_data': extracted_data,
                'next_step': 'verify_data'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CandidateVerificationView(APIView):
    """
    Step 3 & 4: Preview and update extracted data
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, draft_id):
        draft = get_object_or_404(CandidateDraft, id=draft_id, user=request.user)
        serializer = CandidateVerificationSerializer(draft)
        return Response({
            'message': 'Draft data retrieved for verification',
            'draft': serializer.data
        })
    
    def put(self, request, draft_id):
        draft = get_object_or_404(CandidateDraft, id=draft_id, user=request.user)
        serializer = CandidateVerificationSerializer(draft, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(status=CandidateDraft.Status.VERIFIED)
            return Response({
                'message': 'Draft data updated successfully',
                'draft': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CandidateSubmissionView(APIView):
    """
    Step 5: Final submission - create candidate from draft
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, draft_id):
        draft = get_object_or_404(CandidateDraft, id=draft_id, user=request.user)
        serializer = CandidateSubmissionSerializer(data=request.data)
        
        if serializer.is_valid() and serializer.validated_data['confirm_submission']:
            with transaction.atomic():
                # Create candidate from draft
                verified_data = draft.verified_data or draft.extracted_data
                candidate = Candidate.objects.create(
                    recruiter=request.user,
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
                
                ActionLogger.log_user_action(
                    user=request.user,
                    action="candidate_create",
                    details={"candidate_id": candidate.id, "draft_id": draft_id},
                    status="SUCCESS",
                )
                
                return Response({
                    'message': 'Candidate created successfully',
                    'candidate_id': candidate.id
                }, status=status.HTTP_201_CREATED)
        
        return Response({'error': 'Submission confirmation required'}, 
                      status=status.HTTP_400_BAD_REQUEST)


class BulkCandidateCreationView(APIView):
    """
    Bulk candidate creation endpoint
    Supports two steps:
    - step=extract: Extract data from uploaded resumes (returns extracted_candidates)
    - step=submit: Create candidates from edited data
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        step = request.query_params.get('step', '').lower()
        
        if step == 'extract':
            return self._handle_extract_step(request)
        elif step == 'submit':
            return self._handle_submit_step(request)
        else:
            # Default behavior: direct bulk creation (legacy)
            return self._handle_direct_creation(request)
    
    def _handle_extract_step(self, request):
        """Extract data from uploaded resume files"""
        from resumes.models import extract_text
        from resumes.utils import extract_resume_fields
        import PyPDF2
        import io
        
        # Get domain and role from request
        domain = request.data.get('domain', '')
        role = request.data.get('role', '')
        
        if not domain or not role:
            return Response({
                'error': 'domain and role are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get resume files
        resume_files = request.FILES.getlist('resume_files')
        if not resume_files:
            return Response({
                'error': 'At least one resume file is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        extracted_candidates = []
        successful_extractions = 0
        failed_extractions = 0
        
        for resume_file in resume_files:
            try:
                # Extract text from file
                resume_text = ""
                
                # Handle different file types
                if resume_file.name.lower().endswith('.pdf'):
                    try:
                        # Read PDF file
                        pdf_content = resume_file.read()
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                        for page in pdf_reader.pages:
                            resume_text += page.extract_text()
                        # Reset file pointer for potential future use
                        resume_file.seek(0)
                    except Exception as e:
                        print(f"Error reading PDF {resume_file.name}: {e}")
                        resume_text = ""
                
                elif resume_file.name.lower().endswith(('.docx', '.doc')):
                    try:
                        import docx
                        doc = docx.Document(io.BytesIO(resume_file.read()))
                        resume_text = "\n".join([p.text for p in doc.paragraphs])
                        resume_file.seek(0)
                    except Exception as e:
                        print(f"Error reading DOCX {resume_file.name}: {e}")
                        resume_text = ""
                else:
                    extracted_candidates.append({
                        'filename': resume_file.name,
                        'extracted_data': {},
                        'error': 'Unsupported file type. Only PDF, DOCX, and DOC files are allowed.',
                        'can_edit': False
                    })
                    failed_extractions += 1
                    continue
                
                if not resume_text.strip():
                    extracted_candidates.append({
                        'filename': resume_file.name,
                        'extracted_data': {},
                        'error': 'Could not extract text from file',
                        'can_edit': False
                    })
                    failed_extractions += 1
                    continue
                
                # Extract fields from text
                extracted_data = extract_resume_fields(resume_text)
                
                # Add additional fields that might be useful
                extracted_data.update({
                    'current_company': None,
                    'current_role': None,
                    'expected_salary': 0,
                    'notice_period': 0,
                })
                
                extracted_candidates.append({
                    'filename': resume_file.name,
                    'extracted_data': extracted_data,
                    'can_edit': True
                })
                successful_extractions += 1
                
            except Exception as e:
                print(f"Error processing {resume_file.name}: {e}")
                import traceback
                traceback.print_exc()
                extracted_candidates.append({
                    'filename': resume_file.name,
                    'extracted_data': {},
                    'error': f'Error processing file: {str(e)}',
                    'can_edit': False
                })
                failed_extractions += 1
        
        return Response({
            'message': f'Data extraction completed: {successful_extractions} successful, {failed_extractions} failed',
            'domain': domain,
            'role': role,
            'extracted_candidates': extracted_candidates,
            'summary': {
                'total_files': len(resume_files),
                'successful_extractions': successful_extractions,
                'failed_extractions': failed_extractions
            },
            'next_step': 'review_and_edit'
        }, status=status.HTTP_200_OK)
    
    def _handle_submit_step(self, request):
        """Submit edited candidate data to create candidates"""
        from candidates.serializers import BulkCandidateSubmissionSerializer
        from candidates.models import Candidate
        from resumes.models import Resume
        from jobs.models import Job, Domain
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        serializer = BulkCandidateSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        domain_name = validated_data['domain']
        role_name = validated_data['role']
        poc_email = validated_data.get('poc_email', '')
        candidates_data = validated_data['candidates']
        
        # Get or create domain
        domain, _ = Domain.objects.get_or_create(name=domain_name)
        
        # Get or create job
        # Handle company name - check if user has company and it's not None
        company_name = 'Unknown'
        if hasattr(request.user, 'company') and request.user.company is not None:
            company_name = request.user.company.name
        elif hasattr(request.user, 'company_name') and request.user.company_name:
            company_name = request.user.company_name
        
        # Ensure company_name is not empty (required field)
        if not company_name or company_name.strip() == '':
            company_name = 'Unknown'
        
        # Use filter().first() to handle cases where multiple jobs exist
        # Try to find existing job matching both title and company
        job = Job.objects.filter(
            job_title=role_name,
            company_name=company_name
        ).first()
        
        # If no exact match, try just by title (but only if we have a valid company_name)
        if not job:
            job = Job.objects.filter(job_title=role_name).first()
        
        # If no job exists, enforce explicit configuration before proceeding
        if not job:
            return Response(
                {
                    "error": (
                        f"Job '{role_name}' (company '{company_name}') does not exist. "
                        "Please create the job via the Jobs module and select a coding language before scheduling interviews."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Require the job to have coding_language defined (no automatic fallback)
        if not job.coding_language:
            return Response(
                {
                    "error": (
                        f"Job '{job.job_title}' is missing a coding language. "
                        "Update the job in the Jobs module to set coding_language before scheduling interviews."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update existing job if needed - ensure required fields (excluding coding_language) are set
        update_fields = []
        
        current_company_name = job.company_name or ''
        if not current_company_name.strip():
            job.company_name = company_name
            update_fields.append('company_name')
        elif current_company_name != company_name:
            job.company_name = company_name
            update_fields.append('company_name')
        
        if job.domain != domain:
            job.domain = domain
            update_fields.append('domain')
        
        current_spoc_email = job.spoc_email or ''
        if not current_spoc_email.strip():
            job.spoc_email = request.user.email if hasattr(request.user, 'email') else 'admin@example.com'
            update_fields.append('spoc_email')
        
        current_hiring_manager_email = job.hiring_manager_email or ''
        if not current_hiring_manager_email.strip():
            job.hiring_manager_email = request.user.email if hasattr(request.user, 'email') else 'admin@example.com'
            update_fields.append('hiring_manager_email')
        
        if not job.number_to_hire:
            job.number_to_hire = 1
            update_fields.append('number_to_hire')
        
        if not job.position_level:
            job.position_level = Job.PositionLevel.IC
            update_fields.append('position_level')
        
        if update_fields:
            job.save(update_fields=update_fields)
        else:
            job.save()
        
        # Get recruiter (POC)
        recruiter = request.user
        if poc_email:
            try:
                recruiter = User.objects.get(email=poc_email)
            except User.DoesNotExist:
                pass
        
        results = []
        successful_creations = 0
        failed_creations = 0
        
        for candidate_data in candidates_data:
            try:
                filename = candidate_data['filename']
                edited_data = candidate_data['edited_data']
                
                # Create candidate
                # Only use fields that exist in the Candidate model
                candidate = Candidate.objects.create(
                    full_name=edited_data.get('name', ''),
                    email=edited_data.get('email', ''),
                    phone=edited_data.get('phone', ''),
                    work_experience=edited_data.get('work_experience', 0) or 0,
                    job=job,
                    recruiter=recruiter,
                    domain=domain_name,  # Set domain from the request
                    status=Candidate.Status.NEW,
                )
                
                # Set poc_email if provided
                if poc_email:
                    candidate.poc_email = poc_email
                    candidate.save(update_fields=['poc_email'])
                
                # Create resume (if file exists in memory, would need to be stored)
                # For now, just create a placeholder resume
                resume = Resume.objects.create(
                    user=recruiter,
                    parsed_text=f"Resume for {candidate.full_name}",
                )
                candidate.resume = resume
                candidate.save()
                
                results.append({
                    'success': True,
                    'filename': filename,
                    'candidate_id': candidate.id,
                    'resume_id': resume.id,
                    'candidate_name': candidate.full_name
                })
                successful_creations += 1
                
            except Exception as e:
                print(f"Error creating candidate from {candidate_data.get('filename', 'unknown')}: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    'success': False,
                    'filename': candidate_data.get('filename', 'unknown'),
                    'error': str(e)
                })
                failed_creations += 1
        
        return Response({
            'message': f'Bulk candidate creation completed: {successful_creations} successful, {failed_creations} failed',
            'domain': domain_name,
            'role': role_name,
            'results': results,
            'summary': {
                'total_candidates': len(candidates_data),
                'successful_creations': successful_creations,
                'failed_creations': failed_creations
            }
        }, status=status.HTTP_201_CREATED)
    
    def _handle_direct_creation(self, request):
        """Legacy direct bulk creation (not used by frontend)"""
        serializer = BulkCandidateCreationSerializer(data=request.data)
        if serializer.is_valid():
            # Process bulk creation
            candidates_created = []
            # Implementation would go here
            return Response({
                'message': 'Bulk candidate creation completed',
                'candidates_created': candidates_created
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PendingRequestsView(APIView):
    """
    API endpoint to get pending requests (candidates pending scheduling)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get candidates with pending scheduling status"""
        # Filter candidates by pending scheduling status
        pending_statuses = [
            Candidate.Status.NEW,
            Candidate.Status.PENDING_SCHEDULING,
            Candidate.Status.REQUIRES_ACTION,
        ]
        
        # Apply data isolation based on user role
        if (
            getattr(request.user, "role", "").lower() == "admin"
            or request.user.is_superuser
        ):
            queryset = Candidate.objects.filter(status__in=pending_statuses)
        else:
            queryset = Candidate.objects.filter(
                status__in=pending_statuses,
                recruiter=request.user
            )
        
        # Serialize results
        pending_requests = []
        for candidate in queryset.order_by('-created_at'):
            pending_requests.append({
                'id': candidate.id,
                'full_name': candidate.full_name,
                'email': candidate.email,
                'status': candidate.status,
                'job_title': candidate.job.job_title if candidate.job else None,
                'created_at': candidate.created_at.isoformat() if candidate.created_at else None,
            })
        
        return Response(pending_requests, status=status.HTTP_200_OK)
