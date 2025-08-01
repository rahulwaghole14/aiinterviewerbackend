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

class ResumeViewSet(ModelViewSet):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BulkResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = BulkResumeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        files = serializer.validated_data['files']
        results = []
        
        # Process files concurrently for better performance
        with ThreadPoolExecutor(max_workers=min(len(files), 5)) as executor:
            future_to_file = {
                executor.submit(self._process_single_resume, file, request.user): file 
                for file in files
            }
            
            for future in future_to_file:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    file = future_to_file[future]
                    results.append({
                        'success': False,
                        'filename': file.name,
                        'error_message': str(e)
                    })
        
        # Count successes and failures
        successful_uploads = sum(1 for r in results if r['success'])
        failed_uploads = len(results) - successful_uploads
        
        return Response({
            'message': f'Processed {len(results)} resumes: {successful_uploads} successful, {failed_uploads} failed',
            'results': results,
            'summary': {
                'total_files': len(results),
                'successful': successful_uploads,
                'failed': failed_uploads
            }
        }, status=status.HTTP_200_OK)
    
    def _process_single_resume(self, file: UploadedFile, user):
        """Process a single resume file and return result"""
        try:
            # Validate file type
            if not file.name.lower().endswith(('.pdf', '.docx', '.doc')):
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
            
            # Extract data from parsed text
            extracted_data = extract_resume_fields(resume.parsed_text) if resume.parsed_text else {}
            
            return {
                'success': True,
                'filename': file.name,
                'resume_id': resume.id,
                'extracted_data': extracted_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'filename': file.name,
                'error_message': str(e)
            }
