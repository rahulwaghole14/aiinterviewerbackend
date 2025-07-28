from django.urls import path
from .views import CandidateListCreateView, CandidateDetailView, CandidateSummaryView

urlpatterns = [
    path("", CandidateListCreateView.as_view(), name="candidate-list-create"),
    path("<int:pk>/", CandidateDetailView.as_view(), name="candidate-detail"),
    path("summary/", CandidateSummaryView.as_view(), name="candidate-summary"),
]
