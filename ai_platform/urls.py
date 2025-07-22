# ai_platform/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from resumes.views     import ResumeViewSet
from interviews.views  import InterviewViewSet, InterviewStatusSummaryView

# ──────────────────── DRF router (viewsets) ──────────────────────────────
router = DefaultRouter()
router.register(r"resumes",    ResumeViewSet,    basename="resume")
router.register(r"interviews", InterviewViewSet, basename="interview")

# ──────────────────── URL patterns ───────────────────────────────────────
urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # Auth (login / register / token)
    path("auth/", include("users.urls")),

    # Jobs API
    path("api/jobs/", include("jobs.urls")),

    # Candidates API  (list / create / detail / summary)
    path("api/candidates/", include("candidates.urls")),   # ← NEW include

    # Interview status summary   (/api/interviews/summary/)
    path(
        "api/interviews/summary/",
        InterviewStatusSummaryView.as_view(),
        name="interview-summary",
    ),

    # All router‑based endpoints (/api/resumes/, /api/interviews/)
    path("api/", include(router.urls)),

    path("hiring_agency/", include("hiring_agency.urls")),
]

# ──────────────────── Serve media in DEBUG ───────────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
