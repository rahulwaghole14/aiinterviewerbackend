# AI Interviewer API - Postman Documentation

## Overview
This document provides comprehensive documentation for the AI Interviewer platform API. The API is built with Django REST Framework and supports role-based access control with the following hierarchy:

- **ADMIN**: Full access to all data and operations
- **COMPANY**: Access to own data + agencies/recruiters under them
- **HIRING_AGENCY**: Own data, upload resumes, schedule interviews, check results
- **RECRUITER**: Own data, upload resumes, schedule interviews, check results

## Base URL
```
http://localhost:8000
```

## Authentication
The API uses Token-based authentication. Include the token in the Authorization header:
```
Authorization: Token <your_token_here>
```

## Import Instructions
1. Download the `AI_Interviewer_API_Collection.json` file
2. Open Postman
3. Click "Import" and select the JSON file
4. Set up environment variables (see Environment Variables section)

## Environment Variables
Set up these variables in your Postman environment:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `base_url` | API base URL | `http://localhost:8000` |
| `auth_token` | Authentication token | (auto-filled after login) |
| `job_id` | Job ID for testing | (auto-filled after job creation) |
| `candidate_id` | Candidate ID for testing | (auto-filled after candidate creation) |
| `resume_id` | Resume ID for testing | (auto-filled after resume upload) |
| `interview_id` | Interview ID for testing | (auto-filled after interview creation) |
| `draft_id` | Candidate draft ID | (auto-filled after draft creation) |
| `notification_id` | Notification ID | (auto-filled after notification creation) |

---

## API Endpoints

### 1. Authentication

#### 1.1 User Login
- **URL**: `{{base_url}}/api/auth/login/`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
    "email": "admin@rslsolution.com",
    "password": "admin123"
}
```
- **Response**: Returns user data and authentication token
- **Notes**: Use the returned token for subsequent requests

#### 1.2 User Registration
- **URL**: `{{base_url}}/api/auth/register/`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
    "email": "newuser@example.com",
    "password": "password123",
    "full_name": "New User",
    "role": "HIRING_AGENCY",
    "company_name": "Example Company"
}
```

#### 1.3 User Logout
- **URL**: `{{base_url}}/api/auth/logout/`
- **Method**: `POST`
- **Headers**: `Authorization: Token {{auth_token}}`

---

### 2. Jobs Management

#### 2.1 Get All Jobs
- **URL**: `{{base_url}}/api/jobs/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`
- **Query Parameters**:
  - `search`: Search by job title or company
  - `domain`: Filter by domain
  - `status`: Filter by status

#### 2.2 Get Single Job
- **URL**: `{{base_url}}/api/jobs/{{job_id}}/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`

#### 2.3 Create New Job
- **URL**: `{{base_url}}/api/jobs/`
- **Method**: `POST`
- **Headers**: 
  - `Authorization: Token {{auth_token}}`
  - `Content-Type: application/json`
- **Body**:
```json
{
    "job_title": "Senior Software Engineer",
    "company_name": "Tech Corp",
    "spoc_email": "hr@techcorp.com",
    "hiring_manager_email": "manager@techcorp.com",
    "current_team_size_info": "15 developers",
    "number_to_hire": 2,
    "position_level": "Senior",
    "work_experience": "5-8 years",
    "tech_stack_details": "Python, Django, React, AWS",
    "jd_link": "https://example.com/jd"
}
```

#### 2.4 Update Job
- **URL**: `{{base_url}}/api/jobs/{{job_id}}/`
- **Method**: `PUT`
- **Headers**: 
  - `Authorization: Token {{auth_token}}`
  - `Content-Type: application/json`

#### 2.5 Delete Job
- **URL**: `{{base_url}}/api/jobs/{{job_id}}/`
- **Method**: `DELETE`
- **Headers**: `Authorization: Token {{auth_token}}`

#### 2.6 Get Domains
- **URL**: `{{base_url}}/api/jobs/domains/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`

#### 2.7 Create Domain (Admin Only)
- **URL**: `{{base_url}}/api/jobs/domains/`
- **Method**: `POST`
- **Headers**: 
  - `Authorization: Token {{auth_token}}`
  - `Content-Type: application/json`
- **Body**:
```json
{
    "name": "Machine Learning",
    "description": "Machine Learning and AI related jobs"
}
```

---

### 3. Candidates Management

#### 3.1 Get All Candidates
- **URL**: `{{base_url}}/api/candidates/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`

#### 3.2 Get Single Candidate
- **URL**: `{{base_url}}/api/candidates/{{candidate_id}}/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`

#### 3.3 Create Candidate (Single Step)
- **URL**: `{{base_url}}/api/candidates/`
- **Method**: `POST`
- **Headers**: 
  - `Authorization: Token {{auth_token}}`
  - `Content-Type: application/json`
- **Body**:
```json
{
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone_number": "+1234567890",
    "domain": "Software Development",
    "experience_years": 5,
    "current_company": "Tech Corp",
    "current_role": "Senior Developer",
    "expected_salary": 80000,
    "notice_period": 30
}
```

#### 3.4 Multi-Step Candidate Creation

##### Step 1: Create Candidate Draft
- **URL**: `{{base_url}}/api/candidates/create-draft/`
- **Method**: `POST`
- **Headers**: 
  - `Authorization: Token {{auth_token}}`
  - `Content-Type: application/json`
- **Body**:
```json
{
    "domain": "Software Development",
    "role": "Senior Developer"
}
```

##### Step 2: Update Candidate Draft
- **URL**: `{{base_url}}/api/candidates/drafts/{{draft_id}}/`
- **Method**: `PUT`
- **Headers**: 
  - `Authorization: Token {{auth_token}}`
  - `Content-Type: application/json`
- **Body**:
```json
{
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone_number": "+1234567890",
    "experience_years": 5,
    "current_company": "Tech Corp",
    "current_role": "Senior Developer",
    "expected_salary": 80000,
    "notice_period": 30
}
```

##### Step 3: Submit Candidate Draft
- **URL**: `{{base_url}}/api/candidates/drafts/{{draft_id}}/submit/`
- **Method**: `POST`
- **Headers**: `Authorization: Token {{auth_token}}`

#### 3.5 Update Candidate
- **URL**: `{{base_url}}/api/candidates/{{candidate_id}}/`
- **Method**: `PUT`
- **Headers**: 
  - `Authorization: Token {{auth_token}}`
  - `Content-Type: application/json`

#### 3.6 Delete Candidate
- **URL**: `{{base_url}}/api/candidates/{{candidate_id}}/`
- **Method**: `DELETE`
- **Headers**: `Authorization: Token {{auth_token}}`

---

### 4. Resume Management

#### 4.1 Get All Resumes
- **URL**: `{{base_url}}/api/resumes/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`

#### 4.2 Get Single Resume
- **URL**: `{{base_url}}/api/resumes/{{resume_id}}/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`

#### 4.3 Upload Single Resume
- **URL**: `{{base_url}}/api/resumes/`
- **Method**: `POST`
- **Headers**: `Authorization: Token {{auth_token}}`
- **Body**: `form-data`
  - `file`: Resume file (PDF/DOCX)

#### 4.4 Bulk Upload Resumes
- **URL**: `{{base_url}}/api/resumes/bulk-upload/`
- **Method**: `POST`
- **Headers**: `Authorization: Token {{auth_token}}`
- **Body**: `form-data`
  - `files`: Multiple resume files (up to 10 files)
- **Response Structure**:
```json
{
    "success": true,
    "message": "Bulk upload completed successfully",
    "total_files": 3,
    "successful_uploads": 2,
    "failed_uploads": 1,
    "results": [
        {
            "filename": "resume1.pdf",
            "status": "success",
            "resume_id": 123,
            "extracted_data": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "experience": "5 years"
            }
        },
        {
            "filename": "resume2.pdf",
            "status": "failed",
            "error": "Invalid file format"
        }
    ]
}
```

#### 4.5 Delete Resume
- **URL**: `{{base_url}}/api/resumes/{{resume_id}}/`
- **Method**: `DELETE`
- **Headers**: `Authorization: Token {{auth_token}}`

---

### 5. Interviews Management

#### 5.1 Get All Interviews
- **URL**: `{{base_url}}/api/interviews/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`

#### 5.2 Get Single Interview
- **URL**: `{{base_url}}/api/interviews/{{interview_id}}/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`

#### 5.3 Create Interview
- **URL**: `{{base_url}}/api/interviews/`
- **Method**: `POST`
- **Headers**: 
  - `Authorization: Token {{auth_token}}`
  - `Content-Type: application/json`
- **Body**:
```json
{
    "candidate": 1,
    "job": 1,
    "started_at": "2024-08-15T10:00:00Z",
    "ended_at": "2024-08-15T11:00:00Z",
    "interview_round": 1,
    "status": "scheduled"
}
```

#### 5.4 Update Interview
- **URL**: `{{base_url}}/api/interviews/{{interview_id}}/`
- **Method**: `PUT`
- **Headers**: 
  - `Authorization: Token {{auth_token}}`
  - `Content-Type: application/json`
- **Body**:
```json
{
    "candidate": 1,
    "job": 1,
    "started_at": "2024-08-15T14:00:00Z",
    "ended_at": "2024-08-15T15:00:00Z",
    "interview_round": 1,
    "status": "completed",
    "feedback": "Great technical skills, good communication"
}
```

#### 5.5 Delete Interview
- **URL**: `{{base_url}}/api/interviews/{{interview_id}}/`
- **Method**: `DELETE`
- **Headers**: `Authorization: Token {{auth_token}}`

---

### 6. Dashboard & Analytics

#### 6.1 Get Dashboard Data
- **URL**: `{{base_url}}/api/dashboard/data/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`
- **Query Parameters**:
  - `start_date`: Start date (YYYY-MM-DD)
  - `end_date`: End date (YYYY-MM-DD)
- **Response**: Comprehensive dashboard data including metrics, charts, and analytics

#### 6.2 Get Dashboard Summary
- **URL**: `{{base_url}}/api/dashboard/summary/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`
- **Response**: Summary statistics and key metrics

#### 6.3 Get User Activity
- **URL**: `{{base_url}}/api/dashboard/activity/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`
- **Response**: User activity logs and recent actions

---

### 7. Notifications

#### 7.1 Get Notifications
- **URL**: `{{base_url}}/api/notifications/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`
- **Query Parameters**:
  - `unread_only`: Filter unread notifications only
  - `type`: Filter by notification type

#### 7.2 Mark Notification as Read
- **URL**: `{{base_url}}/api/notifications/{{notification_id}}/mark-read/`
- **Method**: `POST`
- **Headers**: `Authorization: Token {{auth_token}}`

#### 7.3 Get Notification Summary
- **URL**: `{{base_url}}/api/notifications/summary/`
- **Method**: `GET`
- **Headers**: `Authorization: Token {{auth_token}}`
- **Response**: Unread count and notification statistics

#### 7.4 Update Notification Preferences
- **URL**: `{{base_url}}/api/notifications/preferences/`
- **Method**: `PUT`
- **Headers**: 
  - `Authorization: Token {{auth_token}}`
  - `Content-Type: application/json`
- **Body**:
```json
{
    "email_notifications": true,
    "in_app_notifications": true,
    "sms_notifications": false
}
```

---

## Testing Workflow

### 1. Initial Setup
1. Import the Postman collection
2. Set up environment variables
3. Run the "User Login" request to get authentication token
4. The token will be automatically saved to the `auth_token` variable

### 2. Basic CRUD Testing
1. **Create**: Use POST requests to create resources
2. **Read**: Use GET requests to retrieve resources
3. **Update**: Use PUT requests to modify resources
4. **Delete**: Use DELETE requests to remove resources

### 3. Multi-Step Candidate Flow Testing
1. Create a candidate draft
2. Update the draft with extracted data
3. Submit the draft to create the final candidate
4. Schedule an interview for the candidate

### 4. Bulk Operations Testing
1. Upload multiple resume files
2. Check the response for successful and failed uploads
3. Verify extracted data from resumes

---

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

## Error Handling

All API responses follow a consistent error format:
```json
{
    "error": "Error message",
    "details": "Additional error details"
}
```

## Rate Limiting

- Authentication endpoints: 5 requests per minute
- Other endpoints: 100 requests per minute
- Bulk upload: 10 files per request

## File Upload Limits

- Single file: 10MB
- Supported formats: PDF, DOCX
- Bulk upload: Maximum 10 files per request

---

## Support

For API support or questions:
- Check the Django admin interface for data management
- Review server logs for detailed error information
- Ensure proper authentication and permissions

## Version Information

- API Version: 1.0
- Django Version: 4.2+
- DRF Version: 3.14+
- Last Updated: August 2024 