from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Resume
from .serializers import ResumeSerializer
import os

class ResumeViewSet(ModelViewSet):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Check if user already has a resume
        existing_resume = Resume.objects.filter(user=self.request.user).first()

        if existing_resume:
            # Delete the old resume file from storage
            if existing_resume.file and os.path.isfile(existing_resume.file.path):
                os.remove(existing_resume.file.path)
            # Delete the old resume record from database
            existing_resume.delete()

        # Save the new resume
        serializer.save(user=self.request.user)
