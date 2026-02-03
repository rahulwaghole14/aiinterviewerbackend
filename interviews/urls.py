# interviews/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r"slots", views.InterviewSlotViewSet, basename="interview-slots")
router.register(
    r"schedules", views.InterviewScheduleViewSet, basename="interview-schedules"
)
router.register(
    r"configurations",
    views.AIInterviewConfigurationViewSet,
    basename="ai-interview-configurations",
)
router.register(
    r"conflicts", views.InterviewConflictViewSet, basename="interview-conflicts"
)

urlpatterns = [
    # Public interview access (no authentication required)
    path(
        "public/<str:link_token>/",
        views.PublicInterviewAccessView.as_view(),
        name="public-interview-access",
    ),
    # Existing interview endpoints
    path("", views.InterviewListCreateView.as_view(), name="interview-list-create"),
    path("<uuid:pk>/", views.InterviewDetailView.as_view(), name="interview-detail"),
    path(
        "<uuid:pk>/feedback/",
        views.InterviewFeedbackView.as_view(),
        name="interview-feedback",
    ),
    path(
        "<uuid:pk>/generate-link/",
        views.InterviewGenerateLinkView.as_view(),
        name="interview-generate-link",
    ),
    path(
        "<uuid:pk>/download-pdf/",
        views.InterviewDownloadPDFView.as_view(),
        name="interview-download-pdf",
    ),
    # Slot management endpoints
    path("", include(router.urls)),
    # Utility endpoints
    path(
        "available-slots/", views.SlotAvailabilityView.as_view(), name="available-slots"
    ),
    path("calendar/", views.InterviewCalendarView.as_view(), name="interview-calendar"),
    # Screen recording endpoints
    path(
        "<uuid:pk>/screen-recording/upload/",
        views.ScreenRecordingUploadView.as_view(),
        name="screen-recording-upload",
    ),
    path(
        "<uuid:pk>/screen-recording/delete/",
        views.ScreenRecordingDeleteView.as_view(),
        name="screen-recording-delete",
    ),
]
