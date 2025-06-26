from django.urls import path
from .views import JobListCreateView

urlpatterns = [
    path('create/', JobListCreateView.as_view(), name='job-create'),
]
