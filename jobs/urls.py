from django.urls import path
from .views import (
    # Domain management views
    DomainListCreateView,
    DomainDetailView,
    DomainActiveListView,
    # Job management views
    JobListCreateView,
    JobDetailView,
    JobTitleListView,
    JobsByDomainView
)

urlpatterns = [
    # Domain management endpoints
    path('domains/', DomainListCreateView.as_view(), name='domain-list-create'),
    path('domains/active/', DomainActiveListView.as_view(), name='domain-active-list'),
    path('domains/<int:pk>/', DomainDetailView.as_view(), name='domain-detail'),
    
    # Job management endpoints
    path('', JobListCreateView.as_view(), name='job-list-create'),
    path('<int:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('titles/', JobTitleListView.as_view(), name='job-title-list'),
    path('by-domain/<int:domain_id>/', JobsByDomainView.as_view(), name='jobs-by-domain'),
]
