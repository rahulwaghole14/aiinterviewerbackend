from django.urls import path
from .views import JobListCreateView, JobDetailView, JobTitleListView

urlpatterns = [
    path('', JobListCreateView.as_view(), name='job-list-create'),         # GET, POST
    path('<int:id>/', JobDetailView.as_view(), name='job-detail'),         # GET, PUT, DELETE
    path('titles/', JobTitleListView.as_view(), name='job-titles'),        # GET
]
