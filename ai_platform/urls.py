from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from resumes.views import ResumeViewSet
from candidates.views import CandidateListCreateView

router = DefaultRouter()
router.register(r'resumes', ResumeViewSet, basename='resume')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('jobs/', include('jobs.urls')),
    path('api/', include(router.urls)),
    path('api/candidates/', CandidateListCreateView.as_view(), name='candidates'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
