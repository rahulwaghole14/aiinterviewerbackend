# Talaro Interview Link Generation Guide

## Overview

The AI Interview Link Generation system provides a secure, token-based approach for candidates to access AI-powered interviews without requiring authentication. This system integrates with the existing interview management infrastructure and provides a seamless experience for both administrators and candidates.

## Features

### 🔐 Secure Link Generation
- **HMAC-based token generation** for security
- **Time-limited access** (2 hours after interview end)
- **Interview window validation** (15 minutes before to 2 hours after)
- **Automatic expiration** handling

### 🤖 AI Interview Integration
- **Automatic AI session creation** when generating links
- **AI question generation** based on job description and resume
- **Real-time AI evaluation** of candidate responses
- **Comprehensive feedback** and scoring

### 📱 Public Access
- **No authentication required** for candidates
- **Mobile-friendly** interface
- **Real-time interaction** with Talaro interviewer
- **Progress tracking** and completion status

## API Endpoints

### 1. Generate AI Interview Link
**POST** `/api/ai-interview/generate-link/{interview_id}/`

Generates a new secure AI interview link for the specified interview.

**Request:**
```json
{
  "interview_id": "uuid"
}
```

**Response:**
```json
{
  "interview_id": "uuid",
  "link_token": "base64-encoded-token",
  "ai_interview_url": "https://example.com/api/ai-interview/public/start/",
  "public_interview_url": "https://example.com/api/interviews/public/{token}/",
  "expires_at": "2024-01-15T14:30:00Z",
  "ai_session_id": "uuid",
  "ai_interview_type": "technical",
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  "job_title": "Software Engineer",
  "message": "AI interview link generated successfully"
}
```

### 2. Get AI Interview Link
**GET** `/api/ai-interview/get-link/{interview_id}/`

Retrieves existing AI interview link information.

**Response:**
```json
{
  "interview_id": "uuid",
  "link_token": "base64-encoded-token",
  "ai_interview_url": "https://example.com/api/ai-interview/public/start/",
  "public_interview_url": "https://example.com/api/interviews/public/{token}/",
  "expires_at": "2024-01-15T14:30:00Z",
  "ai_session_id": "uuid",
  "ai_interview_type": "technical",
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  "job_title": "Software Engineer",
  "questions_generated": 5,
  "is_expired": false,
  "message": "AI interview link retrieved successfully"
}
```

### 3. Regenerate AI Interview Link
**POST** `/api/ai-interview/regenerate-link/{interview_id}/`

Regenerates a new AI interview link, invalidating the old one.

**Response:**
```json
{
  "interview_id": "uuid",
  "link_token": "new-base64-encoded-token",
  "ai_interview_url": "https://example.com/api/ai-interview/public/start/",
  "public_interview_url": "https://example.com/api/interviews/public/{new-token}/",
  "expires_at": "2024-01-15T14:30:00Z",
  "ai_session_id": "uuid",
  "ai_interview_type": "technical",
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  "job_title": "Software Engineer",
  "message": "AI interview link regenerated successfully"
}
```

## Public AI Interview Endpoints

### 1. Start AI Interview
**POST** `/api/ai-interview/public/start/`

Starts an AI interview session using the link token.

**Request:**
```json
{
  "interview_id": "uuid",
  "link_token": "base64-encoded-token"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "interview_id": "uuid",
  "candidate_name": "John Doe",
  "job_title": "Software Engineer",
  "ai_interview_type": "technical",
  "current_question": "Tell me about your experience with Python development.",
  "questions": [
    {
      "id": "uuid",
      "text": "Tell me about your experience with Python development.",
      "type": "technical",
      "order": 1,
      "audio_url": "/media/tts/q_0_session_id.mp3"
    }
  ],
  "total_questions": 5,
  "status": "started",
  "message": "Interview started successfully"
}
```

### 2. Submit Response
**POST** `/api/ai-interview/public/submit-response/`

Submits a candidate's response to the current question.

**Request:**
```json
{
  "session_id": "uuid",
  "link_token": "base64-encoded-token",
  "response_text": "I have 3 years of experience with Python..."
}
```

**Response:**
```json
{
  "response_id": "uuid",
  "current_question_id": "uuid",
  "next_question": "What design patterns have you implemented?",
  "feedback": "Great answer! You clearly understand Python fundamentals.",
  "next_instruction": "Please proceed to the next question.",
  "message": "Response submitted successfully"
}
```

### 3. Complete Interview
**POST** `/api/ai-interview/public/complete/`

Completes the AI interview and generates evaluation.

**Request:**
```json
{
  "session_id": "uuid",
  "link_token": "base64-encoded-token"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "evaluation": "Overall, you demonstrated strong technical knowledge...",
  "score": 85,
  "total_questions": 5,
  "answered_questions": 5,
  "strengths": "Strong problem-solving skills, good communication",
  "areas_for_improvement": "Consider more specific examples",
  "recommendation": "Yes",
  "status": "completed",
  "message": "Interview completed successfully"
}
```

## Usage Examples

### Python Script Example

```python
import requests

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Login
login_data = {"email": "admin@example.com", "password": "admin123"}
response = requests.post(f"{API_BASE}/auth/login/", json=login_data)
token = response.json().get('access')
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Generate AI interview link
interview_id = "your-interview-uuid"
response = requests.post(
    f"{API_BASE}/ai-interview/generate-link/{interview_id}/", 
    headers=headers
)

if response.status_code == 200:
    link_data = response.json()
    print(f"AI Interview URL: {link_data['public_interview_url']}")
    print(f"Link Token: {link_data['link_token']}")
```

### JavaScript Example

```javascript
// Generate AI interview link
async function generateAIInterviewLink(interviewId) {
    const response = await fetch(`/api/ai-interview/generate-link/${interviewId}/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });
    
    if (response.ok) {
        const linkData = await response.json();
        return linkData.public_interview_url;
    }
}

// Start AI interview (public endpoint)
async function startAIInterview(interviewId, linkToken) {
    const response = await fetch('/api/ai-interview/public/start/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            interview_id: interviewId,
            link_token: linkToken
        })
    });
    
    if (response.ok) {
        const sessionData = await response.json();
        return sessionData;
    }
}
```

## Security Features

### Token Generation
- Uses HMAC-SHA256 for secure token generation
- Includes interview ID and candidate email in token data
- Base64 URL-safe encoding for web compatibility

### Access Control
- Tokens are tied to specific interviews
- Automatic expiration after interview window
- Validation of interview timing (15 minutes before to 2 hours after)

### Data Protection
- No sensitive data exposed in tokens
- Server-side validation of all requests
- Audit logging of link generation and usage

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "error": "Interview must have a scheduled start time to generate AI interview link"
}
```

**401 Unauthorized:**
```json
{
  "error": "Invalid interview token"
}
```

**404 Not Found:**
```json
{
  "error": "No interview link found for this interview"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Failed to generate AI interview link: [error details]"
}
```

## Testing

### Quick Test Script
Run the included test script to verify functionality:

```bash
python quick_ai_interview_link.py
```

### Comprehensive Test
For full system testing:

```bash
python test_ai_interview_link_generation.py
```

## Integration with Frontend

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

const AIInterviewLinkGenerator = ({ interviewId }) => {
    const [linkData, setLinkData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const generateLink = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`/api/ai-interview/generate-link/${interviewId}/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                setLinkData(data);
            } else {
                const errorData = await response.json();
                setError(errorData.error);
            }
        } catch (err) {
            setError('Failed to generate link');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="ai-interview-link-generator">
            <button 
                onClick={generateLink} 
                disabled={loading}
                className="btn btn-primary"
            >
                {loading ? 'Generating...' : 'Generate AI Interview Link'}
            </button>
            
            {error && (
                <div className="alert alert-danger">{error}</div>
            )}
            
            {linkData && (
                <div className="link-details">
                    <h4>AI Interview Link Generated</h4>
                    <p><strong>Candidate:</strong> {linkData.candidate_name}</p>
                    <p><strong>Job:</strong> {linkData.job_title}</p>
                    <p><strong>Expires:</strong> {new Date(linkData.expires_at).toLocaleString()}</p>
                    
                    <div className="link-urls">
                        <label>Public Interview URL:</label>
                        <input 
                            type="text" 
                            value={linkData.public_interview_url} 
                            readOnly 
                            className="form-control"
                        />
                        <button 
                            onClick={() => navigator.clipboard.writeText(linkData.public_interview_url)}
                            className="btn btn-secondary btn-sm"
                        >
                            Copy URL
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AIInterviewLinkGenerator;
```

## Best Practices

### For Administrators
1. **Generate links early** - Create links well before the interview time
2. **Monitor usage** - Track link generation and usage patterns
3. **Regenerate when needed** - Use regeneration for security or technical issues
4. **Test thoroughly** - Verify links work before sending to candidates

### For Candidates
1. **Use the link promptly** - Links expire after the interview window
2. **Prepare environment** - Ensure stable internet and quiet environment
3. **Follow instructions** - Read all provided guidance before starting
4. **Complete fully** - Finish all questions for best evaluation

### For Developers
1. **Handle errors gracefully** - Implement proper error handling
2. **Validate inputs** - Always validate interview IDs and tokens
3. **Log activities** - Maintain audit trails for security
4. **Test edge cases** - Test expiration, invalid tokens, etc.

## Troubleshooting

### Common Issues

**Link not working:**
- Check if interview has a start time
- Verify link hasn't expired
- Ensure interview is configured for AI interview type

**Questions not generating:**
- Check AI service configuration
- Verify job description and resume data
- Review server logs for AI service errors

**Authentication errors:**
- Verify admin credentials
- Check token expiration
- Ensure proper authorization headers

### Debug Steps
1. Check server logs for detailed error messages
2. Verify interview configuration in admin panel
3. Test API endpoints individually
4. Validate token format and expiration
5. Check AI service connectivity

## Support

For technical support or questions about the AI Interview Link Generation system:

1. Check the server logs for detailed error information
2. Review the API documentation for endpoint details
3. Test with the provided test scripts
4. Contact the development team with specific error messages

---

**Last Updated:** January 2024  
**Version:** 1.0  
**Author:** AI Interview System Team

