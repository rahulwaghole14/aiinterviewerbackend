"""
Gemini API-based Dynamic Coding Question Generator
Generates coding questions, test cases, and evaluations using Google's Gemini API
"""

import google.generativeai as genai
import json
import re
from typing import List, Dict, Any, Optional

# Configure Gemini API
from django.conf import settings
if getattr(settings, 'GEMINI_API_KEY', ''):
    genai.configure(api_key=settings.GEMINI_API_KEY)

def get_coding_questions_from_gemini(job_title: str, domain_name: str = None, language_preference: str = None) -> List[Dict[str, Any]]:
    """
    Generate coding questions using Gemini API based on job profile
    
    Args:
        job_title (str): The job title from the Job model
        domain_name (str): The domain name (optional)
        language_preference (str): Preferred programming language
    
    Returns:
        list: List of coding question dictionaries with test cases
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Determine appropriate programming language based on job profile
        if not language_preference:
            language_preference = get_appropriate_language(job_title, domain_name)
        
        # Create comprehensive prompt for question generation
        prompt = f"""
        You are an expert technical interviewer. Generate 2 coding questions for a {job_title} position.
        
        Job Context:
        - Job Title: {job_title}
        - Domain: {domain_name or 'General'}
        - Preferred Language: {language_preference}
        
        Requirements:
        1. Generate 2 coding questions that are relevant to this role
        2. Each question should test practical skills needed for this position
        3. Include comprehensive test cases (3-5 test cases per question)
        4. Provide starter code with proper function signatures
        5. Make questions challenging but fair for the experience level
        
        For each question, provide:
        - title: Clear, descriptive title
        - description: Detailed problem statement with examples
        - language: Programming language to use
        - starter_code: Complete function skeleton with docstrings
        - test_cases: Array of test cases with input and expected output
        - difficulty: Easy/Medium/Hard
        - time_limit: Suggested time in minutes
        
        Return the response as a JSON array with this exact structure:
        [
            {{
                "id": "question_1",
                "type": "CODING",
                "title": "Question Title",
                "description": "Detailed description with examples",
                "language": "{language_preference}",
                "difficulty": "Medium",
                "time_limit": 15,
                "starter_code": "def function_name():\n    # Your code here\n    pass",
                "test_cases": [
                    {{
                        "input": "input_value",
                        "output": "expected_output",
                        "description": "Test case description"
                    }}
                ]
            }}
        ]
        
        Focus on practical, real-world problems that a {job_title} would encounter.
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up the response to extract JSON
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        # Parse JSON response
        questions_data = json.loads(response_text)
        
        # Validate and format the questions
        formatted_questions = []
        for i, question in enumerate(questions_data):
            formatted_question = {
                'id': f'gemini_question_{i+1}',
                'type': 'CODING',
                'title': question.get('title', f'Coding Question {i+1}'),
                'description': question.get('description', ''),
                'language': question.get('language', language_preference),
                'difficulty': question.get('difficulty', 'Medium'),
                'time_limit': question.get('time_limit', 15),
                'starter_code': question.get('starter_code', ''),
                'test_cases': question.get('test_cases', [])
            }
            formatted_questions.append(formatted_question)
        
        return formatted_questions
        
    except Exception as e:
        print(f"Error generating questions with Gemini: {e}")
        # Fallback to static questions
        return get_fallback_questions(job_title, language_preference)


def generate_test_cases_with_gemini(question_description: str, starter_code: str, language: str) -> List[Dict[str, Any]]:
    """
    Generate additional test cases using Gemini API
    
    Args:
        question_description (str): The question description
        starter_code (str): The starter code
        language (str): Programming language
    
    Returns:
        list: List of test cases
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Generate comprehensive test cases for this coding question:
        
        Question: {question_description}
        Language: {language}
        Starter Code: {starter_code}
        
        Generate 5-7 test cases that cover:
        1. Basic functionality
        2. Edge cases
        3. Boundary conditions
        4. Error handling
        5. Performance considerations
        
        Return as JSON array:
        [
            {{
                "input": "input_value",
                "output": "expected_output",
                "description": "Test case description",
                "type": "basic|edge|boundary|error|performance"
            }}
        ]
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        test_cases = json.loads(response_text)
        return test_cases
        
    except Exception as e:
        print(f"Error generating test cases with Gemini: {e}")
        return []


def evaluate_code_with_gemini(code: str, question_description: str, test_cases: List[Dict], language: str) -> Dict[str, Any]:
    """
    Evaluate code execution results using Gemini API
    
    Args:
        code (str): The submitted code
        question_description (str): The question description
        test_cases (list): List of test cases with results
        language (str): Programming language
    
    Returns:
        dict: Evaluation results
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Format test case results
        test_results = []
        for i, test_case in enumerate(test_cases):
            test_results.append({
                'test_case': i + 1,
                'input': test_case.get('input', ''),
                'expected': test_case.get('output', ''),
                'actual': test_case.get('actual_output', ''),
                'passed': test_case.get('passed', False),
                'description': test_case.get('description', '')
            })
        
        prompt = f"""
        Evaluate this code submission for a coding interview:
        
        Question: {question_description}
        Language: {language}
        
        Submitted Code:
        {code}
        
        Test Results:
        {json.dumps(test_results, indent=2)}
        
        Provide a comprehensive evaluation including:
        1. Code correctness (0-100)
        2. Code quality (0-100)
        3. Algorithm efficiency (0-100)
        4. Code style and readability (0-100)
        5. Overall score (0-100)
        6. Detailed feedback
        7. Suggestions for improvement
        8. Strengths and weaknesses
        
        Return as JSON:
        {{
            "correctness_score": 85,
            "quality_score": 80,
            "efficiency_score": 75,
            "style_score": 90,
            "overall_score": 82,
            "feedback": "Detailed feedback here",
            "suggestions": ["Suggestion 1", "Suggestion 2"],
            "strengths": ["Strength 1", "Strength 2"],
            "weaknesses": ["Weakness 1", "Weakness 2"],
            "recommendation": "HIRE|NO_HIRE|STRONG_HIRE|STRONG_NO_HIRE"
        }}
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        evaluation = json.loads(response_text)
        return evaluation
        
    except Exception as e:
        print(f"Error evaluating code with Gemini: {e}")
        return {
            "correctness_score": 0,
            "quality_score": 0,
            "efficiency_score": 0,
            "style_score": 0,
            "overall_score": 0,
            "feedback": f"Error in evaluation: {str(e)}",
            "suggestions": [],
            "strengths": [],
            "weaknesses": [],
            "recommendation": "NO_HIRE"
        }


def get_appropriate_language(job_title: str, domain_name: str = None) -> str:
    """
    Determine appropriate programming language based on job profile
    
    Args:
        job_title (str): Job title
        domain_name (str): Domain name
    
    Returns:
        str: Recommended programming language
    """
    # Handle None values
    if job_title is None:
        job_title = ""
    if domain_name is None:
        domain_name = ""
    
    job_lower = job_title.lower()
    domain_lower = domain_name.lower()
    
    # Data Science / ML roles
    if any(keyword in job_lower for keyword in ['data scientist', 'data science', 'ml engineer', 'machine learning', 'data analyst']):
        return 'PYTHON'
    
    # Backend / Server roles
    elif any(keyword in job_lower for keyword in ['backend', 'api', 'server', 'java', 'spring']):
        return 'JAVA'
    
    # Frontend roles
    elif any(keyword in job_lower for keyword in ['frontend', 'front-end', 'ui', 'ux', 'react', 'angular', 'vue']):
        return 'JAVASCRIPT'
    
    # Mobile development
    elif any(keyword in job_lower for keyword in ['mobile', 'android', 'ios', 'flutter', 'react native']):
        return 'JAVA'  # or 'SWIFT' for iOS
    
    # DevOps / Infrastructure
    elif any(keyword in job_lower for keyword in ['devops', 'sre', 'site reliability', 'infrastructure']):
        return 'PYTHON'
    
    # Database / Data Engineering
    elif any(keyword in job_lower for keyword in ['database', 'data engineer', 'dba', 'sql']):
        return 'SQL'
    
    # Full-stack / General
    elif any(keyword in job_lower for keyword in ['full stack', 'full-stack', 'software engineer', 'developer']):
        return 'PYTHON'  # Default to Python for general roles
    
    # Default
    else:
        return 'PYTHON'


def get_fallback_questions(job_title: str, language: str = 'PYTHON') -> List[Dict[str, Any]]:
    """
    Fallback questions when Gemini API fails
    
    Args:
        job_title (str): Job title
        language (str): Programming language
    
    Returns:
        list: Fallback questions
    """
    # Handle None values
    if job_title is None:
        job_title = ""
    
    if any(keyword in job_title.lower() for keyword in ['data scientist', 'data science', 'ml engineer', 'machine learning']):
        questions = []
        
        # Question 1: Pandas Data Analysis
        questions.append({
            'id': 'fallback_ds_1',
            'type': 'CODING',
            'title': 'Pandas Data Analysis - Top Users by Spending',
            'description': 'Given a dataset of user transactions, find the top 5 users by total spending using pandas.',
            'language': 'PYTHON',
            'difficulty': 'Medium',
            'time_limit': 15,
            'starter_code': '''import pandas as pd

def find_top_users_by_spending(transactions):
    """
    Find the top 5 users by total spending
    
    Args:
        transactions (pd.DataFrame): DataFrame with columns ['user_id', 'amount', 'date']
    
    Returns:
        pd.DataFrame: Top 5 users with their total spending
    """
    # Your code here
    pass''',
            'test_cases': [
                {
                    'input': 'pd.DataFrame({"user_id": [1, 1, 2, 2, 3], "amount": [100, 200, 150, 300, 50]})',
                    'output': 'user_id  total_spending\n1        300\n2        450\n3        50',
                    'description': 'Basic test case'
                }
            ]
        })
        
        # Question 2: Missing Values Analysis
        questions.append({
            'id': 'fallback_ds_2',
            'type': 'CODING',
            'title': 'Data Cleaning - Missing Values Analysis',
            'description': 'Write a function that analyzes missing values in a DataFrame and returns a summary of missing values per column.',
            'language': 'PYTHON',
            'difficulty': 'Easy',
            'time_limit': 10,
            'starter_code': '''import pandas as pd

def analyze_missing_values(df):
    """
    Analyze missing values in a DataFrame
    
    Args:
        df (pd.DataFrame): Input DataFrame
    
    Returns:
        pd.DataFrame: Summary of missing values per column
    """
    # Your code here
    pass''',
            'test_cases': [
                {
                    'input': 'pd.DataFrame({"A": [1, 2, None, 4], "B": [None, 2, 3, None], "C": [1, 2, 3, 4]})',
                    'output': 'Column  Missing_Count  Missing_Percentage\nA       1              25.0\nB       2              50.0\nC       0              0.0',
                    'description': 'Basic missing values analysis'
                }
            ]
        })
        
        # Question 3: Data Aggregation
        questions.append({
            'id': 'fallback_ds_3',
            'type': 'CODING',
            'title': 'Data Aggregation - Sales Analysis',
            'description': 'Given a sales DataFrame, calculate the total sales by month and find the month with the highest sales.',
            'language': 'PYTHON',
            'difficulty': 'Medium',
            'time_limit': 15,
            'starter_code': '''import pandas as pd

def analyze_sales_by_month(sales_df):
    """
    Analyze sales by month and find the best performing month
    
    Args:
        sales_df (pd.DataFrame): DataFrame with columns ['date', 'amount']
    
    Returns:
        tuple: (monthly_sales_df, best_month)
    """
    # Your code here
    pass''',
            'test_cases': [
                {
                    'input': 'pd.DataFrame({"date": ["2023-01-01", "2023-01-15", "2023-02-01", "2023-02-15"], "amount": [100, 200, 150, 300]})',
                    'output': 'Month  Total_Sales\n1      300\n2      450',
                    'description': 'Basic sales aggregation'
                }
            ]
        })
        
        return questions
    else:
        # Generate multiple coding questions based on job title
        questions = []
        
        # Question 1: String manipulation (always include)
        questions.append({
            'id': 'fallback_general_1',
            'type': 'CODING',
            'title': 'String Processing',
            'description': 'Write a function that reverses a string. For example, if the input is "hello", the output should be "olleh".',
            'language': language,
            'difficulty': 'Easy',
            'time_limit': 10,
            'starter_code': f'''def reverse_string(s):
    """
    Reverse a string
    
    Args:
        s (str): Input string
    
    Returns:
        str: Reversed string
    """
    # Your code here
    pass''',
            'test_cases': [
                {
                    'input': '"hello"',
                    'output': 'olleh',
                    'description': 'Basic string reversal'
                },
                {
                    'input': '"world"',
                    'output': 'dlrow',
                    'description': 'Another string reversal'
                },
                {
                    'input': '""',
                    'output': '""',
                    'description': 'Empty string'
                }
            ]
        })
        
        # Question 2: Array/List manipulation
        questions.append({
            'id': 'fallback_general_2',
            'type': 'CODING',
            'title': 'Array Processing',
            'description': 'Write a function that finds the maximum element in a list of integers. If the list is empty, return None.',
            'language': language,
            'difficulty': 'Easy',
            'time_limit': 10,
            'starter_code': f'''def find_maximum(numbers):
    """
    Find the maximum element in a list
    
    Args:
        numbers (list): List of integers
    
    Returns:
        int or None: Maximum element or None if list is empty
    """
    # Your code here
    pass''',
            'test_cases': [
                {
                    'input': '[1, 5, 3, 9, 2]',
                    'output': '9',
                    'description': 'Basic maximum finding'
                },
                {
                    'input': '[-1, -5, -3]',
                    'output': '-1',
                    'description': 'Negative numbers'
                },
                {
                    'input': '[]',
                    'output': 'None',
                    'description': 'Empty list'
                }
            ]
        })
        
        # Question 3: Algorithm problem (for more technical roles)
        if any(keyword in job_title.lower() for keyword in ['developer', 'engineer', 'programmer', 'software']):
            questions.append({
                'id': 'fallback_general_3',
                'type': 'CODING',
                'title': 'Algorithm Challenge',
                'description': 'Write a function that checks if a string is a palindrome (reads the same forwards and backwards). Ignore case and non-alphanumeric characters.',
                'language': language,
                'difficulty': 'Medium',
                'time_limit': 15,
                'starter_code': f'''def is_palindrome(s):
    """
    Check if a string is a palindrome
    
    Args:
        s (str): Input string
    
    Returns:
        bool: True if palindrome, False otherwise
    """
    # Your code here
    pass''',
                'test_cases': [
                    {
                        'input': '"A man a plan a canal Panama"',
                        'output': 'True',
                        'description': 'Palindrome with spaces and mixed case'
                    },
                    {
                        'input': '"race a car"',
                        'output': 'False',
                        'description': 'Not a palindrome'
                    },
                    {
                        'input': '"Madam"',
                        'output': 'True',
                        'description': 'Simple palindrome'
                    }
                ]
            })
        
        return questions


def validate_gemini_response(response_text: str) -> bool:
    """
    Validate that Gemini response contains valid JSON
    
    Args:
        response_text (str): Response text from Gemini
    
    Returns:
        bool: True if valid JSON, False otherwise
    """
    try:
        # Clean up response
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        json.loads(response_text)
        return True
    except:
        return False
