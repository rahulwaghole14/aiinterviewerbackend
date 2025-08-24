from django.urls import path
from . import views

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
    path('check_camera/', views.check_camera, name='check_camera'),
    path('end_session/', views.end_interview_session, name='end_interview_session'),
    path('release_camera/', views.release_camera, name='release_camera'),
    path('verify_id/', views.verify_id, name='verify_id'),
    path('execute_code/', views.execute_code, name='execute_code'),
    
    # --- NEW URL FOR FINAL SUBMISSION OF THE CODING CHALLENGE ---
    path('submit_coding_challenge/', views.submit_coding_challenge, name='submit_coding_challenge'),
]