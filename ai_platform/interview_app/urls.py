from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # Existing URLs for the app
    path('invite/', views.create_interview_invite, name='create_invite'),
    path('', views.interview_portal, name='interview_portal'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('report/<uuid:session_id>/pdf/', views.download_report_pdf, name='download_report_pdf'),
    path('report/<uuid:session_id>/', views.interview_report, name='interview_report'),
    path('complete/', views.interview_complete, name='interview_complete'),

    # API Endpoints
    path('video_feed/', views.video_feed, name='video_feed'),
    path('status/', views.get_proctoring_status, name='get_proctoring_status'),
    path('report_tab_switch/', views.report_tab_switch, name='report_tab_switch'),
    path('transcribe/', views.transcribe_audio, name='transcribe_audio'),
    path('save_answer/', views.save_answer, name='save_answer'),
    path('check_camera/', views.check_camera, name='check_camera'),
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
    
    # --- NEW API ENDPOINTS FOR DATA LISTING ---
    path('api/interview-sessions/', api_views.interview_sessions_api, name='interview_sessions_api'),
    path('api/interview-questions/', api_views.interview_questions_api, name='interview_questions_api'),
    path('api/code-submissions/', api_views.code_submissions_api, name='code_submissions_api'),
    path('api/warning-logs/', api_views.warning_logs_api, name='warning_logs_api'),
    path('api/dashboard-stats/', api_views.dashboard_stats_api, name='dashboard_stats_api'),
    path('api/test/', api_views.test_api, name='test_api'),
    path('api/interview-evaluations/', api_views.get_interview_evaluations, name='get_interview_evaluations'),
    path('api/recording/<uuid:session_id>/', api_views.get_interview_recording, name='get_interview_recording'),
]