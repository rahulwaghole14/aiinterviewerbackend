from django.urls import path
from .views import (
    CandidateListCreateView,
    CandidateDetailView,
    CandidateSummaryView,
    # New step-by-step views
    DomainRoleSelectionView,
    DataExtractionView,
    CandidateVerificationView,
    CandidateSubmissionView
)

urlpatterns = [
    # Step-by-step candidate creation endpoints
    path('select-domain/', DomainRoleSelectionView.as_view(), name='domain-role-selection'),
    path('extract-data/', DataExtractionView.as_view(), name='data-extraction'),
    path('verify/<int:draft_id>/', CandidateVerificationView.as_view(), name='candidate-verification'),
    path('submit/<int:draft_id>/', CandidateSubmissionView.as_view(), name='candidate-submission'),
    
    # Existing endpoints
    path('', CandidateListCreateView.as_view(), name='candidate-list-create'),
    path('<int:pk>/', CandidateDetailView.as_view(), name='candidate-detail'),
    path('summary/', CandidateSummaryView.as_view(), name='candidate-summary'),
]
