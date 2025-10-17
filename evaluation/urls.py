from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EvaluationViewSet,
    EvaluationSummaryView,
    EvaluationReportView,
    SubmitFeedbackView,
    AllFeedbacksView,
)

# Create router for evaluation CRUD operations
router = DefaultRouter()
router.register(r"crud", EvaluationViewSet, basename="evaluation-crud")

urlpatterns = [
    # CRUD operations for evaluations
    path("", include(router.urls)),
    # Legacy endpoints (keep for backward compatibility)
    path(
        "summary/<uuid:interview_id>/",
        EvaluationSummaryView.as_view(),
        name="evaluation-summary",
    ),
    path(
        "report/<uuid:interview_id>/",
        EvaluationReportView.as_view(),
        name="evaluation-report",
    ),
    path("feedback/manual/", SubmitFeedbackView.as_view(), name="submit-feedback"),
    path(
        "feedback/all/<int:candidate_id>/",
        AllFeedbacksView.as_view(),
        name="all-feedbacks",
    ),
]
