"""
Coding Round Service with Gemini-based evaluation
Integrates with the existing interview system
"""
import os
import json
import subprocess
import tempfile
import google.generativeai as genai
from django.conf import settings

# Configure Gemini
GEMINI_API_KEY = "AIzaSyBU4ZmzsBdCUGlHg4eZCednvOwL4lqDVtw"
genai.configure(api_key=GEMINI_API_KEY)


def generate_coding_questions_with_testcases(job_description: str, num_questions: int = 2):
    """
    Generate coding questions with test cases using Gemini AI
    Uses the EXACT prompt from interview_app_11/gemini_question_generator.py
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Extract job title from JD
        job_title = "Technical Role"
        if "AI/ML Intern" in job_description or "Machine Learning" in job_description:
            job_title = "AI/ML Intern"
        elif "Python" in job_description or "Django" in job_description:
            job_title = "Python Developer"
        elif "JavaScript" in job_description or "React" in job_description:
            job_title = "Full Stack Developer"
        
        # Enhanced prompt that uses the FULL JD to generate relevant questions
        prompt = f"""
        You are an expert technical interviewer. Generate {num_questions} coding questions based on this job description.
        
        JOB DESCRIPTION:
        {job_description[:2000]}
        
        Job Title: {job_title}
        Preferred Language: PYTHON
        
        Requirements:
        1. Generate {num_questions} coding questions that are DIRECTLY RELEVANT to the skills and responsibilities in the JD above
        2. Focus on the technical skills, tools, and concepts mentioned in the job description
        3. Each question should test practical skills needed for this specific position
        4. Include comprehensive test cases (3-5 test cases per question)
        5. Make questions challenging but appropriate for the experience level mentioned in the JD
        
        For AI/ML roles, focus on:
        - Data manipulation and preprocessing (lists, arrays, transformations)
        - Statistical calculations (mean, median, variance, normalization)
        - Algorithm implementation (sorting, searching, optimization)
        - Mathematical operations (linear algebra, probability)
        - Data structure design (for model storage, caching, etc.)
        
        For each question, provide:
        - title: Clear, descriptive title
        - description: Detailed problem statement with examples
        - language: Programming language to use (PYTHON)
        - starter_code: Complete function or class skeleton with docstrings
        - test_cases: Array of test cases with input and expected output
        - difficulty: Easy/Medium/Hard (based on JD experience level)
        - time_limit: Suggested time in minutes
        
        Return the response as a JSON array with this exact structure:
        [
            {{
                "id": "question_1",
                "type": "CODING",
                "title": "Question Title",
                "description": "Detailed description with examples",
                "language": "PYTHON",
                "difficulty": "Medium",
                "time_limit": 15,
                "starter_code": "def function_name(param):\\n    # Your code here\\n    pass",
                "test_cases": [
                    {{
                        "input": "input_value",
                        "output": "expected_output",
                        "description": "Test case description"
                    }}
                ]
            }}
        ]
        
        IMPORTANT: Generate questions that directly test the skills mentioned in the job description.
        Return ONLY the JSON array, no other text.
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        print(f"📥 Gemini response (first 500 chars):\n{response_text[:500]}\n")
        
        # Clean up response - EXACT LOGIC from gemini_question_generator.py
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Handle both array and object formats
        if response_text.startswith('['):
            # Direct array format
            questions_data = json.loads(response_text)
        elif response_text.startswith('{'):
            # Object format with "questions" key
            parsed = json.loads(response_text)
            questions_data = parsed.get('questions', [])
        else:
            raise Exception("Response is neither array nor object")
        
        print(f"✅ Parsed {len(questions_data)} questions from Gemini")
        
        # Convert to our format
        formatted_questions = []
        for question in questions_data:
            formatted_question = {
                'title': question.get('title', 'Coding Question'),
                'description': question.get('description', ''),
                'language': question.get('language', 'PYTHON'),
                'difficulty': question.get('difficulty', 'Medium'),
                'test_cases': []
            }
            
            # Extract test cases
            for tc in question.get('test_cases', []):
                formatted_question['test_cases'].append({
                    'input': tc.get('input', ''),
                    'expected_output': tc.get('output', tc.get('expected_output', ''))
                })
            
            formatted_questions.append(formatted_question)
        
        return formatted_questions
        
    except Exception as e:
        print(f"❌ Error generating coding questions: {e}")
        import traceback
        traceback.print_exc()
        
        # Try again with simpler prompt
        try:
            print("🔄 Retrying with simplified prompt...")
            model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Same model, simpler prompt
            
            simple_prompt = f"""
            Based on this job description, create {num_questions} Python coding problems.
            
            JOB DESCRIPTION:
            {job_description[:1500]}
            
            IMPORTANT: Generate coding questions that test the SPECIFIC SKILLS mentioned in the job description above.
            - For AI/ML roles: focus on data manipulation, statistical calculations, algorithm implementation
            - For Web Dev roles: focus on APIs, databases, data processing
            - For general roles: focus on algorithms and data structures mentioned in the JD
            
            Return ONLY valid JSON in this exact format:
            {{
                "questions": [
                    {{
                        "title": "Problem Name",
                        "description": "Clear problem statement with example",
                        "language": "PYTHON",
                        "difficulty": "Medium",
                        "test_cases": [
                            {{"input": "input1", "expected_output": "output1"}},
                            {{"input": "input2", "expected_output": "output2"}},
                            {{"input": "input3", "expected_output": "output3"}}
                        ]
                    }}
                ]
            }}
            """
            
            response = model.generate_content(simple_prompt)
            response_text = response.text.strip()
            
            # Extract JSON
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            import re
            json_match = re.search(r'\{[\s\S]*"questions"[\s\S]*\}', response_text)
            if json_match:
                response_text = json_match.group(0)
            
            questions_data = json.loads(response_text)
            print(f"✅ Retry successful! Generated {len(questions_data.get('questions', []))} questions")
            return questions_data.get('questions', [])
            
        except Exception as retry_error:
            print(f"❌ Retry also failed: {retry_error}")
            # Re-raise to prevent silent failure
            raise Exception(f"Failed to generate coding questions after retry: {retry_error}")


def execute_python_code(code: str, test_input: str = None):
    """
    Execute Python code safely with test input
    Returns: (stdout, stderr, passed)
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Add test input handling if provided
            if test_input:
                code_with_input = f"""
{code}

# Test execution
if __name__ == "__main__":
    test_input = {repr(test_input)}
    result = solution(test_input) if 'solution' in dir() else None
    print(result if result is not None else '')
"""
            else:
                code_with_input = code
            
            f.write(code_with_input)
            temp_file = f.name
        
        # Execute the code
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=5  # 5 second timeout
        )
        
        # Clean up
        os.unlink(temp_file)
        
        return result.stdout.strip(), result.stderr.strip(), result.returncode == 0
        
    except subprocess.TimeoutExpired:
        return "", "Execution timed out (5 seconds)", False
    except Exception as e:
        return "", f"Execution error: {str(e)}", False


def evaluate_code_with_testcases(code: str, test_cases: list, language: str = "PYTHON"):
    """
    Evaluate code against multiple test cases
    Returns: (passed_count, total_count, results)
    """
    results = []
    passed_count = 0
    
    for i, test_case in enumerate(test_cases):
        test_input = test_case.get('input')
        expected_output = str(test_case.get('expected_output')).strip()
        
        stdout, stderr, success = execute_python_code(code, test_input)
        
        if stderr:
            results.append({
                'test_case': i + 1,
                'input': test_input,
                'expected': expected_output,
                'actual': stderr,
                'passed': False,
                'error': True
            })
        else:
            actual_output = stdout.strip()
            passed = (actual_output == expected_output)
            if passed:
                passed_count += 1
            
            results.append({
                'test_case': i + 1,
                'input': test_input,
                'expected': expected_output,
                'actual': actual_output,
                'passed': passed,
                'error': False
            })
    
    return passed_count, len(test_cases), results


def evaluate_code_with_gemini(code: str, question: str, test_results: list):
    """
    Get AI feedback on code quality using Gemini
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Prepare test results summary
        passed_tests = sum(1 for r in test_results if r['passed'])
        total_tests = len(test_results)
        
        prompt = f"""
        You are an expert code reviewer. Evaluate the following code submission:
        
        Problem: {question}
        
        Submitted Code:
        ```python
        {code}
        ```
        
        Test Results: {passed_tests}/{total_tests} tests passed
        
        Provide:
        1. Code Quality Score (0-100)
        2. Strengths (2-3 points)
        3. Areas for Improvement (2-3 points)
        4. Overall Feedback (2-3 sentences)
        
        Format as:
        Score: [0-100]
        Strengths:
        - [strength 1]
        - [strength 2]
        Areas for Improvement:
        - [improvement 1]
        - [improvement 2]
        Feedback: [overall feedback]
        """
        
        response = model.generate_content(prompt)
        feedback_text = response.text
        
        # Parse the response
        import re
        score_match = re.search(r"Score:\s*(\d+)", feedback_text)
        score = int(score_match.group(1)) if score_match else 50
        
        return {
            'score': score,
            'feedback': feedback_text,
            'passed_tests': passed_tests,
            'total_tests': total_tests
        }
        
    except Exception as e:
        print(f"❌ Error evaluating code with Gemini: {e}")
        return {
            'score': 50,
            'feedback': f"Code evaluation completed. {passed_tests}/{total_tests} tests passed.",
            'passed_tests': passed_tests,
            'total_tests': total_tests
        }


def generate_comprehensive_feedback(qa_transcript: list, coding_results: list):
    """
    Generate comprehensive interview feedback combining Q&A and coding
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Prepare Q&A summary
        qa_summary = "\n".join([
            f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}"
            for item in qa_transcript[:5]  # Limit to first 5 Q&A
        ])
        
        # Prepare coding summary
        coding_summary = "\n".join([
            f"Problem: {result.get('question', '')}\nScore: {result.get('score', 0)}/100\nTests Passed: {result.get('passed_tests', 0)}/{result.get('total_tests', 0)}"
            for result in coding_results
        ])
        
        prompt = f"""
        You are an expert technical interviewer providing final evaluation.
        
        Technical Q&A Summary:
        {qa_summary}
        
        Coding Challenge Summary:
        {coding_summary}
        
        Provide a comprehensive evaluation:
        1. Overall Score (0-100)
        2. Technical Knowledge Assessment
        3. Coding Skills Assessment
        4. Key Strengths
        5. Areas for Development
        6. Final Recommendation (Strong Hire / Hire / Maybe / No Hire)
        
        Keep it professional and constructive.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"❌ Error generating comprehensive feedback: {e}")
        return "Interview completed successfully. Detailed evaluation will be provided separately."

