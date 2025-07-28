from django.db.models import Count
from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from .models import Candidate
from resumes.models import Resume, extract_resume_fields
from utils.name_parser import parse_candidate_name
from .serializers import CandidateCreateSerializer, CandidateListSerializer


class CandidateListCreateView(generics.ListCreateAPIView):
    queryset = Candidate.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ["created_at", "last_updated"]
    search_fields = ["full_name", "email", "domain"]

    def get_serializer_class(self):
        return CandidateCreateSerializer if self.request.method == "POST" else CandidateListSerializer

    def create(self, request, *args, **kwargs):
        user = request.user
        domain = request.data.get("domain")
        poc_email = request.data.get("poc_email")
        job_title = request.data.get("job_title")
        files = request.FILES.getlist("resume_file")

        if not all([domain, poc_email, job_title, files]):
            return Response(
                {"error": "Fields 'domain', 'poc_email', 'job_title', and at least one 'resume_file' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing_count = Candidate.objects.filter(
            recruiter=user, domain=domain, job_title=job_title, poc_email=poc_email
        ).count()

        if existing_count + len(files) > 10:
            return Response({
                "error": f"Cannot upload {len(files)} resumes. Only {10 - existing_count} slots remaining."
            }, status=status.HTTP_400_BAD_REQUEST)

        created = []

        for file in files:
            resume = Resume(user=user, file=file)
            resume.save()
            parsed = extract_resume_fields(resume.parsed_text)

            candidate = Candidate.objects.create(
                recruiter=user,
                resume=resume,
                full_name=parse_candidate_name(parsed.get("name", "")),
                email=parsed.get("email", ""),
                phone=parsed.get("phone", ""),
                work_experience=parsed.get("work_experience"),
                domain=domain,
                poc_email=poc_email,
                job_title=job_title,
            )

            created.append({
                "id": candidate.id,
                "full_name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone,
                "work_experience": candidate.work_experience,
                "domain": domain,
                "poc_email": poc_email,
                "job_title": job_title,
            })

        return Response(created, status=status.HTTP_201_CREATED)


class CandidateDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Candidate.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return CandidateCreateSerializer if self.request.method in ("PUT", "PATCH") else CandidateListSerializer


class CandidateSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        summary = (
            Candidate.objects.values("status")
            .annotate(count=Count("id"))
            .order_by()
        )
        return Response(summary)
