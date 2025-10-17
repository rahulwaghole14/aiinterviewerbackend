# Talaro Interview Integration Guide

## Overview

This guide explains how to integrate your Talaro interview model into the Django backend. The system provides a complete Talaro interview management solution with session tracking, question generation, response evaluation, and result analysis.

## Architecture

### 🔧 **Core Components**

1. **AI Interview Models** (`ai_interview/models.py`)
   - `AIInterviewSession`: Manages interview sessions
   - `AIInterviewQuestion`: Stores generated questions
   - `AIInterviewResponse`: Tracks candidate responses
   - `AIInterviewResult`: Final interview results

2. **AI Interview Service** (`ai_interview/services.py`)
   - `AIInterviewService`: Main service class for AI operations
   - Handles question generation, response evaluation, and result calculation

3. **API Endpoints** (`ai_interview/views.py`)
   - RESTful endpoints for session management
   - Public endpoints for candidate access
   - Admin endpoints for result review

## 🚀 **Integration Steps**

### Step 1: Configure AI Model Settings

Add your AI model configuration to `ai_platform/settings.py`:

```python
# AI Interview Model Configuration
AI_MODEL_NAME = config('AI_MODEL_NAME', default='your_model_name')
AI_MODEL_VERSION = config('AI_MODEL_VERSION', default='1.0')
AI_MODEL_API_ENDPOINT = config('AI_MODEL_API_ENDPOINT', default='https://your-ai-model-api.com')
AI_MODEL_API_KEY = config('AI_MODEL_API_KEY', default='your_api_key')
```

### Step 2: Integrate Your AI Model

Replace the placeholder methods in `ai_interview/services.py`:

#### A. Question Generation
```python
def _call_external_ai_model(self, context: Dict) -> List[Dict]:
    """
    Call your AI model to generate questions
    """
    import requests
    
    payload = {
        'context': context,
        'model_name': self.model_name,
        'model_version': self.model_version
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {self.api_key}'
    }
    
    response = requests.post(
        f"{self.api_endpoint}/generate-questions",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json().get('questions', [])
    else:
        logger.error(f"AI model API error: {response.status_code} - {response.text}")
        return self._generate_fallback_questions(context)
```

#### B. Response Evaluation
```python
def _call_external_ai_evaluation(self, question: AIInterviewQuestion, response_text: str) -> Dict:
    """
    Call your AI model to evaluate responses
    """
    import requests
    
    payload = {
        'question': question.question_text,
        'response': response_text,
        'question_type': question.question_type,
        'difficulty': question.difficulty,
        'context': question.question_context
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {self.api_key}'
    }
    
    response = requests.post(
        f"{self.api_endpoint}/evaluate-response",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"AI evaluation API error: {response.status_code} - {response.text}")
        return self._generate_mock_evaluation(question, response_text)
```

### Step 3: Expected AI Model API Format

#### Question Generation Endpoint
**URL**: `POST /generate-questions`

**Request**:
```json
{
    "context": {
        "candidate_name": "John Doe",
        "candidate_domain": "Python Development",
        "job_title": "Senior Python Developer",
        "company_name": "Tech Corp",
        "interview_type": "technical",
        "difficulty_level": "medium",
        "question_count": 10,
        "time_limit": 60
    },
    "model_name": "your_model_name",
    "model_version": "1.0"
}
```

**Response**:
```json
{
    "questions": [
        {
            "type": "technical",
            "difficulty": "medium",
            "question": "Explain the difference between REST and GraphQL APIs.",
            "context": {
                "topic": "API Design",
                "category": "Web Development"
            },
            "prompt": "Generate a technical question about API design"
        }
    ]
}
```

#### Response Evaluation Endpoint
**URL**: `POST /evaluate-response`

**Request**:
```json
{
    "question": "Explain the difference between REST and GraphQL APIs.",
    "response": "REST uses multiple endpoints while GraphQL uses a single endpoint...",
    "question_type": "technical",
    "difficulty": "medium",
    "context": {
        "topic": "API Design",
        "category": "Web Development"
    }
}
```

**Response**:
```json
{
    "score": 85,
    "feedback": "Excellent explanation of the key differences",
    "confidence": 0.92,
    "ai_response": "Thank you for your detailed response. You correctly identified the main differences between REST and GraphQL.",
    "response_time": 2.1
}
```

## 📡 **API Endpoints**

### Public Endpoints (No Authentication Required)

#### 1. Start AI Interview Session
**URL**: `POST /api/ai-interview/start/`

**Request**:
```json
{
    "interview_id": "uuid-of-interview"
}
```

**Response**:
```json
{
    "session_id": "uuid-of-session",
    "interview_id": "uuid-of-interview",
    "candidate_name": "John Doe",
    "job_title": "Senior Python Developer",
    "ai_interview_type": "technical",
    "total_questions": 10,
    "status": "created",
    "message": "AI interview session created successfully"
}
```

#### 2. Main AI Interview Run Endpoint
**URL**: `POST /api/ai-interview/run-interview/`

**Request**:
```json
{
    "action": "start|question|response|complete",
    "session_id": "uuid-of-session",
    "data": {
        // Additional data based on action
    }
}
```

**Actions**:

##### Start Interview
```json
{
    "action": "start",
    "session_id": "uuid-of-session"
}
```

##### Get Next Question
```json
{
    "action": "question",
    "session_id": "uuid-of-session"
}
```

##### Submit Response
```json
{
    "action": "response",
    "session_id": "uuid-of-session",
    "data": {
        "question_id": "uuid-of-question",
        "response_text": "Candidate's answer here",
        "response_type": "text",
        "response_data": {}
    }
}
```

##### Complete Interview
```json
{
    "action": "complete",
    "session_id": "uuid-of-session"
}
```

### Admin Endpoints (Authentication Required)

#### 1. Session Management
- `GET /api/ai-interview/sessions/` - List all sessions
- `GET /api/ai-interview/sessions/{id}/` - Get session details
- `POST /api/ai-interview/sessions/{id}/start_interview/` - Start session
- `POST /api/ai-interview/sessions/{id}/get_next_question/` - Get next question
- `POST /api/ai-interview/sessions/{id}/submit_response/` - Submit response
- `POST /api/ai-interview/sessions/{id}/complete_session/` - Complete session

#### 2. Results Management
- `GET /api/ai-interview/results/` - List all results
- `GET /api/ai-interview/results/{id}/` - Get result details
- `POST /api/ai-interview/results/{id}/add_human_review/` - Add human review

## 🔄 **Interview Flow**

### 1. Candidate Access Flow
```
1. Candidate clicks interview link
2. System validates link and creates AI session
3. Candidate starts interview via /api/ai-interview/run-interview/
4. AI generates questions based on job requirements
5. Candidate answers questions one by one
6. AI evaluates each response in real-time
7. System generates final results and recommendations
```

### 2. Admin Review Flow
```
1. Admin views interview results
2. Reviews AI-generated scores and feedback
3. Adds human review and final rating
4. Makes hiring decision based on combined AI + human evaluation
```

## 🛠 **Deployment on Render**

### 1. Environment Variables
Add these to your Render environment:

```bash
AI_MODEL_NAME=your_model_name
AI_MODEL_VERSION=1.0
AI_MODEL_API_ENDPOINT=https://your-ai-model-api.com
AI_MODEL_API_KEY=your_api_key
```

### 2. Model Integration Options

#### Option A: External AI Model API
- Deploy your AI model separately (e.g., on Render, AWS, GCP)
- Configure the API endpoint in Django settings
- Django calls your AI model via HTTP requests

#### Option B: Integrated AI Model
- Add your AI model code directly to the Django project
- Install required dependencies (tensorflow, pytorch, etc.)
- Update Render build configuration for larger instances

### 3. Render Configuration

#### Build Command
```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
```

#### Start Command
```bash
gunicorn ai_platform.wsgi:application
```

#### Environment Variables
```bash
AI_MODEL_NAME=your_model_name
AI_MODEL_VERSION=1.0
AI_MODEL_API_ENDPOINT=https://your-ai-model-api.com
AI_MODEL_API_KEY=your_api_key
INTERVIEW_LINK_SECRET=your-secret-key
FRONTEND_URL=https://your-frontend-url.com
```

## 📊 **Data Models**

### AIInterviewSession
```python
{
    'id': 'uuid',
    'interview': 'OneToOneField to Interview',
    'status': 'active|paused|completed|error',
    'model_name': 'string',
    'model_version': 'string',
    'ai_configuration': 'JSON',
    'current_question_index': 'integer',
    'total_questions': 'integer',
    'session_started_at': 'datetime',
    'session_ended_at': 'datetime',
    'session_duration': 'integer (seconds)',
    'response_time_avg': 'float',
    'questions_answered': 'integer'
}
```

### AIInterviewQuestion
```python
{
    'id': 'uuid',
    'session': 'ForeignKey to AIInterviewSession',
    'question_index': 'integer',
    'question_type': 'technical|behavioral|coding|system_design|general',
    'difficulty': 'easy|medium|hard',
    'question_text': 'text',
    'question_context': 'JSON',
    'ai_model_prompt': 'text',
    'ai_model_response': 'text',
    'question_asked_at': 'datetime',
    'response_received_at': 'datetime',
    'response_time': 'float',
    'is_answered': 'boolean',
    'is_correct': 'boolean',
    'score': 'float (0-100)',
    'ai_feedback': 'text',
    'human_feedback': 'text'
}
```

### AIInterviewResult
```python
{
    'id': 'uuid',
    'session': 'OneToOneField to AIInterviewSession',
    'interview': 'OneToOneField to Interview',
    'total_score': 'float (0-100)',
    'technical_score': 'float (0-100)',
    'behavioral_score': 'float (0-100)',
    'coding_score': 'float (0-100)',
    'questions_attempted': 'integer',
    'questions_correct': 'integer',
    'average_response_time': 'float',
    'completion_time': 'integer (seconds)',
    'ai_summary': 'text',
    'ai_recommendations': 'text',
    'strengths': 'JSON array',
    'weaknesses': 'JSON array',
    'overall_rating': 'excellent|good|average|poor|pending',
    'hire_recommendation': 'boolean',
    'confidence_level': 'float (0-100)',
    'human_reviewer': 'ForeignKey to CustomUser',
    'human_rating': 'string',
    'human_feedback': 'text',
    'reviewed_at': 'datetime'
}
```

## 🔍 **Testing**

### 1. Test AI Interview Flow
```bash
# Start Django server
python manage.py runserver

# Test interview link access
curl -X POST http://localhost:8000/api/ai-interview/start/ \
  -H "Content-Type: application/json" \
  -d '{"interview_id": "your-interview-uuid"}'

# Test question generation
curl -X POST http://localhost:8000/api/ai-interview/run-interview/ \
  -H "Content-Type: application/json" \
  -d '{"action": "start", "session_id": "your-session-uuid"}'
```

### 2. Mock AI Model Testing
The system includes mock implementations for testing:
- Mock question generation based on interview type
- Mock response evaluation based on response length
- Fallback questions when AI model is unavailable

## 🚨 **Error Handling**

### 1. AI Model Unavailable
- System falls back to mock questions and evaluations
- Logs errors for monitoring
- Continues interview flow without interruption

### 2. Network Issues
- Retry logic for API calls
- Timeout handling (30 seconds default)
- Graceful degradation to mock responses

### 3. Invalid Responses
- Validation of AI model responses
- Fallback to default questions/evaluations
- Error logging for debugging

## 📈 **Monitoring and Analytics**

### 1. Logging
All AI interview operations are logged:
- Session creation and completion
- Question generation and response submission
- AI model API calls and responses
- Error conditions and fallbacks

### 2. Metrics
Track key performance indicators:
- Average response times
- Question completion rates
- AI model accuracy vs human reviews
- Session success rates

## 🔐 **Security Considerations**

### 1. API Key Management
- Store AI model API keys in environment variables
- Never commit keys to version control
- Use secure key rotation practices

### 2. Data Privacy
- Candidate responses are stored securely
- Implement data retention policies
- Ensure GDPR compliance for personal data

### 3. Access Control
- Public endpoints for candidate access
- Authenticated endpoints for admin operations
- Role-based permissions for different user types

## 🎯 **Next Steps**

1. **Integrate Your AI Model**: Replace mock implementations with your actual AI model
2. **Configure API Endpoints**: Set up your AI model API endpoints
3. **Test End-to-End Flow**: Verify the complete interview process
4. **Deploy to Render**: Deploy the updated backend with AI integration
5. **Monitor Performance**: Track AI model performance and accuracy
6. **Iterate and Improve**: Refine questions and evaluation based on results

---

*This integration provides a complete AI interview solution that can be deployed on Render with your custom AI model. The system is designed to be scalable, secure, and maintainable.*

