from rest_framework import generics
from .models import Job
from .serializers import JobSerializer

class JobListCreateView(generics.ListCreateAPIView):  # ✅ This allows GET + POST
    queryset = Job.objects.all()
    serializer_class = JobSerializer
