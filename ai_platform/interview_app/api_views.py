from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.serializers import serialize
from django.core.paginator import Paginator
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from .models import InterviewSession, InterviewQuestion, CodeSubmission, WarningLog, TestCase
from django.db import models

@csrf_exempt
@require_http_methods(["GET"])
def interview_sessions_api(request):
    """API endpoint to get all interview sessions"""
    try:
        # Get query parameters
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 50)
        status_filter = request.GET.get('status', None)
        search = request.GET.get('search', None)
        
        # Base queryset
        sessions = InterviewSession.objects.all().order_by('-created_at')
        
        # Apply filters
        if status_filter and status_filter != 'all':
            sessions = sessions.filter(status=status_filter)
        
        if search:
            sessions = sessions.filter(
                candidate_name__icontains=search
            ) | sessions.filter(
                candidate_email__icontains=search
            ) | sessions.filter(
                session_key__icontains=search
            )
        
        # Pagination
        paginator = Paginator(sessions, per_page)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        sessions_data = []
        for session in page_obj:
            sessions_data.append({
                'id': str(session.id),
                'session_key': session.session_key,
                'candidate_name': session.candidate_name,
                'candidate_email': session.candidate_email,
                'job_description': session.job_description,
                'resume_text': session.resume_text,
                'status': session.status,
                'scheduled_at': session.scheduled_at.isoformat() if session.scheduled_at else None,
                'created_at': session.created_at.isoformat(),
                'is_evaluated': session.is_evaluated,
                'answers_score': session.answers_score,
                'resume_score': session.resume_score,
                'overall_performance_score': session.overall_performance_score,
                'answers_feedback': session.answers_feedback,
                'resume_feedback': session.resume_feedback,
                'overall_performance_feedback': session.overall_performance_feedback,
                'id_verification_status': session.id_verification_status,
            })
        
        response = JsonResponse({
            'success': True,
            'data': sessions_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
        
    except Exception as e:
        response = JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

@csrf_exempt
@require_http_methods(["GET"])
def interview_questions_api(request):
    """API endpoint to get all interview questions"""
    try:
        # Get query parameters
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 50)
        question_type = request.GET.get('type', None)
        search = request.GET.get('search', None)
        
        # Base queryset with session data
        questions = InterviewQuestion.objects.select_related('session').all().order_by('-session__created_at', 'order')
        
        # Apply filters
        if question_type and question_type != 'all':
            questions = questions.filter(question_type=question_type)
        
        if search:
            questions = questions.filter(
                question_text__icontains=search
            ) | questions.filter(
                session__candidate_name__icontains=search
            )
        
        # Pagination
        paginator = Paginator(questions, per_page)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        questions_data = []
        for question in page_obj:
            questions_data.append({
                'id': str(question.id),
                'session': {
                    'id': str(question.session.id),
                    'candidate_name': question.session.candidate_name,
                    'candidate_email': question.session.candidate_email,
                    'session_key': question.session.session_key,
                } if question.session else None,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'question_level': question.question_level,
                'order': question.order,
                'coding_language': question.coding_language,
                'audio_url': question.audio_url,
                'transcribed_answer': question.transcribed_answer,
                'response_time_seconds': question.response_time_seconds,
                'words_per_minute': question.words_per_minute,
                'filler_word_count': question.filler_word_count,
            })
        
        response = JsonResponse({
            'success': True,
            'data': questions_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
        
    except Exception as e:
        response = JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

@csrf_exempt
@require_http_methods(["GET"])
def code_submissions_api(request):
    """API endpoint to get all code submissions"""
    try:
        # Get query parameters
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 50)
        language = request.GET.get('language', None)
        search = request.GET.get('search', None)
        
        # Base queryset with session data
        submissions = CodeSubmission.objects.select_related('session').all().order_by('-created_at')
        
        # Apply filters
        if language and language != 'all':
            submissions = submissions.filter(language=language)
        
        if search:
            submissions = submissions.filter(
                submitted_code__icontains=search
            ) | submissions.filter(
                session__candidate_name__icontains=search
            )
        
        # Pagination
        paginator = Paginator(submissions, per_page)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        submissions_data = []
        for submission in page_obj:
            submissions_data.append({
                'id': str(submission.id),
                'session': {
                    'id': str(submission.session.id),
                    'candidate_name': submission.session.candidate_name,
                    'candidate_email': submission.session.candidate_email,
                    'session_key': submission.session.session_key,
                } if submission.session else None,
                'question_id': submission.question_id,
                'submitted_code': submission.submitted_code,
                'language': submission.language,
                'passed_all_tests': submission.passed_all_tests,
                'output_log': submission.output_log,
                'created_at': submission.created_at.isoformat(),
            })
        
        response = JsonResponse({
            'success': True,
            'data': submissions_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
        
    except Exception as e:
        response = JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

@csrf_exempt
@require_http_methods(["GET"])
def warning_logs_api(request):
    """API endpoint to get all warning logs"""
    try:
        # Get query parameters
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 50)
        warning_type = request.GET.get('type', None)
        
        # Base queryset with session data
        warnings = WarningLog.objects.select_related('session').all().order_by('-timestamp')
        
        # Apply filters
        if warning_type and warning_type != 'all':
            warnings = warnings.filter(warning_type=warning_type)
        
        # Pagination
        paginator = Paginator(warnings, per_page)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        warnings_data = []
        for warning in page_obj:
            warnings_data.append({
                'id': str(warning.id),
                'session': {
                    'id': str(warning.session.id),
                    'candidate_name': warning.session.candidate_name,
                    'candidate_email': warning.session.candidate_email,
                    'session_key': warning.session.session_key,
                } if warning.session else None,
                'warning_type': warning.warning_type,
                'timestamp': warning.timestamp.isoformat(),
            })
        
        response = JsonResponse({
            'success': True,
            'data': warnings_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
        
    except Exception as e:
        response = JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

@csrf_exempt
@require_http_methods(["GET"])
def dashboard_stats_api(request):
    """API endpoint to get dashboard statistics"""
    try:
        # Calculate statistics
        total_sessions = InterviewSession.objects.count()
        completed_sessions = InterviewSession.objects.filter(status='COMPLETED').count()
        scheduled_sessions = InterviewSession.objects.filter(status='SCHEDULED').count()
        expired_sessions = InterviewSession.objects.filter(status='EXPIRED').count()
        
        total_questions = InterviewQuestion.objects.count()
        technical_questions = InterviewQuestion.objects.filter(question_type='TECHNICAL').count()
        behavioral_questions = InterviewQuestion.objects.filter(question_type='BEHAVIORAL').count()
        coding_questions = InterviewQuestion.objects.filter(question_type='CODING').count()
        
        total_submissions = CodeSubmission.objects.count()
        passed_submissions = CodeSubmission.objects.filter(passed_all_tests=True).count()
        failed_submissions = CodeSubmission.objects.filter(passed_all_tests=False).count()
        
        total_warnings = WarningLog.objects.count()
        
        # Average scores
        avg_overall_score = InterviewSession.objects.filter(
            overall_performance_score__isnull=False
        ).aggregate(avg_score=models.Avg('overall_performance_score'))['avg_score'] or 0
        
        avg_answers_score = InterviewSession.objects.filter(
            answers_score__isnull=False
        ).aggregate(avg_score=models.Avg('answers_score'))['avg_score'] or 0
        
        avg_resume_score = InterviewSession.objects.filter(
            resume_score__isnull=False
        ).aggregate(avg_score=models.Avg('resume_score'))['avg_score'] or 0
        
        response = JsonResponse({
            'success': True,
            'data': {
                'sessions': {
                    'total': total_sessions,
                    'completed': completed_sessions,
                    'scheduled': scheduled_sessions,
                    'expired': expired_sessions,
                },
                'questions': {
                    'total': total_questions,
                    'technical': technical_questions,
                    'behavioral': behavioral_questions,
                    'coding': coding_questions,
                },
                'submissions': {
                    'total': total_submissions,
                    'passed': passed_submissions,
                    'failed': failed_submissions,
                },
                'warnings': {
                    'total': total_warnings,
                },
                'scores': {
                    'avg_overall': round(avg_overall_score, 1),
                    'avg_answers': round(avg_answers_score, 1),
                    'avg_resume': round(avg_resume_score, 1),
                }
            }
        })
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
        
    except Exception as e:
        response = JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

@csrf_exempt
@require_http_methods(["GET"])
def test_api(request):
    """Test API endpoint to verify connectivity"""
    response = JsonResponse({
        'success': True,
        'message': 'API is working!',
        'timestamp': '2025-08-26T12:00:00Z'
    })
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response
