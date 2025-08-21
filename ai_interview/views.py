# ai_interview/views.py
import os
import json
import logging
import base64
import cv2
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import re

from .models import AIInterviewSession, AIInterviewQuestion, AIInterviewResponse, AIInterviewResult
from .serializers import (
    AIInterviewSessionSerializer, AIInterviewQuestionSerializer,
    AIInterviewResponseSerializer, AIInterviewResultSerializer
)
from .services import ai_interview_service
from interviews.models import Interview

# Import existing AI model components (temporarily disabled for testing)
# from ai_platform.interview_app.camera import VideoCamera
# from ai_platform.interview_app.yolo_face_detector import detect_face_with_yolo

logger = logging.getLogger(__name__)

# Global camera instances
CAMERAS = {}
import threading
camera_lock = threading.Lock()

def get_camera_for_session(session_id):
    """Get or create camera instance for session"""
    # Temporarily disabled for testing
    logger.info(f"Camera functionality temporarily disabled for session {session_id}")
    return None

def release_camera_for_session(session_id):
    """Release camera instance for session"""
    # Temporarily disabled for testing
    logger.info(f"Camera release functionality temporarily disabled for session {session_id}")
    pass

def validate_interview_token(interview_id, link_token):
    """Validate interview link token"""
    try:
        # Decode the link token
        decoded_token = base64.urlsafe_b64decode(link_token.encode('utf-8')).decode('utf-8')
        token_interview_id, signature = decoded_token.split(':', 1)
        
        # Verify interview ID matches
        if str(interview_id) != token_interview_id:
            return False, "Invalid interview token"
        
        # Get the interview and validate
        interview = Interview.objects.get(id=interview_id)
        is_valid, message = interview.validate_interview_link(link_token)
        
        return is_valid, message
    except Exception as e:
        logger.error(f"Error validating interview token: {e}")
        return False, "Invalid interview token"

class GenerateAIInterviewLinkView(APIView):
    """Generate a secure AI interview link for candidates"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, interview_id):
        """Generate a secure AI interview link"""
        try:
            # Get the interview
            interview = get_object_or_404(Interview, id=interview_id)
            
            # Check if interview is ready for AI interview
            if not interview.started_at:
                return Response({
                    'error': 'Interview must have a scheduled start time to generate AI interview link'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if interview is for AI interview type
            if not interview.ai_interview_type:
                return Response({
                    'error': 'Interview must be configured for AI interview to generate AI interview link'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate the interview link using the existing method
            link_token = interview.generate_interview_link()
            
            if not link_token:
                return Response({
                    'error': 'Failed to generate interview link'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Create AI interview session if it doesn't exist
            ai_session, created = AIInterviewSession.objects.get_or_create(
                interview=interview,
                defaults={
                    'status': 'ACTIVE',
                    'ai_configuration': {
                        'language_code': 'en',
                        'accent_tld': 'com',
                        'candidate_name': interview.candidate.full_name,
                        'candidate_email': interview.candidate.email,
                        'job_title': interview.job.job_title if interview.job else '',
                        'job_description': interview.job.description if interview.job else '',
                        'resume_text': getattr(interview.candidate, 'resume_text', '') or '',
                    }
                }
            )
            
            # Generate questions for the AI session if it's newly created
            if created:
                try:
                    questions = ai_interview_service.generate_questions(ai_session)
                    logger.info(f"Generated {len(questions)} questions for AI session {ai_session.id}")
                except Exception as e:
                    logger.error(f"Error generating questions: {e}")
                    # Create a default question if AI service fails
                    AIInterviewQuestion.objects.create(
                        session=ai_session,
                        question_text="Tell me about yourself and your experience.",
                        question_type="behavioral",
                        question_index=1
                    )
            
            # Build the AI interview URL
            base_url = request.build_absolute_uri('/').rstrip('/')
            ai_interview_url = f"{base_url}/api/ai-interview/public/start/"
            
            return Response({
                'interview_id': str(interview.id),
                'link_token': link_token,
                'ai_interview_url': ai_interview_url,
                'public_interview_url': f"{base_url}/api/interviews/public/{link_token}/",
                'expires_at': interview.link_expires_at.isoformat() if interview.link_expires_at else None,
                'ai_session_id': str(ai_session.id),
                'ai_interview_type': interview.ai_interview_type,
                'candidate_name': interview.candidate.full_name,
                'candidate_email': interview.candidate.email,
                'job_title': interview.job.job_title if interview.job else 'Technical Role',
                'message': 'AI interview link generated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error generating AI interview link: {e}")
            return Response({
                'error': f'Failed to generate AI interview link: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetAIInterviewLinkView(APIView):
    """Get existing AI interview link for an interview"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, interview_id):
        """Get the existing AI interview link"""
        try:
            # Get the interview
            interview = get_object_or_404(Interview, id=interview_id)
            
            if not interview.interview_link:
                return Response({
                    'error': 'No interview link found for this interview'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if AI session exists
            try:
                ai_session = AIInterviewSession.objects.get(interview=interview)
                ai_session_id = str(ai_session.id)
                questions_count = AIInterviewQuestion.objects.filter(session=ai_session).count()
            except AIInterviewSession.DoesNotExist:
                ai_session_id = None
                questions_count = 0
            
            # Build URLs
            base_url = request.build_absolute_uri('/').rstrip('/')
            ai_interview_url = f"{base_url}/api/ai-interview/public/start/"
            
            return Response({
                'interview_id': str(interview.id),
                'link_token': interview.interview_link,
                'ai_interview_url': ai_interview_url,
                'public_interview_url': f"{base_url}/api/interviews/public/{interview.interview_link}/",
                'expires_at': interview.link_expires_at.isoformat() if interview.link_expires_at else None,
                'ai_session_id': ai_session_id,
                'ai_interview_type': interview.ai_interview_type,
                'candidate_name': interview.candidate.full_name,
                'candidate_email': interview.candidate.email,
                'job_title': interview.job.job_title if interview.job else 'Technical Role',
                'questions_generated': questions_count,
                'is_expired': interview.link_expires_at and timezone.now() > interview.link_expires_at,
                'message': 'AI interview link retrieved successfully'
            })
            
        except Exception as e:
            logger.error(f"Error getting AI interview link: {e}")
            return Response({
                'error': f'Failed to get AI interview link: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RegenerateAIInterviewLinkView(APIView):
    """Regenerate a new AI interview link (invalidates old one)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, interview_id):
        """Regenerate a new AI interview link"""
        try:
            # Get the interview
            interview = get_object_or_404(Interview, id=interview_id)
            
            # Check if interview is ready for AI interview
            if not interview.started_at:
                return Response({
                    'error': 'Interview must have a scheduled start time to regenerate AI interview link'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Clear existing link
            interview.interview_link = None
            interview.link_expires_at = None
            interview.save()
            
            # Generate new link
            link_token = interview.generate_interview_link()
            
            if not link_token:
                return Response({
                    'error': 'Failed to regenerate interview link'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Update or create AI session
            ai_session, created = AIInterviewSession.objects.get_or_create(
                interview=interview,
                defaults={
                    'status': 'ACTIVE',
                    'ai_configuration': {
                        'language_code': 'en',
                        'accent_tld': 'com',
                        'candidate_name': interview.candidate.full_name,
                        'candidate_email': interview.candidate.email,
                        'job_title': interview.job.job_title if interview.job else '',
                        'job_description': interview.job.description if interview.job else '',
                        'resume_text': getattr(interview.candidate, 'resume_text', '') or '',
                    }
                }
            )
            
            # Regenerate questions if session already existed
            if not created:
                # Clear existing questions
                AIInterviewQuestion.objects.filter(session=ai_session).delete()
                
                # Generate new questions
                try:
                    questions = ai_interview_service.generate_questions(ai_session)
                    logger.info(f"Regenerated {len(questions)} questions for AI session {ai_session.id}")
                except Exception as e:
                    logger.error(f"Error regenerating questions: {e}")
                    # Create a default question if AI service fails
                    AIInterviewQuestion.objects.create(
                        session=ai_session,
                        question_text="Tell me about yourself and your experience.",
                        question_type="behavioral",
                        question_index=1
                    )
            
            # Build URLs
            base_url = request.build_absolute_uri('/').rstrip('/')
            ai_interview_url = f"{base_url}/api/ai-interview/public/start/"
            
            return Response({
                'interview_id': str(interview.id),
                'link_token': link_token,
                'ai_interview_url': ai_interview_url,
                'public_interview_url': f"{base_url}/api/interviews/public/{link_token}/",
                'expires_at': interview.link_expires_at.isoformat() if interview.link_expires_at else None,
                'ai_session_id': str(ai_session.id),
                'ai_interview_type': interview.ai_interview_type,
                'candidate_name': interview.candidate.full_name,
                'candidate_email': interview.candidate.email,
                'job_title': interview.job.job_title if interview.job else 'Technical Role',
                'message': 'AI interview link regenerated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error regenerating AI interview link: {e}")
            return Response({
                'error': f'Failed to regenerate AI interview link: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PublicStartInterviewView(APIView):
    """Public endpoint to start an AI interview session using link token"""
    permission_classes = []  # No authentication required
    
    def post(self, request):
        """Start the interview session using interview link token"""
        try:
            interview_id = request.data.get('interview_id')
            link_token = request.data.get('link_token')
            
            if not interview_id or not link_token:
                return Response({
                    'error': 'Interview ID and link token are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate the interview token
            is_valid, message = validate_interview_token(interview_id, link_token)
            if not is_valid:
                return Response({
                    'error': message
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get the interview
            interview = get_object_or_404(Interview, id=interview_id)
            
            # Check if interview can be started
            now = timezone.now()
            if interview.started_at and now < interview.started_at:
                return Response({
                    'error': f'Interview starts at {interview.started_at.strftime("%I:%M %p")}. Please wait.',
                    'status': 'not_started'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create AI interview session
            session, created = AIInterviewSession.objects.get_or_create(
                interview=interview,
                defaults={
                    'status': 'ACTIVE',
                    'ai_configuration': {
                        'language_code': 'en',
                        'accent_tld': 'com',
                        'candidate_name': interview.candidate.full_name,
                        'candidate_email': interview.candidate.email,
                        'job_title': interview.job.job_title if interview.job else '',
                        'job_description': interview.job.description if interview.job else '',
                        'resume_text': getattr(interview.candidate, 'resume_text', '') or '',
                    }
                }
            )
            
            if created:
                # Generate questions for new session using the actual AI model
                try:
                    questions = ai_interview_service.generate_questions(session)
                    logger.info(f"Generated {len(questions)} questions for session {session.id}")
                except Exception as e:
                    logger.error(f"Error generating questions: {e}")
                    # Create a default question if AI service fails
                    AIInterviewQuestion.objects.create(
                        session=session,
                        question_text="Tell me about yourself and your experience.",
                        question_type="behavioral",
                        question_index=1
                    )
            
            # Get questions for the session
            questions = AIInterviewQuestion.objects.filter(session=session).order_by('question_index')
            
            # Prepare question data
            questions_data = []
            for question in questions:
                questions_data.append({
                    'id': str(question.id),
                    'text': question.question_text,
                    'type': question.question_type,
                    'order': question.question_index,
                    'audio_url': getattr(question, 'audio_url', None)
                })
            
            # Get first question for immediate display
            current_question = questions_data[0] if questions_data else None
            
            return Response({
                'session_id': str(session.id),
                'interview_id': str(interview.id),
                'candidate_name': interview.candidate.full_name,
                'job_title': interview.job.job_title if interview.job else 'Technical Role',
                'ai_interview_type': interview.ai_interview_type or 'technical',
                'current_question': current_question['text'] if current_question else "Welcome to your AI interview! Let's begin.",
                'questions': questions_data,
                'total_questions': len(questions_data),
                'status': 'started',
                'message': 'Interview started successfully'
            })
            
        except Exception as e:
            logger.error(f"Error starting public interview: {e}")
            return Response({
                'error': f'Failed to start interview: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PublicSubmitResponseView(APIView):
    """Public endpoint to submit a response using link token"""
    permission_classes = []  # No authentication required
    
    def post(self, request):
        """Submit response using interview link token"""
        try:
            session_id = request.data.get('session_id')
            link_token = request.data.get('link_token')
            response_text = request.data.get('response_text', '')
            response_audio = request.data.get('response_audio')
            
            if not session_id or not link_token:
                return Response({
                    'error': 'Session ID and link token are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the session
            session = get_object_or_404(AIInterviewSession, id=session_id)
            
            # Validate the interview token
            is_valid, message = validate_interview_token(str(session.interview.id), link_token)
            if not is_valid:
                return Response({
                    'error': message
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get current question
            current_question = AIInterviewQuestion.objects.filter(session=session).order_by('question_index').first()
            if not current_question:
                return Response({
                    'error': 'No questions available for this session'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create response
            response = AIInterviewResponse.objects.create(
                session=session,
                question=current_question,
                response_text=response_text,
                response_audio=response_audio,
                response_time=timezone.now()
            )
            
            # Get next question
            next_question = AIInterviewQuestion.objects.filter(
                session=session, 
                question_index__gt=current_question.question_index
            ).order_by('question_index').first()
            
            # Generate AI feedback using the actual AI model
            try:
                import google.generativeai as genai
                gemini_api_key = "AIzaSyBXhqoQx3maTEJNdGH6xo3ULX1wL1LFPOc"
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                
                # Create a context-aware prompt for feedback
                feedback_prompt = f"""
                You are an expert AI interviewer. The candidate just answered the following question:
                
                Question: {current_question.question_text}
                Answer: {response_text}
                
                Please provide:
                1. A brief, encouraging feedback (1-2 sentences)
                2. A follow-up question or next step
                
                Keep your response conversational and helpful. Format as:
                Feedback: [your feedback here]
                Next: [next question or instruction]
                """
                
                ai_response = model.generate_content(feedback_prompt)
                feedback_text = ai_response.text
                
                # Parse the response
                feedback_match = re.search(r"Feedback:\s*(.*?)(?=\nNext:|$)", feedback_text, re.DOTALL)
                next_match = re.search(r"Next:\s*(.*?)(?=\n|$)", feedback_text, re.DOTALL)
                
                feedback = feedback_match.group(1).strip() if feedback_match else "Thank you for your response."
                next_instruction = next_match.group(1).strip() if next_match else None
                
            except Exception as e:
                logger.error(f"Error generating AI feedback: {e}")
                feedback = f"Thank you for your response. {response_text[:50]}..."
                next_instruction = None
            
            return Response({
                'response_id': str(response.id),
                'current_question_id': str(current_question.id),
                'next_question': next_question.question_text if next_question else None,
                'feedback': feedback,
                'next_instruction': next_instruction,
                'message': 'Response submitted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error submitting public response: {e}")
            return Response({
                'error': f'Failed to submit response: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PublicCompleteInterviewView(APIView):
    """Public endpoint to complete interview using link token"""
    permission_classes = []  # No authentication required
    
    def post(self, request):
        """Complete interview using interview link token"""
        try:
            session_id = request.data.get('session_id')
            link_token = request.data.get('link_token')
            
            if not session_id or not link_token:
                return Response({
                    'error': 'Session ID and link token are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the session
            session = get_object_or_404(AIInterviewSession, id=session_id)
            
            # Validate the interview token
            is_valid, message = validate_interview_token(str(session.interview.id), link_token)
            if not is_valid:
                return Response({
                    'error': message
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if session.status == 'COMPLETED':
                return Response({
                    'error': 'Session already completed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark session as completed
            session.status = 'COMPLETED'
            session.completed_at = timezone.now()
            session.save()
            
            # Generate AI evaluation using the actual AI model
            try:
                import google.generativeai as genai
                gemini_api_key = "AIzaSyBXhqoQx3maTEJNdGH6xo3ULX1wL1LFPOc"
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                
                # Get all responses for evaluation
                responses = AIInterviewResponse.objects.filter(session=session).select_related('question')
                total_responses = responses.count()
                total_questions = AIInterviewQuestion.objects.filter(session=session).count()
                
                # Create evaluation prompt
                qa_text = ""
                for response in responses:
                    qa_text += f"Question: {response.question.question_text}\nAnswer: {response.response_text}\n\n"
                
                evaluation_prompt = f"""
                You are an expert AI interviewer evaluating a candidate's performance. 
                
                Job: {session.interview.job.job_title if session.interview.job else 'Technical Role'}
                Candidate: {session.interview.candidate.full_name}
                Questions Answered: {total_responses}/{total_questions}
                
                Questions and Answers:
                {qa_text}
                
                Please provide:
                1. An overall score from 0-100
                2. A detailed evaluation of their performance
                3. Key strengths and areas for improvement
                4. A recommendation (Strong Yes, Yes, Maybe, No)
                
                Format your response as:
                Score: [0-100]
                Evaluation: [detailed evaluation]
                Strengths: [key strengths]
                Areas for Improvement: [areas to improve]
                Recommendation: [Strong Yes/Yes/Maybe/No]
                """
                
                ai_response = model.generate_content(evaluation_prompt)
                evaluation_text = ai_response.text
                
                # Parse the response
                score_match = re.search(r"Score:\s*(\d+)", evaluation_text)
                evaluation_match = re.search(r"Evaluation:\s*(.*?)(?=\nStrengths:|$)", evaluation_text, re.DOTALL)
                strengths_match = re.search(r"Strengths:\s*(.*?)(?=\nAreas for Improvement:|$)", evaluation_text, re.DOTALL)
                improvement_match = re.search(r"Areas for Improvement:\s*(.*?)(?=\nRecommendation:|$)", evaluation_text, re.DOTALL)
                recommendation_match = re.search(r"Recommendation:\s*(.*?)(?=\n|$)", evaluation_text, re.DOTALL)
                
                score = int(score_match.group(1)) if score_match else min(100, int((total_responses / max(total_questions, 1)) * 100))
                evaluation = evaluation_match.group(1).strip() if evaluation_match else f"Interview completed successfully. You answered {total_responses} out of {total_questions} questions."
                strengths = strengths_match.group(1).strip() if strengths_match else "Good participation in the interview."
                areas_for_improvement = improvement_match.group(1).strip() if improvement_match else "Continue developing your skills."
                recommendation = recommendation_match.group(1).strip() if recommendation_match else "Yes"
                
            except Exception as e:
                logger.error(f"Error generating AI evaluation: {e}")
                total_responses = AIInterviewResponse.objects.filter(session=session).count()
                total_questions = AIInterviewQuestion.objects.filter(session=session).count()
                evaluation = f"Interview completed successfully. You answered {total_responses} out of {total_questions} questions."
                score = min(100, int((total_responses / max(total_questions, 1)) * 100))
                strengths = "Good participation in the interview."
                areas_for_improvement = "Continue developing your skills."
                recommendation = "Yes"
            
            return Response({
                'session_id': str(session.id),
                'evaluation': evaluation,
                'score': score,
                'total_questions': total_questions,
                'answered_questions': total_responses,
                'strengths': strengths,
                'areas_for_improvement': areas_for_improvement,
                'recommendation': recommendation,
                'status': 'completed',
                'message': 'Interview completed successfully'
            })
            
        except Exception as e:
            logger.error(f"Error completing public interview: {e}")
            return Response({
                'error': f'Failed to complete interview: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AIInterviewSessionViewSet(generics.ListCreateAPIView):
    """ViewSet for AI Interview Sessions"""
    queryset = AIInterviewSession.objects.all()
    serializer_class = AIInterviewSessionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Create a new AI interview session"""
        try:
            interview_id = request.data.get('interview_id')
            interview = get_object_or_404(Interview, id=interview_id)
            
            # Create AI configuration
            ai_configuration = {
                'language_code': 'en',
                'accent_tld': 'com',
                'candidate_name': interview.candidate.full_name,
                'candidate_email': interview.candidate.email,
                'job_title': interview.job.job_title if interview.job else '',
                'job_description': interview.job.description if interview.job else '',
                'resume_text': getattr(interview.candidate, 'resume_text', '') or '',
            }
            
            # Create session using service
            session = ai_interview_service.create_session(interview, ai_configuration)
            
            # Generate questions
            questions = ai_interview_service.generate_questions(session)
            
            serializer = self.get_serializer(session)
            return Response({
                'session': serializer.data,
                'questions_count': len(questions),
                'message': 'AI interview session created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating AI interview session: {e}")
            return Response({
                'error': f'Failed to create AI interview session: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StartInterviewView(APIView):
    """Start an AI interview session"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        """Start the interview session"""
        try:
            session = get_object_or_404(AIInterviewSession, id=session_id)
            
            if session.status != 'ACTIVE':
                return Response({
                    'error': 'Session is not active'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get questions for the session
            questions = AIInterviewQuestion.objects.filter(session=session).order_by('question_index')
            
            # Prepare question data
            questions_data = []
            for question in questions:
                questions_data.append({
                    'id': str(question.id),
                    'text': question.question_text,
                    'type': question.question_type,
                    'order': question.question_index,
                    'audio_url': getattr(question, 'audio_url', None)
                })
            
            return Response({
                'session_id': str(session.id),
                'candidate_name': session.ai_configuration.get('candidate_name', 'Candidate'),
                'job_title': session.ai_configuration.get('job_title', 'Technical Role'),
                'questions': questions_data,
                'total_questions': len(questions_data),
                'status': 'started'
            })
            
        except Exception as e:
            logger.error(f"Error starting interview: {e}")
            return Response({
                'error': f'Failed to start interview: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SubmitResponseView(APIView):
    """Submit a response to an interview question"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id, question_id):
        """Submit audio response and get transcription"""
        try:
            session = get_object_or_404(AIInterviewSession, id=session_id)
            question = get_object_or_404(AIInterviewQuestion, id=question_id, session=session)
            
            if 'audio_data' not in request.FILES:
                return Response({
                    'error': 'Audio file is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            audio_file = request.FILES['audio_data']
            
            # Transcribe response using service
            response = ai_interview_service.transcribe_response(
                audio_file=audio_file,
                session_id=session_id,
                question_id=question_id
            )
            
            return Response({
                'response_id': str(response.id),
                'transcribed_text': response.transcribed_text,
                'filler_word_count': response.filler_word_count,
                'sentiment_score': response.sentiment_score,
                'response_time': response.response_time.isoformat(),
                'message': 'Response submitted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error submitting response: {e}")
            return Response({
                'error': f'Failed to submit response: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CompleteInterviewView(APIView):
    """Complete an AI interview session"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        """Complete the interview and generate evaluation"""
        try:
            session = get_object_or_404(AIInterviewSession, id=session_id)
            
            if session.status == 'COMPLETED':
                return Response({
                    'error': 'Session already completed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Evaluate session using service
            result = ai_interview_service.evaluate_session(session)
            
            # Get session summary
            summary = ai_interview_service.get_session_summary(session)
            
            return Response({
                'session_id': str(session.id),
                'status': 'completed',
                'evaluation': {
                    'resume_score': result.resume_score,
                    'answers_score': result.answers_score,
                    'overall_score': result.overall_score,
                    'resume_feedback': result.resume_feedback,
                    'answers_feedback': result.answers_feedback
                },
                'summary': summary,
                'message': 'Interview completed and evaluated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error completing interview: {e}")
            return Response({
                'error': f'Failed to complete interview: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Proctoring endpoints (integrated from existing AI model)
@csrf_exempt
def video_feed(request):
    """Video feed for proctoring"""
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({"error": "Session ID required"}, status=400)
    
    camera = get_camera_for_session(session_id)
    if not camera:
        return JsonResponse({"error": "Camera not found"}, status=404)
    
    def generate_frames():
        while True:
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    
    return StreamingHttpResponse(
        generate_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

@csrf_exempt
def get_proctoring_status(request):
    """Get proctoring status and warnings"""
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({}, status=400)
    
    camera = get_camera_for_session(session_id)
    if not camera:
        return JsonResponse({}, status=404)
    
    return JsonResponse(camera.get_latest_warnings())

@csrf_exempt
@require_POST
def report_tab_switch(request):
    """Report tab switch events"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        status = data.get('status')
        
        if not session_id:
            return JsonResponse({"error": "Session ID required"}, status=400)
        
        camera = get_camera_for_session(session_id)
        if not camera:
            return JsonResponse({"error": "Camera not found"}, status=404)
        
        camera.set_tab_switch_status(status == 'hidden')
        return JsonResponse({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error reporting tab switch: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def check_camera(request):
    """Check if camera is available"""
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({"error": "Session ID required"}, status=400)
    
    camera = get_camera_for_session(session_id)
    if camera and camera.video.isOpened():
        return JsonResponse({"status": "ok"})
    else:
        release_camera_for_session(session_id)
        return JsonResponse({
            "error": "Camera not available"
        }, status=500)

@csrf_exempt
@require_POST
def release_camera(request):
    """Release camera resources"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({"error": "Session ID required"}, status=400)
        
        release_camera_for_session(session_id)
        return JsonResponse({"status": "success"})
        
    except Exception as e:
        logger.error(f"Error releasing camera: {e}")
        return JsonResponse({"error": str(e)}, status=500)

# ID Verification endpoint (integrated from existing AI model)
@csrf_exempt
@require_POST
def verify_id(request):
    """Verify candidate ID using AI"""
    try:
        image_data = request.POST.get('image_data')
        session_id = request.POST.get('session_id')
        
        if not all([image_data, session_id]):
            return JsonResponse({
                'error': 'Missing required data'
            }, status=400)
        
        session = get_object_or_404(AIInterviewSession, id=session_id)
        
        # Decode base64 image
        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1]
        img_file = ContentFile(
            base64.b64decode(imgstr), 
            name=f"id_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        )
        
        # Save image temporarily
        tmp_path = f"/tmp/id_verification_{session_id}.{ext}"
        with open(tmp_path, 'wb') as f:
            f.write(img_file.read())
        
        try:
            # Read image with OpenCV
            full_image = cv2.imread(tmp_path)
            if full_image is None:
                return JsonResponse({
                    'error': 'Invalid image format'
                }, status=400)
            
            # Detect faces using YOLO
            results = detect_face_with_yolo(full_image)
            boxes = results[0].boxes if results and hasattr(results[0], 'boxes') else []
            num_faces_detected = len(boxes)
            
            if num_faces_detected != 2:
                if num_faces_detected < 2:
                    message = f"Verification failed. Only {num_faces_detected} face(s) detected. Please ensure both your live face and the face on your ID card are clearly visible."
                else:
                    message = f"Verification failed. {num_faces_detected} faces detected. Please ensure only you and your ID card are in the frame."
                return JsonResponse({'error': message}, status=400)
            
            # Use Gemini for OCR
            import google.generativeai as genai
            gemini_api_key = "AIzaSyBXhqoQx3maTEJNdGH6xo3ULX1wL1LFPOc"
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            with open(tmp_path, 'rb') as f:
                image_bytes = f.read()
            
            id_card_for_ocr = {'mime_type': 'image/jpeg', 'data': image_bytes}
            prompt = ("You are an OCR expert. Extract the following from the provided image of an ID card: "
                      "- Full Name\n- ID Number\n"
                      "If a value cannot be extracted, state 'Not Found'. Do not add any warnings.\n"
                      "Format:\nName: <value>\nID Number: <value>")
            
            response = model.generate_content([prompt, id_card_for_ocr])
            text = response.text
            
            # Parse extracted data
            name_match = re.search(r"Name:\s*(.+)", text, re.IGNORECASE)
            id_number_match = re.search(r"ID Number:\s*(.+)", text, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else None
            id_number = id_number_match.group(1).strip() if id_number_match else None
            
            # Validate extracted data
            invalid_phrases = ['not found', 'cannot be', 'unreadable', 'blurry', 'unavailable', 'missing']
            name_verified = name and len(name.strip()) > 2 and not any(phrase in name.lower() for phrase in invalid_phrases)
            
            if not name_verified:
                return JsonResponse({
                    'error': f"Could not reliably read the name from the ID card. Extracted: '{name}'. Please try again."
                }, status=400)
            
            # Check name match
            candidate_name = session.ai_configuration.get('candidate_name', '')
            if candidate_name.lower().split()[0] not in name.lower():
                return JsonResponse({
                    'error': f"Name on ID ('{name}') does not match the registered name ('{candidate_name}')."
                }, status=400)
            
            # Update session
            session.id_verification_status = 'Verified'
            session.extracted_id_details = f"Name: {name}, ID: {id_number}"
            session.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Verification successful!'
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        logger.error(f"Error in ID verification: {e}")
        return JsonResponse({
            'error': f'An unexpected error occurred: {str(e)}'
        }, status=500)

# API Views for session management
class AIInterviewSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Detail view for AI Interview Sessions"""
    queryset = AIInterviewSession.objects.all()
    serializer_class = AIInterviewSessionSerializer
    permission_classes = [IsAuthenticated]

class AIInterviewQuestionListView(generics.ListAPIView):
    """List questions for an AI interview session"""
    serializer_class = AIInterviewQuestionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        session_id = self.kwargs.get('session_id')
        return AIInterviewQuestion.objects.filter(session_id=session_id).order_by('question_index')

class AIInterviewResponseListView(generics.ListAPIView):
    """List responses for an AI interview session"""
    serializer_class = AIInterviewResponseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        session_id = self.kwargs.get('session_id')
        return AIInterviewResponse.objects.filter(session_id=session_id).order_by('response_time')

class AIInterviewResultDetailView(generics.RetrieveAPIView):
    """Detail view for AI Interview Results"""
    queryset = AIInterviewResult.objects.all()
    serializer_class = AIInterviewResultSerializer
    permission_classes = [IsAuthenticated]
