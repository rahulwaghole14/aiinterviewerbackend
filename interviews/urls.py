# interviews/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'slots', views.InterviewSlotViewSet, basename='interview-slots')
router.register(r'schedules', views.InterviewScheduleViewSet, basename='interview-schedules')
router.register(r'availability', views.InterviewerAvailabilityViewSet, basename='interviewer-availability')
router.register(r'conflicts', views.InterviewConflictViewSet, basename='interview-conflicts')

urlpatterns = [
    # Existing interview endpoints
    path('', views.InterviewListCreateView.as_view(), name='interview-list-create'),
    path('<uuid:pk>/', views.InterviewDetailView.as_view(), name='interview-detail'),
    path('<uuid:pk>/feedback/', views.InterviewFeedbackView.as_view(), name='interview-feedback'),
    
    # Slot management endpoints
    path('', include(router.urls)),
    
    # Utility endpoints
    path('available-slots/', views.SlotAvailabilityView.as_view(), name='available-slots'),
    path('calendar/', views.InterviewCalendarView.as_view(), name='interview-calendar'),
]
