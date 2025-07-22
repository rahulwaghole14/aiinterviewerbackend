# interviews/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    InterviewViewSet,
    InterviewStatusSummaryView,   # summary view
)

# ─── DRF router for CRUD endpoints ───────────────────────────
router = DefaultRouter()
router.register(r"", InterviewViewSet, basename="interview")

# ─── URL patterns ────────────────────────────────────────────
urlpatterns = [
    # Summary must come first (otherwise the router would treat
    # "summary/" as a primary‑key and return 404)
    path("summary/", InterviewStatusSummaryView.as_view(), name="interview-summary"),

    # All standard CRUD routes:
    #   /api/interviews/           → list / create
    #   /api/interviews/<pk>/      → retrieve / update / delete
    path("", include(router.urls)),
]
