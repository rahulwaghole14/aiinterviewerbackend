"""
Comprehensive Evaluation Service
Provides detailed AI-powered evaluation of complete interviews using Gemini
"""
import re
import google.generativeai as genai
from django.conf import settings
from interview_app.models import InterviewSession, InterviewQuestion, CodeSubmission

# Configure Gemini
api_key = getattr(settings, 'GEMINI_API_KEY', None) or getattr(settings, 'GOOGLE_API_KEY', None)
if api_key:
    genai.configure(api_key=api_key)
else:
    print("⚠️ WARNING: GEMINI_API_KEY not set. Comprehensive evaluation may fail.")


class ComprehensiveEvaluationService:
    """
    Service for comprehensive AI evaluation of interview sessions
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash') if api_key else None
    
    def evaluate_complete_interview(self, session_key: str) -> dict:
        """
        Evaluate a complete interview session comprehensively
        
        Args:
            session_key (str): The interview session key
            
        Returns:
            dict: Comprehensive evaluation results with scores, analysis, and recommendations
        """
        try:
            # Get the session
            session = InterviewSession.objects.get(session_key=session_key)
            
            # Collect all questions and answers
            all_questions = InterviewQuestion.objects.filter(session=session).order_by('conversation_sequence', 'order')
            
            # Separate technical, behavioral, and coding questions
            technical_qa = []
            behavioral_qa = []
            coding_submissions = []
            
            # Build a map of question_id -> question_text for AI questions
            ai_questions_map = {}
            for q in all_questions:
                # AI questions have role='AI' and question_text
                if (q.role == 'AI' or (not q.role and q.question_text)) and q.question_text:
                    ai_questions_map[q.id] = {
                        'text': q.question_text,
                        'type': q.question_type,
                        'order': q.order
                    }
            
            # Process interviewee answers and match with AI questions
            for q in all_questions:
                # Interviewee answers have role='INTERVIEWEE' and transcribed_answer
                if q.role == 'INTERVIEWEE' and q.transcribed_answer:
                    # Find the corresponding AI question
                    # Try to find by order (answer usually has same order as question)
                    corresponding_question = None
                    for ai_q in all_questions:
                        if (ai_q.role == 'AI' or (not ai_q.role and ai_q.question_text)) and ai_q.order == q.order:
                            corresponding_question = ai_q.question_text
                            break
                    
                    # If not found by order, try to find by conversation_sequence (answer is usually sequence-1)
                    if not corresponding_question and q.conversation_sequence:
                        prev_seq = q.conversation_sequence - 1
                        for ai_q in all_questions:
                            if ai_q.conversation_sequence == prev_seq and ai_q.question_text:
                                corresponding_question = ai_q.question_text
                                break
                    
                    question_text = corresponding_question or 'Question not available'
                    
                    if q.question_type == 'TECHNICAL':
                        technical_qa.append({
                            'question': question_text,
                            'answer': q.transcribed_answer,
                            'question_level': q.question_level or 'MAIN',
                            'response_time': q.response_time_seconds,
                            'words_per_minute': q.words_per_minute,
                            'filler_word_count': q.filler_word_count or 0,
                            'order': q.order,
                            'conversation_sequence': q.conversation_sequence
                        })
                    elif q.question_type == 'BEHAVIORAL':
                        behavioral_qa.append({
                            'question': question_text,
                            'answer': q.transcribed_answer,
                            'question_level': q.question_level or 'MAIN',
                            'response_time': q.response_time_seconds,
                            'words_per_minute': q.words_per_minute,
                            'filler_word_count': q.filler_word_count or 0,
                            'order': q.order,
                            'conversation_sequence': q.conversation_sequence
                        })
            
            # Process coding questions - collect ALL coding submissions
            # First, get all coding submissions for this session
            all_code_submissions = CodeSubmission.objects.filter(session=session).order_by('created_at')
            print(f"🔍 Found {all_code_submissions.count()} code submissions for session {session_key}")
            
            # Map submissions to questions
            for code_submission in all_code_submissions:
                try:
                    # Try to find the corresponding question
                    question = None
                    if code_submission.question_id:
                        # Try to get question by ID (as string or UUID)
                        try:
                            question = InterviewQuestion.objects.get(id=code_submission.question_id)
                        except InterviewQuestion.DoesNotExist:
                            # Try as string
                            try:
                                question = InterviewQuestion.objects.get(id=str(code_submission.question_id))
                            except InterviewQuestion.DoesNotExist:
                                pass
                    
                    # If question not found by ID, try to find any CODING question for this session
                    if not question:
                        coding_questions = InterviewQuestion.objects.filter(
                            session=session,
                            question_type='CODING'
                        ).order_by('order', 'id')
                        # Match by order or just use first coding question
                        if coding_questions.exists():
                            question = coding_questions.first()
                    
                    question_text = question.question_text if question and question.question_text else f"Coding Challenge {len(coding_submissions) + 1}"
                    
                    coding_submissions.append({
                        'question': question_text,
                        'code': code_submission.submitted_code or '',
                        'language': code_submission.language or 'Unknown',
                        'test_results': code_submission.output_log or 'No test results',
                        'passed_tests': code_submission.passed_count or 0,
                        'total_tests': code_submission.total_count or 0,
                        'passed_all_tests': code_submission.passed_all_tests or False
                    })
                    print(f"✅ Added coding submission: {question_text[:50]}... ({code_submission.language}, {code_submission.passed_count}/{code_submission.total_count} tests passed)")
                except Exception as e:
                    print(f"⚠️ Error processing code submission {code_submission.id}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Also check for coding questions that might not have submissions yet
            for q in all_questions:
                if q.question_type == 'CODING':
                    # Check if we already have a submission for this question
                    has_submission = False
                    for sub in coding_submissions:
                        if sub.get('question') == q.question_text:
                            has_submission = True
                            break
                    
                    # If no submission found, still include the question (candidate might not have submitted)
                    if not has_submission and q.question_text:
                        coding_submissions.append({
                            'question': q.question_text,
                            'code': 'No code submitted',
                            'language': q.coding_language or 'Unknown',
                            'test_results': 'No submission received',
                            'passed_tests': 0,
                            'total_tests': 0,
                            'passed_all_tests': False
                        })
                        print(f"⚠️ Coding question found but no submission: {q.question_text[:50]}...")
            
            print(f"📊 Total coding submissions/challenges collected: {len(coding_submissions)}")
            
            # Fallback: If no interviewee answers found, try to get from questions with transcribed_answer
            if not technical_qa and not behavioral_qa:
                for q in all_questions:
                    if q.transcribed_answer and q.transcribed_answer.strip() and q.transcribed_answer != 'No answer provided':
                        question_text = q.question_text if q.question_text else 'Question not available'
                        if q.question_type == 'TECHNICAL':
                            technical_qa.append({
                                'question': question_text,
                                'answer': q.transcribed_answer
                            })
                        elif q.question_type == 'BEHAVIORAL':
                            behavioral_qa.append({
                                'question': question_text,
                                'answer': q.transcribed_answer
                            })
            
            # If no data available, return minimal evaluation
            if not technical_qa and not behavioral_qa and not coding_submissions:
                print(f"⚠️ No interview data found for session {session_key}, returning minimal evaluation")
                return {
                    'overall_score': 0.0,
                    'technical_score': 0,
                    'behavioral_score': 0,
                    'coding_score': 0,
                    'communication_score': 0,
                    'confidence_level': 0,
                    'strengths': ['Interview completed but no answers were provided'],
                    'weaknesses': ['No interview responses available for evaluation'],
                    'technical_analysis': 'No technical questions were answered during the interview.',
                    'behavioral_analysis': 'No behavioral questions were answered during the interview.',
                    'coding_analysis': 'No coding challenges were part of this interview.',
                    'detailed_feedback': 'The interview session was completed but no candidate responses were recorded for evaluation.',
                    'hiring_recommendation': 'Unable to provide recommendation due to lack of interview data.',
                    'recommendation': 'MAYBE',
                    'questions_attempted': 0,
                    'questions_correct': 0,
                    'accuracy_percentage': 0
                }
            
            print(f"🔍 DEBUG: Technical Q&A Data for LLM Analysis:")
            print(f"   Total Technical Questions Found: {len(technical_qa)}")
            for i, qa in enumerate(technical_qa, 1):
                print(f"   Q{i}: {qa['question'][:80]}...")
                print(f"   A{i}: {qa['answer'][:80]}...")
                print(f"   ---")
            
            print(f"🔍 DEBUG: Behavioral Q&A Data for LLM Analysis:")
            print(f"   Total Behavioral Questions Found: {len(behavioral_qa)}")
            for i, qa in enumerate(behavioral_qa, 1):
                print(f"   Q{i}: {qa['question'][:80]}...")
                print(f"   A{i}: {qa['answer'][:80]}...")
                print(f"   ---")
            
            print(f"🔍 DEBUG: Coding Submissions for LLM Analysis:")
            print(f"   Total Coding Challenges Found: {len(coding_submissions)}")
            for i, sub in enumerate(coding_submissions, 1):
                print(f"   Challenge {i}: {sub['question'][:80]}...")
                print(f"   Tests Passed: {sub['passed_tests']}/{sub['total_tests']}")
                print(f"   ---")

            # Build comprehensive evaluation prompt
            evaluation_prompt = self._build_evaluation_prompt(
                session=session,
                technical_qa=technical_qa,
                behavioral_qa=behavioral_qa,
                coding_submissions=coding_submissions
            )
            
            print(f"🔍 DEBUG: Full Prompt Being Sent to LLM:")
            print(f"   Prompt Length: {len(evaluation_prompt)} characters")
            print(f"   Technical Questions Section: {'=== TECHNICAL QUESTIONS & ANSWERS ===' in evaluation_prompt}")
            print(f"   Question Correctness Section: {'=== QUESTION CORRECTNESS ANALYSIS ===' in evaluation_prompt}")
            print(f"   First 500 chars of prompt: {evaluation_prompt[:500]}...")
            print(f"   ---")
            
            # Get AI evaluation
            if not self.model:
                raise Exception("Gemini model not configured. Please set GEMINI_API_KEY.")
            
            print(f"🔄 Requesting comprehensive evaluation from Gemini...")
            response = self.model.generate_content(evaluation_prompt)
            evaluation_text = response.text
            
            print(f"🔍 DEBUG: LLM Response Received:")
            print(f"   Response Length: {len(evaluation_text)} characters")
            print(f"   Contains Question Correctness Section: {'=== QUESTION CORRECTNESS ANALYSIS ===' in evaluation_text}")
            
            # Extract and show the question correctness analysis section
            correctness_section = re.search(r'=== QUESTION CORRECTNESS ANALYSIS ===(.*?)(?===|$)', evaluation_text, re.DOTALL | re.IGNORECASE)
            if correctness_section:
                correctness_text = correctness_section.group(1).strip()
                print(f"   Question Correctness Analysis Found:")
                for line in correctness_text.split('\n')[:10]:  # Show first 10 lines
                    if line.strip():
                        print(f"     {line.strip()}")
            else:
                print(f"   ⚠️ QUESTION CORRECTNESS ANALYSIS section not found in LLM response!")
            
            print(f"   ---")
            
            # Parse the response
            result = self._parse_evaluation_response(evaluation_text, technical_qa, behavioral_qa, coding_submissions)
            
            # Calculate accuracy metrics - separate for technical and overall
            technical_attempted = len(technical_qa)
            behavioral_attempted = len(behavioral_qa)
            coding_attempted = len(coding_submissions)
            total_questions = technical_attempted + behavioral_attempted + coding_attempted
            
            # Get correctness counts from parsed result
            technical_correct = result.get('technical_correct', 0)
            behavioral_correct = result.get('behavioral_correct', 0)
            coding_correct = result.get('coding_correct', 0)
            total_correct = technical_correct + behavioral_correct + coding_correct
            
            # Calculate accuracy percentages
            technical_accuracy = (technical_correct / technical_attempted * 100) if technical_attempted > 0 else 0
            behavioral_accuracy = (behavioral_correct / behavioral_attempted * 100) if behavioral_attempted > 0 else 0
            coding_accuracy = (coding_correct / coding_attempted * 100) if coding_attempted > 0 else 0
            overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
            
            # CRITICAL: Add metrics to result - use technical counts for Technical Performance Metrics
            # Frontend expects questions_attempted and questions_correct for TECHNICAL questions
            # These values come from LLM's QUESTION CORRECTNESS ANALYSIS section
            result['questions_attempted'] = technical_attempted
            result['questions_correct'] = technical_correct
            result['accuracy_percentage'] = technical_accuracy
            
            print(f"✅ LLM Analysis Results:")
            print(f"   Technical Questions Attempted: {technical_attempted}")
            print(f"   Technical Questions Correct: {technical_correct}")
            print(f"   Technical Accuracy: {technical_accuracy:.1f}%")
            print(f"   (These values come from LLM's QUESTION CORRECTNESS ANALYSIS)")
            
            # Also include separate counts for all question types
            result['technical_questions_attempted'] = technical_attempted
            result['technical_questions_correct'] = technical_correct
            result['technical_accuracy_percentage'] = technical_accuracy
            
            result['behavioral_questions_attempted'] = behavioral_attempted
            result['behavioral_questions_correct'] = behavioral_correct
            result['behavioral_accuracy_percentage'] = behavioral_accuracy
            
            result['coding_questions_attempted'] = coding_attempted
            result['coding_questions_correct'] = coding_correct
            result['coding_accuracy_percentage'] = coding_accuracy
            
            result['total_questions'] = total_questions
            result['total_correct'] = total_correct
            result['overall_accuracy_percentage'] = overall_accuracy
            
            print(f"✅ Comprehensive evaluation completed")
            print(f"   Overall Score: {result.get('overall_score', 0):.1f}/100")
            print(f"   Technical Score: {result.get('technical_score', 0):.1f}/100")
            print(f"   Coding Score: {result.get('coding_score', 0):.1f}/100")
            
            return result
            
        except InterviewSession.DoesNotExist:
            print(f"❌ Session {session_key} not found")
            raise Exception(f"Interview session {session_key} not found")
        except Exception as e:
            print(f"❌ Error in comprehensive evaluation: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _build_evaluation_prompt(self, session, technical_qa, behavioral_qa, coding_submissions) -> str:
        """Build the comprehensive evaluation prompt"""
        
        # Build Q&A transcript with proper sequence format
        qa_transcript = ""
        if technical_qa:
            qa_transcript += "\n=== Questions & Answers - Round AI Interview Technical Questions ===\n"
            qa_transcript += "\n[Exact Database Sequence - Technical Interview Performance Analysis]\n"
            for i, qa in enumerate(technical_qa, 1):
                qa_transcript += f"\nQuestion {i}: {qa['question']}\nAnswer {i}: {qa['answer']}\n"
                # Add detailed performance metrics
                qa_transcript += f"Question Level: {qa['question_level']}\n"
                if qa['response_time']:
                    qa_transcript += f"Response Time: {qa['response_time']} seconds\n"
                if qa['words_per_minute']:
                    qa_transcript += f"Speaking Rate: {qa['words_per_minute']} words per minute\n"
                if qa['filler_word_count']:
                    qa_transcript += f"Filler Words Used: {qa['filler_word_count']}\n"
                qa_transcript += f"Database Order: {qa['order']} | Sequence: {qa['conversation_sequence']}\n"
                qa_transcript += "---\n"
        
        if behavioral_qa:
            qa_transcript += "\n=== Questions & Answers - Round AI Interview Behavioral Questions ===\n"
            qa_transcript += "\n[Exact Database Sequence - Behavioral Interview Analysis]\n"
            for i, qa in enumerate(behavioral_qa, 1):
                qa_transcript += f"\nQuestion {i}: {qa['question']}\nAnswer {i}: {qa['answer']}\n"
                # Add detailed performance metrics
                qa_transcript += f"Question Level: {qa['question_level']}\n"
                if qa['response_time']:
                    qa_transcript += f"Response Time: {qa['response_time']} seconds\n"
                if qa['words_per_minute']:
                    qa_transcript += f"Speaking Rate: {qa['words_per_minute']} words per minute\n"
                if qa['filler_word_count']:
                    qa_transcript += f"Filler Words Used: {qa['filler_word_count']}\n"
                qa_transcript += f"Database Order: {qa['order']} | Sequence: {qa['conversation_sequence']}\n"
                qa_transcript += "---\n"
        
        # Build coding submissions
        coding_text = ""
        if coding_submissions:
            coding_text += "\n=== CODING CHALLENGES ===\n"
            for i, sub in enumerate(coding_submissions, 1):
                coding_text += f"\nChallenge {i}:\n"
                coding_text += f"Problem: {sub['question']}\n"
                coding_text += f"Language: {sub['language']}\n"
                coding_text += f"Tests Passed: {sub['passed_tests']}/{sub['total_tests']}\n"
                coding_text += f"Test Results: {sub['test_results']}\n"
                coding_text += f"Submitted Code:\n```\n{sub['code']}\n```\n\n"
        
        # Job description context
        job_context = session.job_description or "No job description provided"
        
        # Extract years of experience from job description or resume
        years_experience = self._extract_years_of_experience(job_context, session.resume_text or "")
        
        prompt = f"""You are an expert technical hiring manager conducting a comprehensive interview evaluation.

JOB DESCRIPTION:
{job_context[:2000]}

YEARS OF EXPERIENCE EXPECTED:
{years_experience}

CANDIDATE RESUME SUMMARY:
{session.resume_summary or 'No resume summary available.'}

INTERVIEW TRANSCRIPT:
{qa_transcript or 'No spoken questions and answers provided.'}

CODING SUBMISSIONS:
{coding_text or 'No coding challenges were part of this interview.'}

EVALUATION TASK:
Provide a comprehensive evaluation of this candidate's interview performance. Analyze:
1. Technical knowledge and problem-solving ability relative to expected experience level
2. Coding skills and code quality (if applicable) 
3. Communication and clarity of expression
4. Behavioral responses and cultural fit
5. Overall performance and potential considering years of experience

IMPORTANT: Evaluate the candidate's technical performance based on their demonstrated knowledge during the interview questions and answers. Consider:
- Depth of technical understanding shown in responses
- Problem-solving approach and methodology
- Ability to articulate complex technical concepts
- Practical application of knowledge
- Performance relative to expected experience level ({years_experience})

Provide your evaluation in this EXACT format (use the exact section headers):

=== OVERALL SCORE ===
[Provide a score from 0-100 based on overall performance]

=== TECHNICAL SCORE ===
[Provide a score from 0-100 for technical knowledge and problem-solving]

=== BEHAVIORAL SCORE ===
[Provide a score from 0-100 for behavioral responses and communication]

=== CODING SCORE ===
[Provide a score from 0-100 for coding skills. If no coding challenges, use 0]

=== COMMUNICATION SCORE ===
[Provide a score from 0-100 for communication clarity, grammar, and articulation]

=== CONFIDENCE LEVEL ===
[Provide a score from 0-100 indicating confidence in this evaluation]

=== STRENGTHS ===
- [Specific strength 1]
- [Specific strength 2]
- [Specific strength 3]

=== WEAKNESSES ===
- [Specific weakness 1]
- [Specific weakness 2]
- [Specific weakness 3]

=== TECHNICAL ANALYSIS ===
[Detailed analysis of technical performance based on the exact question-answer sequence:
- Evaluate depth of technical knowledge demonstrated in responses
- Analyze problem-solving methodology and approach
- Assess ability to articulate complex technical concepts clearly
- Consider practical application of theoretical knowledge
- Evaluate performance relative to expected experience level
- Identify specific technical strengths and areas for improvement
- Comment on accuracy and completeness of technical answers]

=== BEHAVIORAL ANALYSIS ===
[2-3 sentences analyzing communication skills, clarity, professionalism, and behavioral responses]

=== CODING ANALYSIS ===
[2-3 sentences analyzing coding skills, code quality, problem-solving approach, algorithm efficiency, and code structure. If coding challenges were provided, analyze the submitted code in detail. If no coding challenges were provided, state "No coding challenges were part of this interview."]

=== DETAILED FEEDBACK ===
[3-4 sentences providing comprehensive feedback on overall performance, highlighting key observations and areas for development]

=== HIRING RECOMMENDATION ===
[2-3 sentences providing a clear hiring recommendation with justification]

=== RECOMMENDATION ===
[One of: STRONG_HIRE, HIRE, MAYBE, NO_HIRE]

=== TECHNICAL PERFORMANCE METRICS ANALYSIS ===
Based on the exact question-answer sequence and performance data provided above, analyze:

1. **Technical Knowledge Depth**: Evaluate the depth and breadth of technical knowledge demonstrated
2. **Problem-Solving Approach**: Analyze methodology, logical thinking, and approach to technical problems
3. **Communication Clarity**: Assess ability to articulate complex technical concepts clearly and concisely
4. **Response Quality**: Evaluate accuracy, completeness, and relevance of technical answers
5. **Performance vs Experience Level**: Compare performance against expected experience level ({years_experience})
6. **Speaking Metrics**: Consider response times, speaking rates, and filler word usage patterns
7. **Question Handling**: Analyze how well the candidate handles different question types and difficulty levels

Provide specific examples from the Q&A sequence to support your analysis.

=== QUESTION CORRECTNESS ANALYSIS ===
For each technical question, evaluate if the answer is CORRECT, PARTIALLY_CORRECT, or INCORRECT.
Format: Q1: CORRECT/PARTIALLY_CORRECT/INCORRECT [Brief justification]
Q2: CORRECT/PARTIALLY_CORRECT/INCORRECT [Brief justification]
... (one line per question in order)

For coding challenges, mark as CORRECT only if all test cases passed. Otherwise mark as PARTIALLY_CORRECT or INCORRECT.

Be specific, constructive, and professional. Base your scores on the actual content provided.
"""
        return prompt
    
    def _extract_years_of_experience(self, job_description: str, resume_text: str) -> str:
        """Extract years of experience from job description and resume"""
        import re
        
        # Common patterns for years of experience
        experience_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\s*-\s*(\d+)\s*years?\s*(?:of\s*)?experience',
            r'experience\s*:\s*(\d+)\+?\s*years?',
            r'senior.*?(\d+)\+?\s*years?',
            r'junior.*?(\d+)\s*years?',
            r'mid.*?(\d+)\s*-\s*(\d+)\s*years?'
        ]
        
        # Try to extract from job description first
        for pattern in experience_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    return f"{match.group(1)}-{match.group(2)} years"
                else:
                    return f"{match.group(1)}+ years"
        
        # Try to extract from resume
        for pattern in experience_patterns:
            match = re.search(pattern, resume_text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    return f"{match.group(1)}-{match.group(2)} years"
                else:
                    return f"{match.group(1)}+ years"
        
        return "Not specified"
    
    def _parse_evaluation_response(self, response_text: str, technical_qa: list, behavioral_qa: list, coding_submissions: list) -> dict:
        """Parse the AI evaluation response into structured data"""
        
        result = {
            'overall_score': 50.0,
            'technical_score': 0,
            'behavioral_score': 0,
            'coding_score': 0,
            'communication_score': 0,
            'confidence_level': 0,
            'strengths': [],
            'weaknesses': [],
            'technical_analysis': '',
            'behavioral_analysis': '',
            'coding_analysis': '',
            'detailed_feedback': '',
            'hiring_recommendation': '',
            'recommendation': 'MAYBE',
            'technical_correct': 0,
            'behavioral_correct': 0,
            'coding_correct': 0
        }
        
        try:
            # Extract scores
            score_patterns = {
                'overall_score': r'=== OVERALL SCORE ===\s*(\d+(?:\.\d+)?)',
                'technical_score': r'=== TECHNICAL SCORE ===\s*(\d+(?:\.\d+)?)',
                'behavioral_score': r'=== BEHAVIORAL SCORE ===\s*(\d+(?:\.\d+)?)',
                'coding_score': r'=== CODING SCORE ===\s*(\d+(?:\.\d+)?)',
                'communication_score': r'=== COMMUNICATION SCORE ===\s*(\d+(?:\.\d+)?)',
                'confidence_level': r'=== CONFIDENCE LEVEL ===\s*(\d+(?:\.\d+)?)',
            }
            
            for key, pattern in score_patterns.items():
                match = re.search(pattern, response_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    result[key] = float(match.group(1))
            
            # Extract strengths (list items)
            strengths_match = re.search(r'=== STRENGTHS ===(.*?)(?=== WEAKNESSES ===|===)', response_text, re.DOTALL | re.IGNORECASE)
            if strengths_match:
                strengths_text = strengths_match.group(1).strip()
                # Extract bullet points
                strengths = [line.strip().lstrip('-•*').strip() for line in strengths_text.split('\n') if line.strip() and line.strip().startswith(('-', '•', '*'))]
                result['strengths'] = strengths if strengths else [strengths_text[:200]]
            
            # Extract weaknesses (list items)
            weaknesses_match = re.search(r'=== WEAKNESSES ===(.*?)(?=== TECHNICAL ANALYSIS ===|===)', response_text, re.DOTALL | re.IGNORECASE)
            if weaknesses_match:
                weaknesses_text = weaknesses_match.group(1).strip()
                # Extract bullet points
                weaknesses = [line.strip().lstrip('-•*').strip() for line in weaknesses_text.split('\n') if line.strip() and line.strip().startswith(('-', '•', '*'))]
                result['weaknesses'] = weaknesses if weaknesses else [weaknesses_text[:200]]
            
            # Extract analysis sections
            analysis_patterns = {
                'technical_analysis': r'=== TECHNICAL ANALYSIS ===(.*?)(?=== BEHAVIORAL ANALYSIS ===|===)', 
                'behavioral_analysis': r'=== BEHAVIORAL ANALYSIS ===(.*?)(?=== CODING ANALYSIS ===|===)',
                'coding_analysis': r'=== CODING ANALYSIS ===(.*?)(?=== DETAILED FEEDBACK ===|===)',
                'detailed_feedback': r'=== DETAILED FEEDBACK ===(.*?)(?=== HIRING RECOMMENDATION ===|===)',
                'hiring_recommendation': r'=== HIRING RECOMMENDATION ===(.*?)(?=== RECOMMENDATION ===|$)',
            }
            
            for key, pattern in analysis_patterns.items():
                match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
                if match:
                    result[key] = match.group(1).strip()
            
            # CRITICAL: If coding submissions exist but coding_analysis is empty or says "No coding challenges",
            # generate a fallback analysis from the coding submissions
            if coding_submissions and (not result.get('coding_analysis') or 
                                      'no coding challenges' in result.get('coding_analysis', '').lower()):
                print(f"⚠️ Coding submissions exist but AI didn't analyze them. Generating fallback analysis...")
                fallback_analysis = self._generate_coding_analysis_fallback(coding_submissions)
                if fallback_analysis:
                    result['coding_analysis'] = fallback_analysis
                    print(f"✅ Generated fallback coding analysis: {fallback_analysis[:100]}...")
            
            # Extract recommendation
            recommendation_match = re.search(r'=== RECOMMENDATION ===\s*(STRONG_HIRE|HIRE|MAYBE|NO_HIRE)', response_text, re.IGNORECASE)
            if recommendation_match:
                result['recommendation'] = recommendation_match.group(1).upper()
            
            # Parse question correctness analysis
            correctness_section = re.search(r'=== QUESTION CORRECTNESS ANALYSIS ===(.*?)(?===|$)', response_text, re.DOTALL | re.IGNORECASE)
            if correctness_section:
                correctness_text = correctness_section.group(1).strip()
                print(f"🔍 DEBUG: Parsing Question Correctness Analysis:")
                print(f"   Raw Correctness Text: {correctness_text[:200]}...")
                
                # Parse each line: Q1: CORRECT, Q2: INCORRECT, etc.
                correctness_lines = [line.strip() for line in correctness_text.split('\n') if line.strip() and ':' in line]
                print(f"   Parsed {len(correctness_lines)} correctness lines")
                
                # Count correct answers by category
                technical_correct = 0
                behavioral_correct = 0
                coding_correct = 0
                
                # Map question indices to categories
                question_index = 0
                
                # Technical questions
                print(f"🔍 DEBUG: Processing {len(technical_qa)} technical questions:")
                for i in range(len(technical_qa)):
                    question_index += 1
                    # Look for Q{question_index}: CORRECT or PARTIALLY_CORRECT
                    pattern = rf'Q{question_index}:\s*(CORRECT|PARTIALLY_CORRECT|INCORRECT)'
                    match = re.search(pattern, correctness_text, re.IGNORECASE)
                    if match:
                        status = match.group(1).upper()
                        print(f"   Q{question_index}: {status} -> Counting as correct")
                        # Count CORRECT and PARTIALLY_CORRECT as correct (you can adjust this)
                        if status in ['CORRECT', 'PARTIALLY_CORRECT']:
                            technical_correct += 1
                    else:
                        print(f"   Q{question_index}: NOT FOUND in correctness analysis")
                
                # Behavioral questions (continue numbering)
                print(f"🔍 DEBUG: Processing {len(behavioral_qa)} behavioral questions:")
                for i in range(len(behavioral_qa)):
                    question_index += 1
                    pattern = rf'Q{question_index}:\s*(CORRECT|PARTIALLY_CORRECT|INCORRECT)'
                    match = re.search(pattern, correctness_text, re.IGNORECASE)
                    if match:
                        status = match.group(1).upper()
                        print(f"   Q{question_index}: {status} -> Counting as correct")
                        if status in ['CORRECT', 'PARTIALLY_CORRECT']:
                            behavioral_correct += 1
                    else:
                        print(f"   Q{question_index}: NOT FOUND in correctness analysis")
                
                # Coding challenges (continue numbering)
                print(f"🔍 DEBUG: Processing {len(coding_submissions)} coding challenges:")
                for i in range(len(coding_submissions)):
                    question_index += 1
                    pattern = rf'Q{question_index}:\s*(CORRECT|PARTIALLY_CORRECT|INCORRECT)'
                    match = re.search(pattern, correctness_text, re.IGNORECASE)
                    if match:
                        status = match.group(1).upper()
                        print(f"   Q{question_index}: {status} -> Counting as correct only if CORRECT")
                        # For coding, only count CORRECT (all tests passed)
                        if status == 'CORRECT':
                            coding_correct += 1
                    else:
                        print(f"   Q{question_index}: NOT FOUND in correctness analysis")
                        # Fallback: check if all tests passed from submission data
                        if coding_submissions[i].get('passed_tests', 0) == coding_submissions[i].get('total_tests', 0) and coding_submissions[i].get('total_tests', 0) > 0:
                            coding_correct += 1
                            print(f"📋 Coding Q{question_index}: CORRECT (from test results)")
                        else:
                            print(f"⚠️ Coding Q{question_index}: Not found in correctness analysis")
                            coding_correct += 1
                
                result['technical_correct'] = technical_correct
                result['behavioral_correct'] = behavioral_correct
                result['coding_correct'] = coding_correct
                
                print(f"   Parsed correctness: Technical {technical_correct}/{len(technical_qa)}, Behavioral {behavioral_correct}/{len(behavioral_qa)}, Coding {coding_correct}/{len(coding_submissions)}")
            else:
                # Fallback: estimate from scores if correctness analysis not found
                print(f"   ⚠️ Question correctness analysis not found, estimating from scores...")
                technical_correct = self._estimate_correct_answers(result, len(technical_qa), result.get('technical_score', 0))
                behavioral_correct = self._estimate_correct_answers(result, len(behavioral_qa), result.get('behavioral_score', 0))
                coding_correct = self._estimate_correct_answers(result, len(coding_submissions), result.get('coding_score', 0))
                
                result['technical_correct'] = technical_correct
                result['behavioral_correct'] = behavioral_correct
                result['coding_correct'] = coding_correct
            
            # Fallback: if parsing failed, try to extract from unstructured text
            if result['overall_score'] == 50.0 and not result['technical_analysis']:
                # Try to find scores in any format
                overall_match = re.search(r'(?:overall|total).*?score.*?(\d+(?:\.\d+)?)', response_text, re.IGNORECASE)
                if overall_match:
                    result['overall_score'] = float(overall_match.group(1))
                
                # Use the full response as detailed feedback if parsing failed
                if len(response_text) > 100:
                    result['detailed_feedback'] = response_text[:500]
                    result['technical_analysis'] = response_text[:200]
            
        except Exception as e:
            print(f"⚠️ Error parsing evaluation response: {e}")
            import traceback
            traceback.print_exc()
            # Return default structure with response text as feedback
            result['detailed_feedback'] = response_text[:500] if response_text else 'Evaluation completed but parsing failed.'
            # Estimate correctness from scores as fallback
            result['technical_correct'] = self._estimate_correct_answers(result, len(technical_qa), result.get('technical_score', 0))
            result['behavioral_correct'] = self._estimate_correct_answers(result, len(behavioral_qa), result.get('behavioral_score', 0))
            result['coding_correct'] = self._estimate_correct_answers(result, len(coding_submissions), result.get('coding_score', 0))
        
        return result
    
    def _estimate_correct_answers(self, result: dict, total_questions: int, category_score: float = None) -> int:
        """Estimate number of correct answers based on scores"""
        if total_questions == 0:
            return 0
        
        # Use category-specific score if provided, otherwise use overall score
        if category_score is not None and category_score > 0:
            score_ratio = category_score / 100.0
        else:
            overall_score = result.get('overall_score', 50.0)
            score_ratio = overall_score / 100.0
        
        correct_count = int(score_ratio * total_questions)
        
        return max(0, min(correct_count, total_questions))
    
    def _generate_coding_analysis_fallback(self, coding_submissions: list) -> str:
        """Generate a fallback coding analysis when AI doesn't provide one"""
        if not coding_submissions:
            return "No coding challenges were part of this interview."
        
        analysis_parts = []
        total_challenges = len(coding_submissions)
        passed_challenges = sum(1 for sub in coding_submissions if sub.get('passed_all_tests', False))
        languages_used = list(set([sub.get('language', 'Unknown') for sub in coding_submissions if sub.get('language')]))
        
        analysis_parts.append(f"The candidate completed {total_challenges} coding challenge(s).")
        
        if passed_challenges > 0:
            analysis_parts.append(f"{passed_challenges} out of {total_challenges} challenge(s) passed all test cases.")
        else:
            analysis_parts.append("No challenges passed all test cases.")
        
        if languages_used:
            analysis_parts.append(f"Languages used: {', '.join(languages_used)}.")
        
        # Add details about each submission
        for i, sub in enumerate(coding_submissions, 1):
            passed = sub.get('passed_tests', 0)
            total = sub.get('total_tests', 0)
            language = sub.get('language', 'Unknown')
            if total > 0:
                analysis_parts.append(f"Challenge {i} ({language}): {passed}/{total} tests passed.")
        
        return " ".join(analysis_parts)


# Create a singleton instance for backward compatibility
comprehensive_evaluation_service = ComprehensiveEvaluationService()

