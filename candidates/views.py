# candidates/views.py
from django.db.models import Count
from rest_framework import generics, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response

from .models      import Candidate
from .serializers import (
    CandidateCreateSerializer,   # serializer for POST / PUT / PATCH
    CandidateListSerializer      # serializer for GET (list / detail)
)


# ────────────────────────────────────────────────────────────────
# List & Create  →  /api/candidates/
# ────────────────────────────────────────────────────────────────
class CandidateListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/candidates/  → list candidates
    POST /api/candidates/  → create candidate
    """
    queryset           = Candidate.objects.select_related("job")
    permission_classes = [permissions.IsAuthenticated]

    # optional ordering / search helpers
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ["created_at", "updated_at"]
    search_fields   = ["full_name", "email", "domain"]

    def get_serializer_class(self):
        # write operations use the create serializer, reads use the list serializer
        return CandidateCreateSerializer if self.request.method == "POST" else CandidateListSerializer


# ────────────────────────────────────────────────────────────────
# Retrieve / Update / Delete  →  /api/candidates/<pk>/
# ────────────────────────────────────────────────────────────────
class CandidateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/candidates/<pk>/  → retrieve
    PATCH  /api/candidates/<pk>/  → partial update
    PUT    /api/candidates/<pk>/  → update
    DELETE /api/candidates/<pk>/  → delete
    """
    queryset           = Candidate.objects.select_related("job")
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        # PUT / PATCH use write serializer; GET uses read serializer
        return (
            CandidateCreateSerializer
            if self.request.method in ("PUT", "PATCH")
            else CandidateListSerializer
        )


# ────────────────────────────────────────────────────────────────
# Summary view (kept exactly as you specified)
# ────────────────────────────────────────────────────────────────
class CandidateSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    _pill_codes = [
        "REQUIRES_ACTION",
        "PENDING_SCHEDULING",
        "BR_IN_PROCESS",
        "BR_EVALUATED",
        "INTERNAL_INTERVIEWS",
        "OFFERED",
        "HIRED",
        "REJECTED",
        "OFFER_REJECTED",
        "CANCELLED",
    ]

    def get(self, request, *args, **kwargs):
        """
        GET /api/candidates/summary/  → simple count per status
        """
        summary = (
            Candidate.objects.values("status")
            .annotate(count=Count("id"))
            .order_by()
        )
        # e.g.  [{"status": "invited", "count": 10}, ...]
        return Response(summary)
