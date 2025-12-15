from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from . import views
import os

urlpatterns = [
    # Existing URLs for the app
    path('invite/', views.create_interview_invite, name='create_invite'),
    path('generate-link/', views.generate_interview_link, name='generate_interview_link'),
    # Interview portal route (specific route, not catch-all)
    path('interview/', views.interview_portal, name='interview_portal'),
    # Root path - serve React app (interview portal accessed via /interview/)
    path('', views.serve_react_app, name='react_app_root'),
    path('report/<uuid:session_id>/pdf/', views.download_report_pdf, name='download_report_pdf'),
    path('report/<uuid:session_id>/', views.interview_report, name='interview_report'),
    path('complete/', views.interview_complete, name='interview_complete'),

    # API Endpoints
    path('video_feed/', views.video_feed, name='video_feed'),
    path('video_frame/', views.video_frame, name='video_frame'),
    path('status/', views.get_proctoring_status, name='get_proctoring_status'),
    path('report_tab_switch/', views.report_tab_switch, name='report_tab_switch'),
    path('transcribe/', views.transcribe_audio, name='transcribe_audio'),
    path('check_camera/', views.check_camera, name='check_camera'),
    path('api/proctoring/event/', views.browser_proctoring_event, name='browser_proctoring_event'),
    path('activate_proctoring/', views.activate_proctoring_camera, name='activate_proctoring_camera'),
    path('end_session/', views.end_interview_session, name='end_interview_session'),
    path('release_camera/', views.release_camera, name='release_camera'),
    path('verify_id/', views.verify_id, name='verify_id'),
    path('execute_code/', views.execute_code, name='execute_code'),
    
    # --- NEW URL FOR FINAL SUBMISSION OF THE CODING CHALLENGE ---
    path('submit_coding_challenge/', views.submit_coding_challenge, name='submit_coding_challenge'),
    
    # --- NEW API ENDPOINTS FOR INTERVIEW RESULTS ---
    path('api/results/<uuid:session_id>/', views.InterviewResultsAPIView.as_view(), name='interview_results_api'),
    path('api/results/', views.InterviewResultsListAPIView.as_view(), name='interview_results_list_api'),
    path('api/analytics/<uuid:session_id>/', views.InterviewAnalyticsAPIView.as_view(), name='interview_analytics_api'),

    # --- VIDEO RECORDING ENDPOINTS ---
    path('ai/recording/upload_video/', views.upload_interview_video, name='upload_interview_video'),
    path('ai/recording/upload_audio/', views.upload_interview_audio, name='upload_interview_audio'),
    
    # Video serving endpoint with proper headers (supports both old and new folder structure)
    path('media/interview_videos/<path:video_path>', views.serve_interview_video, name='serve_interview_video'),
    path('media/interview_videos_merged/<path:video_path>', views.serve_interview_video, name='serve_interview_video_merged'),
    path('media/interview_videos_raw/<path:video_path>', views.serve_interview_video, name='serve_interview_video_raw'),

    # AI Chatbot endpoints
    path('chatbot/', views.chatbot_standalone, name='chatbot_standalone'),
    path('ai/start', views.ai_start, name='ai_start'),
    path('ai/upload_answer', views.ai_upload_answer, name='ai_upload_answer'),
    path('ai/repeat', views.ai_repeat, name='ai_repeat'),
    path('ai/transcript_pdf', views.ai_transcript_pdf, name='ai_transcript_pdf'),


    # Auth endpoints namespace
    path('api/auth/', include('authapp.urls')),

    # Include app APIs under /api/*
    path('api/jobs/', include('jobs.urls')),
    path('api/candidates/', include('candidates.urls')),
    path('api/companies/', include('companies.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/interviews/', include('interviews.urls')),
    path('api/evaluation/', include('evaluation.urls')),  # Evaluation CRUD endpoints
    path('api/requests/', include('candidates.urls')),  # Requests endpoints (pending, etc.)
]

# Serve frontend static assets (CSS, JS, images from Vite build)
# Vite builds assets to /assets/ directory
def serve_frontend_assets(request, path=None):
    """Serve frontend static assets from static_frontend_dist/assets/"""
    from django.http import FileResponse, Http404
    import os
    
    # Handle root-level assets (favicons, etc.) - path might be the filename
    if path is None or '/' not in path:
        # This is likely a root-level asset request
        asset_name = path or request.path.lstrip('/')
        root_assets = [
            os.path.join(settings.BASE_DIR, 'static_frontend_dist', asset_name),
            os.path.join(settings.BASE_DIR, 'frontend', 'dist', asset_name),
        ]
        
        for file_path in root_assets:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(open(file_path, 'rb'), content_type=get_content_type(file_path))
    
    # Try multiple possible locations for /assets/ path
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'static_frontend_dist', 'assets', path),
        os.path.join(settings.BASE_DIR, 'frontend', 'dist', 'assets', path),
    ]
    
    for file_path in possible_paths:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(open(file_path, 'rb'), content_type=get_content_type(file_path))
    
    # Also check root level assets (favicons, etc.)
    root_assets = [
        os.path.join(settings.BASE_DIR, 'static_frontend_dist', path),
        os.path.join(settings.BASE_DIR, 'frontend', 'dist', path),
    ]
    
    for file_path in root_assets:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(open(file_path, 'rb'), content_type=get_content_type(file_path))
    
    raise Http404("Asset not found")

def get_content_type(file_path):
    """Determine content type based on file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    content_types = {
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.jsx': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.eot': 'application/vnd.ms-fontobject',
    }
    return content_types.get(ext, 'application/octet-stream')

# Serve frontend assets before catch-all
urlpatterns += [
    path('assets/<path:path>', serve_frontend_assets, name='serve_frontend_assets'),
    # Serve root-level asset files (favicons, logos, etc.)
    re_path(r'^([^/]+\.(png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot))$', 
            lambda request, *args: serve_frontend_assets(request, args[0] if args else request.path.lstrip('/')), 
            name='serve_root_assets'),
]

# Catch-all route for React SPA (must be added after all other routes)
# This serves the React app for all frontend routes like /login, /dashboard, etc.
# Excludes API routes, media files, static files, assets, and other backend routes
urlpatterns += [
    re_path(r'^(?!api/|media/|static/|assets/|admin/|invite/|generate-link/|report/|complete/|video_feed/|video_frame/|status/|transcribe/|check_camera/|activate_proctoring/|end_session/|release_camera/|verify_id/|execute_code/|submit_coding_challenge/|ai/|chatbot/|interview/).*$', views.serve_react_app, name='react_app'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files from frontend dist folder
    urlpatterns += static('/static/', document_root=os.path.join(settings.BASE_DIR, 'frontend', 'dist'))