# ai_interview/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# No router needed - using individual views

urlpatterns = [
    # AI Interview Link Management
    path('generate-link/<uuid:interview_id>/', views.GenerateAIInterviewLinkView.as_view(), name='ai-interview-generate-link'),
    path('get-link/<uuid:interview_id>/', views.GetAIInterviewLinkView.as_view(), name='ai-interview-get-link'),
    path('regenerate-link/<uuid:interview_id>/', views.RegenerateAIInterviewLinkView.as_view(), name='ai-interview-regenerate-link'),
    
    # Public AI interview endpoints (no authentication required)
    path('public/start/', views.PublicStartInterviewView.as_view(), name='ai-interview-public-start'),
    path('public/submit-response/', views.PublicSubmitResponseView.as_view(), name='ai-interview-public-submit-response'),
    path('public/complete/', views.PublicCompleteInterviewView.as_view(), name='ai-interview-public-complete'),
    
    # Main AI interview endpoints (authenticated)
    path('start/', views.StartInterviewView.as_view(), name='ai-interview-start'),
    path('submit-response/', views.SubmitResponseView.as_view(), name='ai-interview-submit-response'),
    path('complete/', views.CompleteInterviewView.as_view(), name='ai-interview-complete'),
    
    # Detail views
    path('sessions/<int:pk>/', views.AIInterviewSessionDetailView.as_view(), name='ai-interview-session-detail'),
    path('questions/', views.AIInterviewQuestionListView.as_view(), name='ai-interview-questions'),
    path('responses/', views.AIInterviewResponseListView.as_view(), name='ai-interview-responses'),
    path('results/<int:pk>/', views.AIInterviewResultDetailView.as_view(), name='ai-interview-result-detail'),
    
    # Session endpoints
    path('sessions/', views.AIInterviewSessionViewSet.as_view(), name='ai-interview-sessions'),
]
