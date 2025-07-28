from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    InterviewViewSet,
    InterviewStatusSummaryView,
    StartAIInterviewView,
    RecordInterviewResponseView,
    SubmitInterviewView,
)

# DRF router for CRUD endpoints
router = DefaultRouter()
router.register(r"", InterviewViewSet, basename="interview")

urlpatterns = [
    # Summary view
    path("summary/", InterviewStatusSummaryView.as_view(), name="interview-summary"),

    # AI Interview Endpoints
    path("start/", StartAIInterviewView.as_view(), name="interview-start"),
    path("record/", RecordInterviewResponseView.as_view(), name="interview-record"),
    path("submit/", SubmitInterviewView.as_view(), name="interview-submit"),

    # Standard CRUD routes
    path("", include(router.urls)),
]
