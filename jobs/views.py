from rest_framework import generics, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Job
from .serializers import JobSerializer, JobTitleSerializer

# ✅ GET all jobs, POST a new job, with filtering, search & ordering
class JobListCreateView(generics.ListCreateAPIView):
    queryset = Job.objects.all().order_by('-created_at')
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company_name', 'position_level']
    search_fields = ['job_title', 'tech_stack_details']
    ordering_fields = ['created_at', 'job_title']

# ✅ GET, PUT, DELETE a specific job by ID
class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    lookup_field = "id"

# ✅ GET only job titles (for dropdowns or display)
class JobTitleListView(generics.ListAPIView):
    queryset = Job.objects.all()
    serializer_class = JobTitleSerializer
