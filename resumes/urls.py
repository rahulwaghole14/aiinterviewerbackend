from django.urls import path
from .views import ResumeViewSet, BulkResumeUploadView

urlpatterns = [
    path("bulk-upload/", BulkResumeUploadView.as_view(), name="resume-bulk-upload"),
]
