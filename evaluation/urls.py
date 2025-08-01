from django.urls import path
from .views import (
    EvaluationSummaryView,
    EvaluationReportView,
    SubmitFeedbackView,
    AllFeedbacksView
)

urlpatterns = [
    path("", EvaluationSummaryView.as_view(), name="evaluation-list"),  # Root path for listing
    path("<uuid:interview_id>/", EvaluationSummaryView.as_view(), name="evaluation-summary"),
    path("report/<uuid:interview_id>/", EvaluationReportView.as_view(), name="evaluation-report"),
    path("feedback/manual/", SubmitFeedbackView.as_view(), name="submit-feedback"),
    path("feedback/all/<int:candidate_id>/", AllFeedbacksView.as_view(), name="all-feedbacks"),
]
