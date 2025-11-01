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
    Execute Python code safely with test input.
    Handles both function-based and class-based code.
    Returns: (stdout, stderr, passed)
    """
    import re
    
    try:
        # Check if code contains a class definition (for OOP questions)
        class_match = re.search(r'class\s+(\w+)', code)
        
        if class_match and test_input:
            # Class-based code: test_input should be executable Python code
            # Example: "finder = MedianFinder(); finder.addNum(1); finder.findMedian()"
            # Split by semicolon, execute all but last, then print the result of the last
            statements = [s.strip() for s in test_input.split(';') if s.strip()]
            if len(statements) > 1:
                # Execute all statements except the last
                setup = '\n'.join(statements[:-1])
                # Print the result of the last statement
                full_script = f"{code}\n{setup}\nprint({statements[-1]})"
            else:
                # Single statement - just execute and print
                full_script = f"{code}\nprint({test_input})"
        elif test_input:
            # Function-based code: find function name and call it
            function_match = re.search(r'def\s+(\w+)\s*\(', code)
            if function_match:
                function_name = function_match.group(1)
                full_script = f"{code}\nprint({function_name}({test_input}))"
            else:
                # Fallback to 'solution' or 'solve' function
                full_script = f"{code}\nresult = solution({test_input}) if 'solution' in dir() else solve({test_input})\nprint(result)"
        else:
            # No test input - just execute the code
            full_script = code
        
        # Execute using python -c for faster execution
        result = subprocess.run(
            ['python', '-c', full_script],
            capture_output=True,
            text=True,
            timeout=5  # 5 second timeout
        )
        
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
        
        # Prepare detailed test results
        test_details = ""
        for i, result in enumerate(test_results[:5]):  # Show first 5 test cases
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            test_details += f"\nTest Case {result['test_case']}: {status}\n"
            test_details += f"  Input: {result['input']}\n"
            test_details += f"  Expected: {result['expected']}\n"
            test_details += f"  Actual: {result['actual']}\n"
            if result.get('error'):
                test_details += f"  Error: Yes\n"
        
        prompt = f"""
        You are an expert code reviewer and technical interviewer. Evaluate this coding challenge submission:
        
        PROBLEM STATEMENT:
        {question[:500]}
        
        SUBMITTED CODE:
        ```python
        {code}
        ```
        
        TEST RESULTS: {passed_tests}/{total_tests} tests passed
        {test_details}
        
        EVALUATION CRITERIA:
        1. Correctness: Does it solve the problem? Are test cases passing?
        2. Code Quality: Clean, readable, well-structured code?
        3. Efficiency: Time and space complexity appropriate?
        4. Error Handling: Edge cases handled?
        5. Best Practices: Follows Python conventions?
        
        Provide a comprehensive evaluation in this EXACT format:
        
        Score: [0-100]
        
        Strengths:
        - [specific strength 1]
        - [specific strength 2]
        - [specific strength 3 if applicable]
        
        Areas for Improvement:
        - [specific improvement 1]
        - [specific improvement 2]
        - [specific improvement 3 if applicable]
        
        Feedback: [2-3 sentences of overall assessment focusing on correctness, code quality, and approach]
        
        Be specific and constructive. If test cases failed, explain WHY and how to fix it.
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

