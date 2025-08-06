# ai_platform/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from resumes.views     import ResumeViewSet, BulkResumeUploadView
from interviews.views  import InterviewViewSet, InterviewStatusSummaryView

# ──────────────────── DRF router (viewsets) ──────────────────────────────
router = DefaultRouter()
router.register(r"resumes",    ResumeViewSet,    basename="resume")
# ──────────────────── URL patterns ───────────────────────────────────────
urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # Auth (login / register / token)
    path("api/auth/", include("authapp.urls")),

    #Companies
    path('api/companies/', include('companies.urls')),

    # Jobs API
    path("api/jobs/", include("jobs.urls")),

    # Candidates API  (list / create / detail / summary)
    path("api/candidates/", include("candidates.urls")),   # ← NEW include

    # Resume bulk upload endpoint (direct import to avoid conflicts)
    path("api/resumes/bulk-upload/", BulkResumeUploadView.as_view(), name='resume-bulk-upload'),

    # All router‑based endpoints (/api/resumes/, /api/interviews/)
    path("api/", include(router.urls)),

    path("api/hiring_agency/", include("hiring_agency.urls")),

    path("api/interviews/", include("interviews.urls")),

    path("api/evaluation/", include("evaluation.urls")),

    # Notifications API
    path("api/notifications/", include("notifications.urls")),
    # Dashboard API
    path("api/dashboard/", include("dashboard.urls")),

]

# ──────────────────── Serve media in DEBUG ───────────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
