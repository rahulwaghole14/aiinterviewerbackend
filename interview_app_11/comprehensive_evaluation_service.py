"""
Comprehensive Interview Evaluation Service using Gemini API
Evaluates complete interview including spoken questions, answers, and coding challenges
"""

import google.generativeai as genai
import json
import logging
import requests
from typing import Dict, List, Any, Optional
from django.utils import timezone
from interview_app.models import InterviewSession, InterviewQuestion, CodeSubmission
from evaluation.models import Evaluation
from interviews.models import Interview

logger = logging.getLogger(__name__)

# Configure Gemini API
from django.conf import settings
_gemini_api_key = getattr(settings, 'GEMINI_API_KEY', '')
if _gemini_api_key:
    try:
        genai.configure(api_key=_gemini_api_key)
        print("✅ Gemini API configured successfully")
    except Exception as e:
        print(f"⚠️ Error configuring Gemini API: {e}")
else:
    print("⚠️ GEMINI_API_KEY not set in Django settings")

class ComprehensiveEvaluationService:
    """
    Service for comprehensive interview evaluation using Gemini API
    """
    
    def __init__(self):
        # Try newer models first (gemini-2.5-flash, gemini-2.0-flash-exp)
        # Then fallback to older models
        model_priority = [
            'gemini-2.0-flash-exp',  # Latest experimental
            'gemini-2.5-flash',       # Latest stable
            'gemini-1.5-pro-latest',  # Latest of 1.5 series
            'models/gemini-pro',      # Try with models/ prefix
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
            # Last resort: try to use REST API directly
            print("⚠️ All SDK models failed, will use REST API fallback")
            self.use_rest_api = True
            self.api_key = _gemini_api_key
        else:
            self.use_rest_api = False
    
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
            print(f"📋 Evaluating interview session: {session_key}")
            print(f"   Candidate: {session.candidate_name}")
            
            # Extract all interview data
            interview_data = self._extract_interview_data(session)
            
            # Validate we have data
            if not interview_data['spoken_questions'] and not interview_data['coding_submissions']:
                print(f"⚠️ No interview data found (no Q&A or coding submissions)")
                return self._create_fallback_evaluation(interview_data)
            
            print(f"📊 Interview data extracted:")
            print(f"   - {len(interview_data['spoken_questions'])} Q&A pairs")
            print(f"   - {len(interview_data['coding_submissions'])} coding submissions")
            
            # Perform comprehensive evaluation
            print(f"🤖 Calling Gemini API for comprehensive evaluation...")
            evaluation_result = self._perform_comprehensive_evaluation(interview_data)
            
            print(f"✅ Gemini evaluation completed:")
            print(f"   - Overall Score: {evaluation_result.get('overall_score', 0):.1f}/100")
            print(f"   - Technical Score: {evaluation_result.get('technical_score', 0):.1f}/100")
            print(f"   - Coding Score: {evaluation_result.get('coding_score', 0):.1f}/100")
            
            # Save evaluation results (optional - already saved in services.py)
            # self._save_evaluation_results(session, evaluation_result)
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error in comprehensive evaluation: {e}")
            import traceback
            traceback.print_exc()
            # Return fallback instead of raising
            try:
                session = InterviewSession.objects.get(session_key=session_key)
                interview_data = self._extract_interview_data(session)
                return self._create_fallback_evaluation(interview_data)
            except:
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
            'coding_questions': [],
            'resume_text': session.resume_text or '',
            'job_description': session.job_description or '',
            'candidate_name': session.candidate_name,
            'candidate_email': session.candidate_email
        }
        
        # Extract spoken questions and answers
        questions = InterviewQuestion.objects.filter(session=session).order_by('order')
        for question in questions:
            if question.question_type in ['TECHNICAL', 'BEHAVIORAL', 'Ice-Breaker']:
                # Only include questions that have answers (non-empty transcribed_answer)
                transcribed_answer = (question.transcribed_answer or '').strip()
                if transcribed_answer and transcribed_answer != 'No answer provided':
                    data['spoken_questions'].append({
                        'question_text': question.question_text,
                        'question_type': question.question_type,
                        'order': question.order,
                        'transcribed_answer': transcribed_answer,
                        'response_time': question.response_time_seconds or 0
                    })
                else:
                    # Still include questions even without answers for context
                    data['spoken_questions'].append({
                        'question_text': question.question_text,
                        'question_type': question.question_type,
                        'order': question.order,
                        'transcribed_answer': transcribed_answer or 'No answer provided',
                        'response_time': question.response_time_seconds or 0
                    })
        
        # Extract coding questions with test cases
        coding_questions = InterviewQuestion.objects.filter(
            session=session, 
            question_type='CODING'
        ).order_by('order')
        
        for coding_q in coding_questions:
            # Get test cases for this coding question
            from interview_app.models import TestCase
            test_cases = []
            try:
                test_cases_objs = TestCase.objects.filter(question=coding_q)
                for tc in test_cases_objs:
                    test_cases.append({
                        'input': tc.input_data,
                        'expected_output': tc.expected_output,
                        'is_hidden': tc.is_hidden
                    })
            except Exception as e:
                print(f"⚠️ Error getting test cases for question {coding_q.id}: {e}")
            
            data['coding_questions'].append({
                'question_id': str(coding_q.id),
                'question_text': coding_q.question_text,
                'language': coding_q.coding_language or 'PYTHON',
                'test_cases': test_cases
            })
        
        # Extract coding submissions with full details
        coding_submissions = CodeSubmission.objects.filter(session=session).order_by('created_at')
        for submission in coding_submissions:
            # Get the corresponding coding question to include test cases
            coding_question_detail = None
            for cq in data['coding_questions']:
                if cq['question_id'] == str(submission.question_id):
                    coding_question_detail = cq
                    break
            
            submission_data = {
                'question_id': submission.question_id,
                'question_text': coding_question_detail['question_text'] if coding_question_detail else 'Coding Challenge',
                'language': submission.language,
                'submitted_code': submission.submitted_code,
                'passed_tests': submission.passed_all_tests,
                'output_log': submission.output_log or '',
                'gemini_evaluation': submission.gemini_evaluation or {}
            }
            
            # Add test cases from the coding question
            if coding_question_detail:
                submission_data['test_cases'] = coding_question_detail.get('test_cases', [])
            
            data['coding_submissions'].append(submission_data)
        
        print(f"📊 Extracted interview data: {len(data['spoken_questions'])} Q&A pairs, {len(data['coding_submissions'])} coding submissions")
        
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
            
            # Get Gemini evaluation with better error handling
            try:
                if hasattr(self, 'use_rest_api') and self.use_rest_api:
                    # Use REST API directly with v1 endpoint
                    evaluation_text = self._call_gemini_rest_api(prompt)
                elif self.model:
                    response = self.model.generate_content(prompt)
                    evaluation_text = response.text
                else:
                    # No model available, try REST API
                    print("⚠️ No model available, trying REST API fallback")
                    evaluation_text = self._call_gemini_rest_api(prompt)
                
                if not evaluation_text:
                    print("⚠️ Gemini returned empty response, using fallback")
                    return self._create_fallback_evaluation(interview_data)
            except Exception as api_error:
                logger.error(f"Error calling Gemini API: {api_error}")
                print(f"⚠️ Gemini API error: {api_error}")
                # Check if it's a model not found error
                error_str = str(api_error).lower()
                if 'not found' in error_str or 'v1beta' in error_str:
                    print(f"⚠️ Model compatibility issue detected. Trying REST API fallback...")
                    # Try REST API as fallback
                    try:
                        evaluation_text = self._call_gemini_rest_api(prompt)
                        if evaluation_text:
                            print("✅ REST API fallback succeeded")
                        else:
                            return self._create_fallback_evaluation(interview_data)
                    except Exception as rest_error:
                        print(f"⚠️ REST API fallback also failed: {rest_error}")
                        return self._create_fallback_evaluation(interview_data)
                else:
                    # Return fallback evaluation
                    return self._create_fallback_evaluation(interview_data)
            
            # Parse the response
            parsed_evaluation = self._parse_evaluation_response(evaluation_text)
            
            return parsed_evaluation
            
        except Exception as e:
            logger.error(f"Error in Gemini evaluation: {e}")
            import traceback
            traceback.print_exc()
            # Return fallback evaluation
            return self._create_fallback_evaluation(interview_data)
    
    def _call_gemini_rest_api(self, prompt: str) -> str:
        """
        Call Gemini API using REST API directly (v1 endpoint)
        This bypasses SDK version issues
        
        Args:
            prompt (str): The evaluation prompt
            
        Returns:
            str: Response text from Gemini
        """
        # Get API key if not already set
        if not hasattr(self, 'api_key') or not self.api_key:
            from django.conf import settings
            self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        
        if not self.api_key:
            raise ValueError("API key not available for REST API call")
        
        # Use v1 API endpoint (not v1beta)
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract text from response
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if len(parts) > 0 and 'text' in parts[0]:
                        return parts[0]['text']
            
            raise ValueError("Unexpected response format from Gemini REST API")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"REST API request failed: {e}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"REST API response parsing failed: {e}")
            raise
    
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
        
        # Build coding section with full context
        coding_section = ""
        for i, submission in enumerate(interview_data['coding_submissions'], 1):
            coding_section += f"Coding Challenge {i}:\n"
            coding_section += f"Question: {submission.get('question_text', 'Coding Challenge')}\n"
            coding_section += f"Language: {submission['language']}\n"
            coding_section += f"Submitted Code:\n{submission['submitted_code']}\n"
            coding_section += f"Tests Passed: {submission['passed_tests']}\n"
            
            # Include test cases if available
            if submission.get('test_cases'):
                coding_section += f"Test Cases:\n"
                for j, tc in enumerate(submission['test_cases'], 1):
                    coding_section += f"  Test {j}: Input={tc.get('input', 'N/A')}, Expected={tc.get('expected_output', 'N/A')}\n"
            
            coding_section += f"Output/Results: {submission['output_log'][:500] if submission.get('output_log') else 'No output'}\n\n"
        
        # Build comprehensive prompt with all context
        job_desc = interview_data['job_description'] or 'Not provided'
        resume_text = interview_data['resume_text'] or 'Not provided'
        
        # Ensure we have meaningful data
        if not qa_section.strip():
            qa_section = "No questions and answers were recorded during the technical interview."
        if not coding_section.strip():
            coding_section = "No coding submissions were recorded during the coding round."
        
        prompt = f"""
You are an expert technical interviewer conducting a comprehensive evaluation of a candidate's interview performance.

CANDIDATE INFORMATION:
- Name: {interview_data['candidate_name']}
- Email: {interview_data['candidate_email']}
- Job Description: {job_desc[:1500]}

RESUME SUMMARY:
{resume_text[:2000]}

TECHNICAL INTERVIEW - QUESTIONS AND ANSWERS:
{qa_section}

CODING ROUND - CHALLENGES AND SUBMISSIONS:
{coding_section}

Please provide a comprehensive evaluation analyzing:
1. Technical interview performance (quality of answers, depth of knowledge, clarity, relevance to job requirements)
2. Coding round performance (code quality, test case passing, problem-solving approach, code efficiency)
3. Overall communication skills and behavioral traits
4. Strengths and specific areas for improvement
5. Overall fit for the role based on both technical and coding performance

Provide the evaluation in the following format. IMPORTANT: Include ALL metrics needed for data visualization graphs:

OVERALL_SCORE: [0-100]
TECHNICAL_SCORE: [0-100]
BEHAVIORAL_SCORE: [0-100]
CODING_SCORE: [0-100]
COMMUNICATION_SCORE: [0-100]
PROBLEM_SOLVING_SCORE: [0-100] (average of technical and coding scores)
QUESTIONS_ATTEMPTED: [number of questions answered]
QUESTIONS_CORRECT: [number of correct answers]
ACCURACY_PERCENTAGE: [0-100] (percentage of correct answers)

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
        problem_solving_score = self._extract_score(response_text, "PROBLEM_SOLVING_SCORE")
        confidence_level = self._extract_score(response_text, "CONFIDENCE_LEVEL")
        
        # Extract graph metrics
        questions_attempted = int(self._extract_score(response_text, "QUESTIONS_ATTEMPTED"))
        questions_correct = int(self._extract_score(response_text, "QUESTIONS_CORRECT"))
        accuracy_percentage = self._extract_score(response_text, "ACCURACY_PERCENTAGE")
        
        # Calculate problem solving score if not provided (average of technical and coding)
        if problem_solving_score == 0 and (technical_score > 0 or coding_score > 0):
            problem_solving_score = (technical_score + coding_score) / 2
        
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
            'problem_solving_score': problem_solving_score,
            'confidence_level': confidence_level,
            'questions_attempted': questions_attempted,
            'questions_correct': questions_correct,
            'accuracy_percentage': accuracy_percentage,
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
        problem_solving_score = (question_score + coding_score) / 2
        
        # Calculate accuracy
        questions_attempted = answered_questions
        questions_correct = int((overall_score / 100) * questions_attempted) if questions_attempted > 0 else 0
        accuracy_percentage = (questions_correct / questions_attempted * 100) if questions_attempted > 0 else 0
        
        return {
            'overall_score': overall_score,
            'technical_score': question_score,
            'behavioral_score': question_score,
            'coding_score': coding_score,
            'communication_score': question_score,
            'problem_solving_score': problem_solving_score,
            'confidence_level': 70.0,
            'questions_attempted': questions_attempted,
            'questions_correct': questions_correct,
            'accuracy_percentage': accuracy_percentage,
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
                # Create or update evaluation (only use fields that exist in Evaluation model)
                # Evaluation model has: interview, overall_score, traits, suggestions, created_at
                evaluation, created = Evaluation.objects.get_or_create(
                    interview=interview,
                    defaults={
                        'overall_score': min(evaluation_result['overall_score'] / 10, 10.0),  # Convert to 0-10 scale, cap at 10
                        'traits': f"Strengths: {evaluation_result.get('strengths', 'N/A')}\nWeaknesses: {evaluation_result.get('weaknesses', 'N/A')}\nTechnical: {evaluation_result.get('technical_analysis', 'N/A')}\nBehavioral: {evaluation_result.get('behavioral_analysis', 'N/A')}\nCoding: {evaluation_result.get('coding_analysis', 'N/A')}",
                        'suggestions': f"{evaluation_result.get('detailed_feedback', 'N/A')}\n\nHiring Recommendation: {evaluation_result.get('hiring_recommendation', 'N/A')}\nRecommendation: {evaluation_result.get('recommendation', 'MAYBE')}",
                    }
                )
                
                if not created:
                    # Update existing evaluation
                    evaluation.overall_score = min(evaluation_result['overall_score'] / 10, 10.0)
                    evaluation.traits = f"Strengths: {evaluation_result.get('strengths', 'N/A')}\nWeaknesses: {evaluation_result.get('weaknesses', 'N/A')}\nTechnical: {evaluation_result.get('technical_analysis', 'N/A')}\nBehavioral: {evaluation_result.get('behavioral_analysis', 'N/A')}\nCoding: {evaluation_result.get('coding_analysis', 'N/A')}"
                    evaluation.suggestions = f"{evaluation_result.get('detailed_feedback', 'N/A')}\n\nHiring Recommendation: {evaluation_result.get('hiring_recommendation', 'N/A')}\nRecommendation: {evaluation_result.get('recommendation', 'MAYBE')}"
                    evaluation.save()
                
                # Update interview status to completed if not already
                if interview.status != Interview.Status.COMPLETED:
                    interview.status = Interview.Status.COMPLETED
                    interview.save(update_fields=['status'])
                
                logger.info(f"Saved comprehensive evaluation for interview {interview.id}")
            else:
                logger.warning(f"No Interview object found for session {session.session_key}")
                
        except Exception as e:
            logger.error(f"Error saving evaluation results: {e}")


# Global instance
comprehensive_evaluation_service = ComprehensiveEvaluationService()
