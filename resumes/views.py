from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.uploadedfile import UploadedFile
from concurrent.futures import ThreadPoolExecutor
import threading
from .models import Resume
from .serializers import ResumeSerializer, BulkResumeSerializer, ResumeProcessingResultSerializer
from .utils import extract_resume_fields
from utils.hierarchy_permissions import ResumeHierarchyPermission, DataIsolationMixin
from utils.logger import log_resume_upload, log_bulk_resume_upload, log_permission_denied, ActionLogger
from notifications.services import NotificationService

class ResumeViewSet(DataIsolationMixin, ModelViewSet):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    permission_classes = [ResumeHierarchyPermission]

    def perform_create(self, serializer):
        try:
            resume = serializer.save(user=self.request.user)
            
            # Log successful resume upload
            log_resume_upload(
                user=self.request.user,
                resume_id=resume.id,
                filename=resume.file.name if resume.file else 'unknown',
                status='SUCCESS',
                details={
                    'file_size': resume.file.size if resume.file else 0,
                    'content_type': resume.file.content_type if resume.file else 'unknown'
                }
            )
            
            # Process the file after saving to avoid FileDataError
            try:
                if resume.file and hasattr(resume.file, 'path'):
                    from .utils import extract_resume_fields
                    from .models import extract_text
                    
                    # Extract text from file
                    parsed_text = extract_text(resume.file.path)
                    if parsed_text:
                        resume.parsed_text = parsed_text
                        resume.save(update_fields=["parsed_text"])
                        
                        # Log text extraction success
                        ActionLogger.log_user_action(
                            user=self.request.user,
                            action='resume_text_extraction',
                            details={
                                'resume_id': resume.id,
                                'text_length': len(parsed_text)
                            },
                            status='SUCCESS'
                        )
                        
                        # Send notification for resume processing
                        NotificationService.send_resume_processed_notification(resume, self.request.user)
            except Exception as e:
                # Log text extraction failure
                ActionLogger.log_user_action(
                    user=self.request.user,
                    action='resume_text_extraction',
                    details={
                        'resume_id': resume.id,
                        'error': str(e)
                    },
                    status='FAILED'
                )
                
        except Exception as e:
            # Log resume upload failure
            log_resume_upload(
                user=self.request.user,
                resume_id=None,
                filename='unknown',
                status='FAILED',
                details={'error': str(e)}
            )
            raise

    def get_queryset(self):
        """Log resume listing"""
        queryset = super().get_queryset()
        
        ActionLogger.log_user_action(
            user=self.request.user,
            action='resume_list',
            details={'count': queryset.count()},
            status='SUCCESS'
        )
        
        return queryset

    def retrieve(self, request, *args, **kwargs):
        """Log resume retrieval"""
        ActionLogger.log_user_action(
            user=request.user,
            action='resume_retrieve',
            details={'resume_id': kwargs.get('pk')},
            status='SUCCESS'
        )
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Log resume update"""
        ActionLogger.log_user_action(
            user=request.user,
            action='resume_update',
            details={'resume_id': kwargs.get('pk')},
            status='SUCCESS'
        )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Log resume deletion"""
        ActionLogger.log_user_action(
            user=request.user,
            action='resume_delete',
            details={'resume_id': kwargs.get('pk')},
            status='SUCCESS'
        )
        return super().destroy(request, *args, **kwargs)

class BulkResumeUploadView(APIView):
    permission_classes = [ResumeHierarchyPermission]
    
    def post(self, request):
        try:
            serializer = BulkResumeSerializer(data=request.data)
            if not serializer.is_valid():
                # Log validation failure
                ActionLogger.log_user_action(
                    user=request.user,
                    action='bulk_resume_upload',
                    details={
                        'errors': serializer.errors,
                        'file_count': len(request.FILES.getlist('files', []))
                    },
                    status='FAILED'
                )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            files = serializer.validated_data['files']
            results = []
            
            # Log bulk upload start
            ActionLogger.log_user_action(
                user=request.user,
                action='bulk_resume_upload_start',
                details={'file_count': len(files)},
                status='SUCCESS'
            )
            
            # Process files sequentially to avoid file handling issues
            for file in files:
                try:
                    result = self._process_single_resume(file, request.user)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'success': False,
                        'filename': file.name,
                        'error_message': str(e)
                    })
            
            # Count successes and failures
            successful_uploads = sum(1 for r in results if r['success'])
            failed_uploads = len(results) - successful_uploads
            
            # Log bulk upload completion
            log_bulk_resume_upload(
                user=request.user,
                file_count=len(results),
                success_count=successful_uploads,
                failed_count=failed_uploads,
                status='SUCCESS',
                details={
                    'results': results,
                    'ip_address': request.META.get('REMOTE_ADDR')
                }
            )
            
            # Prepare response data
            response_data = {
                'message': f'Processed {len(results)} resumes: {successful_uploads} successful, {failed_uploads} failed',
                'results': results,
                'summary': {
                    'total_files': len(results),
                    'successful': successful_uploads,
                    'failed': failed_uploads
                }
            }
            
            # Send notification for bulk upload completion
            NotificationService.send_bulk_upload_completed_notification(request.user, response_data)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log bulk upload failure
            ActionLogger.log_user_action(
                user=request.user,
                action='bulk_resume_upload',
                details={'error': str(e)},
                status='FAILED'
            )
            raise
    
    def _process_single_resume(self, file: UploadedFile, user):
        """Process a single resume file and return result"""
        try:
            # Validate file type
            if not file.name.lower().endswith(('.pdf', '.docx', '.doc')):
                ActionLogger.log_user_action(
                    user=user,
                    action='resume_upload_validation_failed',
                    details={
                        'filename': file.name,
                        'reason': 'Unsupported file type'
                    },
                    status='FAILED'
                )
                return {
                    'success': False,
                    'filename': file.name,
                    'error_message': 'Unsupported file type. Only PDF, DOCX, and DOC files are allowed.'
                }
            
            # Create resume object
            resume = Resume.objects.create(
                user=user,
                file=file
            )
            
            # Wait a moment for file to be saved, then extract data
            import time
            time.sleep(0.1)  # Small delay to ensure file is saved
            
            # Refresh the resume object to get the parsed text
            resume.refresh_from_db()
            
            # Extract data from parsed text
            extracted_data = {}
            if resume.parsed_text:
                from .utils import extract_resume_fields
                extracted_data = extract_resume_fields(resume.parsed_text)
                
                # Log successful text extraction
                ActionLogger.log_user_action(
                    user=user,
                    action='resume_text_extraction',
                    details={
                        'resume_id': resume.id,
                        'filename': file.name,
                        'text_length': len(resume.parsed_text),
                        'extracted_fields': list(extracted_data.keys())
                    },
                    status='SUCCESS'
                )
            
            return {
                'success': True,
                'filename': file.name,
                'resume_id': resume.id,
                'extracted_data': extracted_data
            }
            
        except Exception as e:
            # Log processing failure
            ActionLogger.log_user_action(
                user=user,
                action='resume_processing_failed',
                details={
                    'filename': file.name,
                    'error': str(e)
                },
                status='FAILED'
            )
            return {
                'success': False,
                'filename': file.name,
                'error_message': str(e)
            }
