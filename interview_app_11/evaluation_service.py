"""
Comprehensive evaluation service for interview app
Extracts questions, answers, and coding results for complete evaluation
"""

import json
import re
from django.utils import timezone
from django.db import transaction
from interview_app.models import InterviewSession, InterviewQuestion, CodeSubmission
from ai_interview.models import AIInterviewSession, AIInterviewResult
from interviews.models import Interview
from evaluation.models import Evaluation
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

class ComprehensiveEvaluationService:
    """
    Service to evaluate complete interview sessions including spoken questions and coding challenges
    """
    
    def __init__(self):
        # Configure Gemini API - Get from Django settings
        from django.conf import settings
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if api_key:
            genai.configure(api_key=api_key)
            # Try newer models first, then fallback
            model_priority = [
                'gemini-2.0-flash-exp',  # Latest experimental
                'gemini-2.5-flash',       # Latest stable
                'gemini-1.5-pro-latest',  # Latest of 1.5 series
                'gemini-pro',             # Standard name
            ]
            
            self.model = None
            self.model_name = None
            
            for model_name in model_priority:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    self.model_name = model_name
                    print(f"✅ Using Gemini model: {model_name}")
                    break
                except Exception as e:
                    print(f"⚠️ Error with {model_name}: {e}")
                    continue
            
            if self.model is None:
                print("⚠️ All SDK models failed, evaluation will use fallback")
                self.model = None
        else:
            raise ValueError("GEMINI_API_KEY not set in environment. Set GEMINI_API_KEY or GOOGLE_API_KEY in .env file")
    
    def evaluate_complete_interview(self, session_key):
        """
        Evaluate a complete interview session including all questions and coding results
        
        Args:
            session_key (str): The session key for the interview
            
        Returns:
            dict: Complete evaluation results
        """
        try:
            # Get the interview session
            session = InterviewSession.objects.get(session_key=session_key)
            
            # Extract all interview data
            interview_data = self._extract_interview_data(session)
            
            # Perform comprehensive evaluation
            evaluation_results = self._perform_comprehensive_evaluation(interview_data)
            
            # Create evaluation records
            self._create_evaluation_records(session, evaluation_results)
            
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Error evaluating interview session {session_key}: {e}")
            raise
    
    def _extract_interview_data(self, session):
        """
        Extract all questions, answers, and coding results from the session
        
        Args:
            session (InterviewSession): The interview session
            
        Returns:
            dict: Complete interview data
        """
        data = {
            'session': session,
            'spoken_questions': [],
            'coding_submissions': [],
            'resume_text': session.resume_text or '',
            'job_description': session.job_description or '',
            'candidate_name': session.candidate_name,
            'candidate_email': session.candidate_email
        }
        
        # Extract spoken questions and answers
        questions = InterviewQuestion.objects.filter(session=session).order_by('order')
        for question in questions:
            if question.question_type in ['TECHNICAL', 'BEHAVIORAL', 'Ice-Breaker']:
                # For spoken questions, we need to get the transcribed answers
                # This would come from the audio transcription system
                data['spoken_questions'].append({
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'order': question.order,
                    'transcribed_answer': question.transcribed_answer or 'No answer provided'
                })
        
        # Extract coding submissions
        coding_submissions = CodeSubmission.objects.filter(session=session).order_by('created_at')
        for submission in coding_submissions:
            data['coding_submissions'].append({
                'question_id': submission.question_id,
                'submitted_code': submission.submitted_code,
                'language': submission.language,
                'passed_all_tests': submission.passed_all_tests,
                'output_log': submission.output_log,
                'gemini_evaluation': submission.gemini_evaluation
            })
        
        return data
    
    def _perform_comprehensive_evaluation(self, interview_data):
        """
        Perform comprehensive evaluation using Gemini API
        
        Args:
            interview_data (dict): Complete interview data
            
        Returns:
            dict: Evaluation results
        """
        results = {
            'resume_score': 0.0,
            'answers_score': 0.0,
            'coding_score': 0.0,
            'overall_score': 0.0,
            'resume_feedback': '',
            'answers_feedback': '',
            'coding_feedback': '',
            'overall_feedback': '',
            'recommendation': 'NO_HIRE'
        }
        
        try:
            # 1. Evaluate Resume
            if interview_data['resume_text']:
                results.update(self._evaluate_resume(interview_data))
            
            # 2. Evaluate Spoken Answers
            if interview_data['spoken_questions']:
                results.update(self._evaluate_spoken_answers(interview_data))
            
            # 3. Evaluate Coding Performance
            if interview_data['coding_submissions']:
                results.update(self._evaluate_coding_performance(interview_data))
            
            # 4. Calculate Overall Score and Recommendation
            results.update(self._calculate_overall_evaluation(results))
            
        except Exception as e:
            logger.error(f"Error in comprehensive evaluation: {e}")
            # Fallback to basic scoring
            results['overall_score'] = 5.0
            results['overall_feedback'] = f"Evaluation completed with basic scoring due to error: {e}"
        
        return results
    
    def _evaluate_resume(self, interview_data):
        """Evaluate resume using Gemini API"""
        try:
            prompt = f"""
            You are an expert recruiter evaluating a candidate's resume for a technical position.
            
            Resume Text:
            {interview_data['resume_text']}
            
            Job Description:
            {interview_data['job_description']}
            
            Please provide:
            1. A score from 0.0 to 10.0
            2. Detailed feedback on strengths and areas for improvement
            
            Format your response EXACTLY as follows:
            SCORE: [Your score, e.g., 7.5]
            FEEDBACK: [Your detailed feedback here]
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            score_match = re.search(r"SCORE:\s*([\d\.]+)", response_text)
            feedback_match = re.search(r"FEEDBACK:\s*(.*?)(?=\n|$)", response_text, re.DOTALL)
            
            return {
                'resume_score': float(score_match.group(1)) if score_match else 5.0,
                'resume_feedback': feedback_match.group(1).strip() if feedback_match else response_text
            }
            
        except Exception as e:
            logger.error(f"Error evaluating resume: {e}")
            return {
                'resume_score': 5.0,
                'resume_feedback': f"Resume evaluation failed: {e}"
            }
    
    def _evaluate_spoken_answers(self, interview_data):
        """Evaluate spoken answers using Gemini API"""
        try:
            qa_text = ""
            for qa in interview_data['spoken_questions']:
                qa_text += f"Question ({qa['question_type']}): {qa['question_text']}\n"
                qa_text += f"Answer: {qa['transcribed_answer']}\n\n"
            
            prompt = f"""
            You are an expert interviewer evaluating a candidate's spoken responses.
            
            Questions and Answers:
            {qa_text}
            
            Please provide:
            1. A score from 0.0 to 10.0
            2. Detailed feedback on communication, relevance, and technical knowledge
            
            Format your response EXACTLY as follows:
            SCORE: [Your score, e.g., 7.5]
            FEEDBACK: [Your detailed feedback here]
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            score_match = re.search(r"SCORE:\s*([\d\.]+)", response_text)
            feedback_match = re.search(r"FEEDBACK:\s*(.*?)(?=\n|$)", response_text, re.DOTALL)
            
            return {
                'answers_score': float(score_match.group(1)) if score_match else 5.0,
                'answers_feedback': feedback_match.group(1).strip() if feedback_match else response_text
            }
            
        except Exception as e:
            logger.error(f"Error evaluating spoken answers: {e}")
            return {
                'answers_score': 5.0,
                'answers_feedback': f"Spoken answers evaluation failed: {e}"
            }
    
    def _evaluate_coding_performance(self, interview_data):
        """Evaluate coding performance using existing Gemini evaluations or create new ones"""
        try:
            coding_submissions = interview_data['coding_submissions']
            total_score = 0.0
            total_feedback = ""
            
            for submission in coding_submissions:
                if submission['gemini_evaluation']:
                    # Use existing Gemini evaluation
                    gemini_data = submission['gemini_evaluation']
                    total_score += gemini_data.get('overall_score', 0) / 100 * 10  # Convert to 0-10 scale
                    total_feedback += f"Code Quality: {gemini_data.get('feedback', 'No feedback')}\n"
                else:
                    # Create new evaluation
                    evaluation = self._evaluate_single_code_submission(submission)
                    total_score += evaluation['score']
                    total_feedback += f"Code Quality: {evaluation['feedback']}\n"
            
            avg_score = total_score / len(coding_submissions) if coding_submissions else 0.0
            
            return {
                'coding_score': avg_score,
                'coding_feedback': total_feedback.strip()
            }
            
        except Exception as e:
            logger.error(f"Error evaluating coding performance: {e}")
            return {
                'coding_score': 5.0,
                'coding_feedback': f"Coding evaluation failed: {e}"
            }
    
    def _evaluate_single_code_submission(self, submission):
        """Evaluate a single code submission"""
        try:
            prompt = f"""
            You are an expert code reviewer evaluating a coding submission.
            
            Code:
            {submission['submitted_code']}
            
            Language: {submission['language']}
            Test Results: {submission['output_log']}
            Passed Tests: {submission['passed_all_tests']}
            
            Please provide:
            1. A score from 0.0 to 10.0
            2. Detailed feedback on code quality, correctness, and best practices
            
            Format your response EXACTLY as follows:
            SCORE: [Your score, e.g., 7.5]
            FEEDBACK: [Your detailed feedback here]
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            score_match = re.search(r"SCORE:\s*([\d\.]+)", response_text)
            feedback_match = re.search(r"FEEDBACK:\s*(.*?)(?=\n|$)", response_text, re.DOTALL)
            
            return {
                'score': float(score_match.group(1)) if score_match else 5.0,
                'feedback': feedback_match.group(1).strip() if feedback_match else response_text
            }
            
        except Exception as e:
            logger.error(f"Error evaluating single code submission: {e}")
            return {
                'score': 5.0,
                'feedback': f"Code evaluation failed: {e}"
            }
    
    def _calculate_overall_evaluation(self, results):
        """Calculate overall score and recommendation"""
        try:
            # Weighted average: 30% resume, 40% answers, 30% coding
            overall_score = (
                results['resume_score'] * 0.3 +
                results['answers_score'] * 0.4 +
                results['coding_score'] * 0.3
            )
            
            # Determine recommendation
            if overall_score >= 8.0:
                recommendation = 'STRONG_YES'
            elif overall_score >= 6.5:
                recommendation = 'YES'
            elif overall_score >= 5.0:
                recommendation = 'MAYBE'
            else:
                recommendation = 'NO'
            
            # Generate overall feedback
            overall_feedback = f"""
            Overall Performance Score: {overall_score:.1f}/10.0
            
            Resume Score: {results['resume_score']:.1f}/10.0
            Interview Answers: {results['answers_score']:.1f}/10.0
            Coding Performance: {results['coding_score']:.1f}/10.0
            
            Recommendation: {recommendation}
            
            This candidate shows {'strong' if overall_score >= 7.0 else 'moderate' if overall_score >= 5.0 else 'weak'} potential for the role.
            """
            
            return {
                'overall_score': overall_score,
                'overall_feedback': overall_feedback.strip(),
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall evaluation: {e}")
            return {
                'overall_score': 5.0,
                'overall_feedback': f"Overall evaluation failed: {e}",
                'recommendation': 'MAYBE'
            }
    
    def _create_evaluation_records(self, session, evaluation_results):
        """Create evaluation records in the database"""
        try:
            with transaction.atomic():
                # Find the corresponding Interview record
                interview = Interview.objects.filter(session_key=session.session_key).first()
                
                if interview:
                    # Create or update Evaluation record
                    evaluation, created = Evaluation.objects.get_or_create(
                        interview=interview,
                        defaults={
                            'overall_score': evaluation_results['overall_score'],
                            'traits': evaluation_results['overall_feedback'],
                            'suggestions': evaluation_results['overall_feedback'],
                            'coding_score': evaluation_results['coding_score'] * 10,  # Convert to 0-100 scale
                            'coding_feedback': evaluation_results['coding_feedback'],
                            'coding_recommendation': evaluation_results['recommendation'],
                            'created_at': timezone.now()
                        }
                    )
                    
                    if not created:
                        # Update existing evaluation
                        evaluation.overall_score = evaluation_results['overall_score']
                        evaluation.traits = evaluation_results['overall_feedback']
                        evaluation.suggestions = evaluation_results['overall_feedback']
                        evaluation.coding_score = evaluation_results['coding_score'] * 10
                        evaluation.coding_feedback = evaluation_results['coding_feedback']
                        evaluation.coding_recommendation = evaluation_results['recommendation']
                        evaluation.save()
                    
                    logger.info(f"Created/updated evaluation for interview {interview.id}: {evaluation_results['overall_score']:.1f}/10.0")
                
        except Exception as e:
            logger.error(f"Error creating evaluation records: {e}")
            raise
