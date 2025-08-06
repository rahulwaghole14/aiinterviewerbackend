from django.urls import path
from .views import (
    CompanyListCreateView,
    CompanyDetailView,
    RecruiterListView,
    RecruiterCreateView,
    RecruiterUpdateDeleteView
)

urlpatterns = [
    # Company routes
    path('', CompanyListCreateView.as_view(), name='company-list-create'),
    path('profile/', CompanyListCreateView.as_view(), name='company-profile'),
    path('<int:pk>/', CompanyDetailView.as_view(), name='company-detail'),

    # Recruiter routes
    path('recruiters/', RecruiterListView.as_view(), name='recruiter-list'),
    path('recruiters/create/', RecruiterCreateView.as_view(), name='recruiter-create'),
    path('recruiters/<int:pk>/', RecruiterUpdateDeleteView.as_view(), name='recruiter-update-delete'),
]
