"""
Comprehensive Interview Evaluation Service using Gemini API
Evaluates complete interview including spoken questions, answers, and coding challenges
"""

import google.generativeai as genai
import json
import logging
from typing import Dict, List, Any, Optional
from django.utils import timezone
from interview_app.models import InterviewSession, InterviewQuestion, CodeSubmission
from evaluation.models import Evaluation
from interviews.models import Interview

logger = logging.getLogger(__name__)

# Configure Gemini API
from django.conf import settings
if getattr(settings, 'GEMINI_API_KEY', ''):
    genai.configure(api_key=settings.GEMINI_API_KEY)

class ComprehensiveEvaluationService:
    """
    Service for comprehensive interview evaluation using Gemini API
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash-002')
    
    def evaluate_complete_interview(self, session_key: str) -> Dict[str, Any]:
        """
        Evaluate complete interview including spoken questions, answers, and coding challenges
        
        Args:
            session_key (str): The interview session key
            
        Returns:
            dict: Comprehensive evaluation results
        """
        try:
            # Get the interview session
            session = InterviewSession.objects.get(session_key=session_key)
            
            # Extract all interview data
            interview_data = self._extract_interview_data(session)
            
            # Perform comprehensive evaluation
            evaluation_result = self._perform_comprehensive_evaluation(interview_data)
            
            # Save evaluation results
            self._save_evaluation_results(session, evaluation_result)
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error in comprehensive evaluation: {e}")
            raise
    
    def _extract_interview_data(self, session: InterviewSession) -> Dict[str, Any]:
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
                data['spoken_questions'].append({
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'order': question.order,
                    'transcribed_answer': question.transcribed_answer or 'No answer provided',
                    'response_time': question.response_time_seconds or 0
                })
        
        # Extract coding submissions
        coding_submissions = CodeSubmission.objects.filter(session=session).order_by('created_at')
        for submission in coding_submissions:
            data['coding_submissions'].append({
                'question_id': submission.question_id,
                'language': submission.language,
                'submitted_code': submission.submitted_code,
                'passed_tests': submission.passed_all_tests,
                'output_log': submission.output_log or '',
                'gemini_evaluation': submission.gemini_evaluation or {}
            })
        
        return data
    
    def _perform_comprehensive_evaluation(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive evaluation using Gemini API
        
        Args:
            interview_data (dict): Complete interview data
            
        Returns:
            dict: Evaluation results
        """
        try:
            # Prepare evaluation prompt
            prompt = self._create_evaluation_prompt(interview_data)
            
            # Get Gemini evaluation
            response = self.model.generate_content(prompt)
            evaluation_text = response.text
            
            # Parse the response
            parsed_evaluation = self._parse_evaluation_response(evaluation_text)
            
            return parsed_evaluation
            
        except Exception as e:
            logger.error(f"Error in Gemini evaluation: {e}")
            # Return fallback evaluation
            return self._create_fallback_evaluation(interview_data)
    
    def _create_evaluation_prompt(self, interview_data: Dict[str, Any]) -> str:
        """
        Create comprehensive evaluation prompt for Gemini
        
        Args:
            interview_data (dict): Complete interview data
            
        Returns:
            str: Evaluation prompt
        """
        session = interview_data['session']
        
        # Build questions and answers section
        qa_section = ""
        for qa in interview_data['spoken_questions']:
            qa_section += f"Q: {qa['question_text']}\nA: {qa['transcribed_answer']}\n\n"
        
        # Build coding section
        coding_section = ""
        for i, submission in enumerate(interview_data['coding_submissions'], 1):
            coding_section += f"Coding Challenge {i}:\n"
            coding_section += f"Language: {submission['language']}\n"
            coding_section += f"Code: {submission['submitted_code'][:500]}...\n"
            coding_section += f"Tests Passed: {submission['passed_tests']}\n"
            coding_section += f"Output: {submission['output_log'][:200]}...\n\n"
        
        prompt = f"""
You are an expert technical interviewer conducting a comprehensive evaluation of a candidate's interview performance.

CANDIDATE INFORMATION:
- Name: {interview_data['candidate_name']}
- Email: {interview_data['candidate_email']}
- Job Description: {interview_data['job_description'][:500]}...

RESUME SUMMARY:
{interview_data['resume_text'][:1000]}...

INTERVIEW QUESTIONS AND ANSWERS:
{qa_section}

CODING CHALLENGES:
{coding_section}

Please provide a comprehensive evaluation with the following format:

OVERALL_SCORE: [0-100]
TECHNICAL_SCORE: [0-100]
BEHAVIORAL_SCORE: [0-100]
CODING_SCORE: [0-100]
COMMUNICATION_SCORE: [0-100]

STRENGTHS:
- [List key strengths]

WEAKNESSES:
- [List areas for improvement]

TECHNICAL_ANALYSIS:
[Detailed technical assessment]

BEHAVIORAL_ANALYSIS:
[Detailed behavioral assessment]

CODING_ANALYSIS:
[Detailed coding assessment]

RECOMMENDATION: [STRONG_HIRE/HIRE/MAYBE/NO_HIRE]
CONFIDENCE_LEVEL: [0-100]

DETAILED_FEEDBACK:
[Comprehensive feedback for the candidate]

HIRING_RECOMMENDATION:
[Final hiring recommendation with reasoning]
"""
        
        return prompt
    
    def _parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini evaluation response
        
        Args:
            response_text (str): Raw response from Gemini
            
        Returns:
            dict: Parsed evaluation data
        """
        import re
        
        # Extract scores
        overall_score = self._extract_score(response_text, "OVERALL_SCORE")
        technical_score = self._extract_score(response_text, "TECHNICAL_SCORE")
        behavioral_score = self._extract_score(response_text, "BEHAVIORAL_SCORE")
        coding_score = self._extract_score(response_text, "CODING_SCORE")
        communication_score = self._extract_score(response_text, "COMMUNICATION_SCORE")
        confidence_level = self._extract_score(response_text, "CONFIDENCE_LEVEL")
        
        # Extract text sections
        strengths = self._extract_section(response_text, "STRENGTHS")
        weaknesses = self._extract_section(response_text, "WEAKNESSES")
        technical_analysis = self._extract_section(response_text, "TECHNICAL_ANALYSIS")
        behavioral_analysis = self._extract_section(response_text, "BEHAVIORAL_ANALYSIS")
        coding_analysis = self._extract_section(response_text, "CODING_ANALYSIS")
        detailed_feedback = self._extract_section(response_text, "DETAILED_FEEDBACK")
        hiring_recommendation = self._extract_section(response_text, "HIRING_RECOMMENDATION")
        
        # Extract recommendation
        recommendation_match = re.search(r"RECOMMENDATION:\s*(\w+)", response_text)
        recommendation = recommendation_match.group(1) if recommendation_match else "MAYBE"
        
        return {
            'overall_score': overall_score,
            'technical_score': technical_score,
            'behavioral_score': behavioral_score,
            'coding_score': coding_score,
            'communication_score': communication_score,
            'confidence_level': confidence_level,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'technical_analysis': technical_analysis,
            'behavioral_analysis': behavioral_analysis,
            'coding_analysis': coding_analysis,
            'detailed_feedback': detailed_feedback,
            'hiring_recommendation': hiring_recommendation,
            'recommendation': recommendation,
            'raw_response': response_text
        }
    
    def _extract_score(self, text: str, label: str) -> float:
        """Extract numeric score from text"""
        import re
        pattern = rf"{label}:\s*(\d+(?:\.\d+)?)"
        match = re.search(pattern, text)
        return float(match.group(1)) if match else 0.0
    
    def _extract_section(self, text: str, label: str) -> str:
        """Extract text section from response"""
        import re
        pattern = rf"{label}:\s*(.*?)(?=\n[A-Z_]+:|$)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _create_fallback_evaluation(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create fallback evaluation when Gemini API fails
        
        Args:
            interview_data (dict): Complete interview data
            
        Returns:
            dict: Fallback evaluation
        """
        # Simple scoring based on available data
        spoken_questions = interview_data['spoken_questions']
        coding_submissions = interview_data['coding_submissions']
        
        # Basic scoring
        answered_questions = len([q for q in spoken_questions if q['transcribed_answer'] and q['transcribed_answer'] != 'No answer provided'])
        total_questions = len(spoken_questions)
        question_score = (answered_questions / max(total_questions, 1)) * 100
        
        passed_coding = len([s for s in coding_submissions if s['passed_tests']])
        total_coding = len(coding_submissions)
        coding_score = (passed_coding / max(total_coding, 1)) * 100 if total_coding > 0 else 0
        
        overall_score = (question_score + coding_score) / 2
        
        return {
            'overall_score': overall_score,
            'technical_score': question_score,
            'behavioral_score': question_score,
            'coding_score': coding_score,
            'communication_score': question_score,
            'confidence_level': 70.0,
            'strengths': f"Answered {answered_questions}/{total_questions} questions",
            'weaknesses': "Limited evaluation data available",
            'technical_analysis': "Basic technical assessment based on question responses",
            'behavioral_analysis': "Basic behavioral assessment based on communication",
            'coding_analysis': f"Completed {passed_coding}/{total_coding} coding challenges" if total_coding > 0 else "No coding challenges",
            'detailed_feedback': "Comprehensive evaluation was not available due to API limitations",
            'hiring_recommendation': "Consider for further evaluation",
            'recommendation': "MAYBE",
            'raw_response': "Fallback evaluation due to API unavailability"
        }
    
    def _save_evaluation_results(self, session: InterviewSession, evaluation_result: Dict[str, Any]):
        """
        Save evaluation results to database
        
        Args:
            session (InterviewSession): The interview session
            evaluation_result (dict): Evaluation results
        """
        try:
            # Find the corresponding Interview object
            interview = Interview.objects.filter(session_key=session.session_key).first()
            
            if interview:
                # Create or update evaluation
                evaluation, created = Evaluation.objects.get_or_create(
                    interview=interview,
                    defaults={
                        'overall_score': evaluation_result['overall_score'] / 10,  # Convert to 0-10 scale
                        'traits': evaluation_result['strengths'],
                        'suggestions': evaluation_result['detailed_feedback'],
                        'coding_score': evaluation_result['coding_score'],
                        'coding_feedback': evaluation_result['coding_analysis'],
                        'coding_strengths': evaluation_result['strengths'],
                        'coding_weaknesses': evaluation_result['weaknesses'],
                        'coding_recommendation': evaluation_result['recommendation'],
                        'gemini_evaluation': evaluation_result,
                        'created_at': timezone.now()
                    }
                )
                
                if not created:
                    # Update existing evaluation
                    evaluation.overall_score = evaluation_result['overall_score'] / 10
                    evaluation.traits = evaluation_result['strengths']
                    evaluation.suggestions = evaluation_result['detailed_feedback']
                    evaluation.coding_score = evaluation_result['coding_score']
                    evaluation.coding_feedback = evaluation_result['coding_analysis']
                    evaluation.coding_strengths = evaluation_result['strengths']
                    evaluation.coding_weaknesses = evaluation_result['weaknesses']
                    evaluation.coding_recommendation = evaluation_result['recommendation']
                    evaluation.gemini_evaluation = evaluation_result
                    evaluation.save()
                
                logger.info(f"Saved comprehensive evaluation for interview {interview.id}")
            else:
                logger.warning(f"No Interview object found for session {session.session_key}")
                
        except Exception as e:
            logger.error(f"Error saving evaluation results: {e}")


# Global instance
comprehensive_evaluation_service = ComprehensiveEvaluationService()
