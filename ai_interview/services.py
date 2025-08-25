# ai_interview/services.py
import os
import json
import logging
import google.generativeai as genai
import whisper
import gtts
from gtts import gTTS
from pathlib import Path
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
from textblob import TextBlob
import re
import traceback

from .models import AIInterviewSession, AIInterviewQuestion, AIInterviewResponse, AIInterviewResult

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure Gemini AI
gemini_api_key = "AIzaSyBXhqoQx3maTEJNdGH6xo3ULX1wL1LFPOc"
genai.configure(api_key=gemini_api_key)

# Load Whisper model
try:
    whisper_model = whisper.load_model("small")
    print("Whisper model 'small' loaded for AI interview service.")
except Exception as e:
    print(f"Error loading Whisper model: {e}")
    whisper_model = None

# Constants
FILLER_WORDS = ['um', 'uh', 'er', 'ah', 'like', 'okay', 'right', 'so', 'you know', 'i mean', 'basically', 'actually', 'literally']
SUPPORTED_LANGUAGES = {'en': 'English'}

class AIInterviewService:
    """
    Service class for handling AI interview operations using the existing AI model
    """
    
    @staticmethod
    def create_session(interview, ai_configuration):
        """
        Create a new AI interview session
        """
        try:
            session = AIInterviewSession.objects.create(
                interview=interview,
                status='ACTIVE',
                model_name='gemini-1.5-flash-latest',
                model_version='1.0',
                ai_configuration=ai_configuration,
                session_started_at=timezone.now()
            )
            
            logger.info(f"Created AI interview session {session.id} for interview {interview.id}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating AI interview session: {e}")
            raise
    
    @staticmethod
    def generate_questions(session):
        """
        Generate interview questions using the existing AI model logic
        """
        try:
            # Get configuration from session
            config = session.ai_configuration
            language_code = config.get('language_code', 'en')
            candidate_name = config.get('candidate_name', 'Candidate')
            job_description = config.get('job_description', '')
            resume_text = config.get('resume_text', '')
            
            # Use the existing AI model logic from interview_app
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            # Generate resume summary
            summary_prompt = f"Summarize key skills from the following resume:\n\n{resume_text}"
            summary_response = model.generate_content(summary_prompt)
            resume_summary = summary_response.text
            
            # Generate questions using the existing logic
            language_name = SUPPORTED_LANGUAGES.get(language_code, 'English')
            master_prompt = (
                f"You are an expert AI interviewer. Your task is to generate 5 insightful interview questions in {language_name}. "
                f"The interview is for a '{job_description.splitlines()[0] if job_description else 'Technical Role'}' role. "
                "Please base the questions on the provided job description and candidate's resume. "
                "Start with a welcoming ice-breaker question that also references something specific from the candidate's resume. "
                "Then, generate a mix of technical and behavioral questions. "
                "You MUST format the output as Markdown. "
                "You MUST include '## Technical Questions' and '## Behavioral Questions' headers. "
                "Each question MUST start with a hyphen '-'. "
                "Do NOT add any introductions, greetings (beyond the first ice-breaker question), or concluding remarks. "
                f"\n\n--- JOB DESCRIPTION ---\n{job_description}\n\n--- RESUME ---\n{resume_text}"
            )
            
            full_response = model.generate_content(master_prompt)
            response_text = full_response.text
            
            # Parse questions from response
            sections = re.findall(r"##\s*(.*?)\s*\n(.*?)(?=\n##|\Z)", response_text, re.DOTALL)
            all_questions = []
            
            if not sections:
                # Fallback to simple questions if parsing fails
                all_questions = [
                    {'type': 'Ice-Breaker', 'text': f'Welcome {candidate_name}! Can you tell me about a challenging project you have worked on?'},
                    {'type': 'Technical Questions', 'text': 'What is the difference between `let`, `const`, and `var` in JavaScript?'},
                    {'type': 'Behavioral Questions', 'text': 'Describe a time you had a conflict with a coworker and how you resolved it.'}
                ]
            else:
                for category_name, question_block in sections:
                    lines = question_block.strip().split('\n')
                    for line in lines:
                        if line.strip().startswith('-'):
                            all_questions.append({
                                'type': category_name.strip(), 
                                'text': line.strip().lstrip('- ').strip()
                            })
            
            if not all_questions:
                raise ValueError("No questions were generated or parsed.")
            
            # Create audio files and save questions
            tts_dir = os.path.join(settings.MEDIA_ROOT, 'tts')
            os.makedirs(tts_dir, exist_ok=True)
            
            created_questions = []
            for i, q_data in enumerate(all_questions):
                # Generate audio
                tts = gTTS(
                    text=q_data['text'], 
                    lang=language_code, 
                    tld=config.get('accent_tld', 'com') if language_code == 'en' else 'com'
                )
                tts_path = os.path.join(tts_dir, f'q_{i}_{session.id}.mp3')
                tts.save(tts_path)
                audio_url = f"{settings.MEDIA_URL}tts/{os.path.basename(tts_path)}"
                
                # Create question in database
                question = AIInterviewQuestion.objects.create(
                    session=session,
                    question_text=q_data['text'],
                    question_type=q_data['type'],
                    question_index=i,
                    audio_url=audio_url
                )
                created_questions.append(question)
            
            # Update session with resume summary
            session.resume_summary = resume_summary
            session.save()
            
            logger.info(f"Generated {len(created_questions)} questions for session {session.id}")
            return created_questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            traceback.print_exc()
            raise
    
    @staticmethod
    def transcribe_response(audio_file, session_id, question_id):
        """
        Transcribe audio response using Whisper
        """
        try:
            if not whisper_model:
                raise Exception("Whisper model not available")
            
            # Save audio file temporarily
            file_path = default_storage.save('temp_audio.webm', audio_file)
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            try:
                # Transcribe using Whisper
                result = whisper_model.transcribe(full_path, fp16=False)
                transcribed_text = result.get('text', '')
                
                # Save response to database
                response = AIInterviewResponse.objects.create(
                    session_id=session_id,
                    question_id=question_id,
                    audio_file=audio_file,
                    transcribed_text=transcribed_text,
                    response_time=timezone.now()
                )
                
                # Calculate metrics
                if transcribed_text:
                    # Calculate filler words
                    lower_text = transcribed_text.lower()
                    filler_count = sum(lower_text.count(word) for word in FILLER_WORDS)
                    
                    # Calculate sentiment
                    sentiment = TextBlob(transcribed_text).sentiment.polarity
                    
                    # Update response with metrics
                    response.filler_word_count = filler_count
                    response.sentiment_score = sentiment
                    response.save()
                
                logger.info(f"Transcribed response for question {question_id}: {len(transcribed_text)} characters")
                return response
                
            finally:
                # Clean up temporary file
                if os.path.exists(full_path):
                    os.remove(full_path)
                    
        except Exception as e:
            logger.error(f"Error transcribing response: {e}")
            raise
    
    @staticmethod
    def evaluate_session(session):
        """
        Evaluate the complete interview session using AI
        """
        try:
            # Get all responses for the session
            responses = AIInterviewResponse.objects.filter(session=session).select_related('question')
            
            if not responses:
                raise Exception("No responses found for evaluation")
            
            # Prepare data for evaluation
            config = session.ai_configuration
            job_description = config.get('job_description', '')
            resume_text = config.get('resume_text', '')
            
            # Create Q&A text for evaluation
            qa_text = ""
            for response in responses:
                qa_text += f"Question: {response.question.question_text}\n"
                qa_text += f"Answer: {response.transcribed_text or 'No answer.'}\n\n"
            
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            # Evaluate resume vs job description
            resume_eval_prompt = (
                "You are an expert technical recruiter. Analyze the following resume against the provided job description. "
                "Provide a score from 0.0 to 10.0 indicating how well the candidate's experience aligns with the job requirements. "
                "Also provide a brief analysis. Format your response EXACTLY as follows:\n\n"
                "SCORE: [Your score, e.g., 8.2]\n"
                "ANALYSIS: [Your one-paragraph analysis here.]"
                f"\n\nJOB DESCRIPTION:\n{job_description}\n\nRESUME:\n{resume_text}"
            )
            
            resume_response = model.generate_content(resume_eval_prompt)
            resume_response_text = resume_response.text
            resume_score_match = re.search(r"SCORE:\s*([\d\.]+)", resume_response_text)
            resume_score = float(resume_score_match.group(1)) if resume_score_match else 0.0
            
            # Evaluate interview answers
            answers_eval_prompt = (
                "You are an expert interviewer. Evaluate the candidate's answers to the following questions. "
                "Provide an overall score from 0.0 to 10.0 for their performance. "
                "Also provide a brief summary of their strengths and areas for improvement. "
                "Format your response EXACTLY as follows:\n\n"
                "SCORE: [Your score, e.g., 6.8]\n"
                "FEEDBACK: [Your detailed feedback here.]"
                f"\n\nQUESTIONS & ANSWERS:\n{qa_text}"
            )
            
            answers_response = model.generate_content(answers_eval_prompt)
            answers_response_text = answers_response.text
            answers_score_match = re.search(r"SCORE:\s*([\d\.]+)", answers_response_text)
            answers_score = float(answers_score_match.group(1)) if answers_score_match else 0.0
            
            # Calculate overall score
            overall_score = (resume_score + answers_score) / 2
            
            # Create evaluation result
            result = AIInterviewResult.objects.create(
                session=session,
                resume_score=resume_score,
                answers_score=answers_score,
                overall_score=overall_score,
                resume_feedback=resume_response_text,
                answers_feedback=answers_response_text,
                evaluation_date=timezone.now()
            )
            
            # Update session status
            session.status = 'COMPLETED'
            session.session_ended_at = timezone.now()
            session.save()
            
            logger.info(f"Completed evaluation for session {session.id}. Overall score: {overall_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating session: {e}")
            traceback.print_exc()
            raise
    
    @staticmethod
    def get_session_summary(session):
        """
        Get a summary of the interview session
        """
        try:
            responses = AIInterviewResponse.objects.filter(session=session)
            
            summary = {
                'session_id': str(session.id),
                'candidate_name': session.ai_configuration.get('candidate_name', 'Unknown'),
                'job_title': session.ai_configuration.get('job_title', 'Unknown'),
                'total_questions': AIInterviewQuestion.objects.filter(session=session).count(),
                'total_responses': responses.count(),
                'average_sentiment': responses.aggregate(avg_sentiment=models.Avg('sentiment_score'))['avg_sentiment'] or 0,
                'total_filler_words': responses.aggregate(total_fillers=models.Sum('filler_word_count'))['total_fillers'] or 0,
                'status': session.status,
                'started_at': session.session_started_at,
                'ended_at': session.session_ended_at
            }
            
            # Add evaluation results if available
            try:
                result = AIInterviewResult.objects.get(session=session)
                summary.update({
                    'resume_score': result.resume_score,
                    'answers_score': result.answers_score,
                    'overall_score': result.overall_score
                })
            except AIInterviewResult.DoesNotExist:
                pass
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
            raise

# Global service instance
ai_interview_service = AIInterviewService()
