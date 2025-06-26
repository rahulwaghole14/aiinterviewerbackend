from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from candidates.models import Candidate
from candidates.serializers import CandidateSerializer, CandidateCreateSerializer


class CandidateListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        qs = Candidate.objects.select_related('resume', 'job', 'recruiter')
        return qs if getattr(user, 'role', None) == 'admin' else qs.filter(recruiter=user)

    def get_serializer_class(self):
        return CandidateCreateSerializer if self.request.method == 'POST' else CandidateSerializer
