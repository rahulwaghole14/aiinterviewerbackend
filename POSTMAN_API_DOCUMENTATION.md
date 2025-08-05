# 🔐 AI Interviewer API Documentation

## 📋 Overview

This document provides comprehensive documentation for the AI Interviewer platform backend API. The API is built with Django REST Framework and provides endpoints for user authentication, job management, candidate management, resume processing, interview scheduling, and more.

## 🌐 Base URL

```
http://localhost:8000
```

## 🔑 Authentication

The API uses **Token-based authentication**. All protected endpoints require a valid authentication token in the request header.

### Authentication Header Format
```
Authorization: Token <your_auth_token>
```

## 📥 Import Instructions

1. Download the `AI_Interviewer_API_Collection.json` file
2. Open Postman
3. Click "Import" button
4. Select the downloaded JSON file
5. The collection will be imported with all endpoints and environment variables

## 🔧 Environment Variables

The collection includes the following environment variables:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `base_url` | API base URL | `http://localhost:8000` |
| `auth_token` | Authentication token | (empty) |
| `user_id` | User ID for testing | (empty) |
| `job_id` | Job ID for testing | (empty) |
| `candidate_id` | Candidate ID for testing | (empty) |
| `resume_id` | Resume ID for testing | (empty) |
| `interview_id` | Interview ID for testing | (empty) |
| `domain_id` | Domain ID for testing | (empty) |
| `company_id` | Company ID for testing | (empty) |
| `hiring_agency_id` | Hiring Agency ID for testing | (empty) |
| `recruiter_id` | Recruiter ID for testing | (empty) |
| `draft_id` | Candidate Draft ID for testing | (empty) |
| `notification_id` | Notification ID for testing | (empty) |

## 🧪 Working Test Credentials

The following credentials are ready to use for testing:

| User Type | Email | Password | Role |
|-----------|-------|----------|------|
| **Company** | `company_test@example.com` | `password123` | COMPANY |
| **Hiring Agency** | `agency_test@example.com` | `password123` | HIRING_AGENCY |
| **Recruiter** | `recruiter_test@example.com` | `password123` | RECRUITER |
| **Admin** | `admin@rslsolution.com` | `admin123` | ADMIN |

## 🔐 Authentication Endpoints

### 1. User Login
- **URL**: `POST /api/auth/login/`
- **Description**: Authenticate user and get access token
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
    "email": "company_test@example.com",
    "password": "password123"
}
```
- **Response**:
```json
{
    "token": "your_auth_token_here",
    "user": {
        "id": 1,
        "email": "company_test@example.com",
        "full_name": "Company Test User",
        "role": "COMPANY",
        "company_name": "Test Company"
    }
}
```

### 2. User Registration
- **URL**: `POST /api/auth/register/`
- **Description**: Register a new user
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
- **Note**: Username field is optional - will be auto-set to email

### 3. User Logout
- **URL**: `POST /api/auth/logout/`
- **Description**: Logout user and invalidate token
- **Headers**: `Authorization: Token <auth_token>`

## 🏢 Domain Management Endpoints

### 1. Get All Domains
- **URL**: `GET /api/jobs/domains/`
- **Description**: Retrieve all domains
- **Headers**: `Authorization: Token <auth_token>`

### 2. Get Active Domains
- **URL**: `GET /api/jobs/domains/active/`
- **Description**: Retrieve only active domains
- **Headers**: `Authorization: Token <auth_token>`

### 3. Create Domain (Admin Only)
- **URL**: `POST /api/jobs/domains/`
- **Description**: Create a new domain
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "name": "Data Science",
    "description": "Data Science and Analytics domain"
}
```

### 4. Update Domain (Admin Only)
- **URL**: `PUT /api/jobs/domains/{domain_id}/`
- **Description**: Update a domain
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "name": "Updated Data Science",
    "description": "Updated description",
    "is_active": true
}
```

### 5. Delete Domain (Admin Only)
- **URL**: `DELETE /api/jobs/domains/{domain_id}/`
- **Description**: Delete a domain
- **Headers**: `Authorization: Token <auth_token>`

## 💼 Jobs Management Endpoints

### 1. Get All Jobs
- **URL**: `GET /api/jobs/`
- **Description**: Retrieve all jobs with optional filtering
- **Headers**: `Authorization: Token <auth_token>`

### 2. Get Jobs by Domain
- **URL**: `GET /api/jobs/domain/{domain_id}/`
- **Description**: Retrieve jobs by specific domain
- **Headers**: `Authorization: Token <auth_token>`

### 3. Create Job
- **URL**: `POST /api/jobs/`
- **Description**: Create a new job posting
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "job_title": "Senior Data Scientist",
    "description": "We are looking for a senior data scientist...",
    "requirements": "Python, Machine Learning, SQL",
    "salary_range": "$80,000 - $120,000",
    "location": "Remote",
    "job_type": "FULL_TIME",
    "domain": 1,
    "company_name": "Tech Corp",
    "spoc_email": "hr@techcorp.com",
    "hiring_manager_email": "manager@techcorp.com",
    "current_team_size_info": "10-15 members",
    "number_to_hire": 2,
    "position_level": "SENIOR",
    "current_process": "Technical + Behavioral",
    "tech_stack_details": "Python, TensorFlow, SQL, AWS"
}
```

### 4. Get Job Details
- **URL**: `GET /api/jobs/{job_id}/`
- **Description**: Get detailed information about a specific job
- **Headers**: `Authorization: Token <auth_token>`

### 5. Update Job
- **URL**: `PUT /api/jobs/{job_id}/`
- **Description**: Update an existing job posting
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "job_title": "Updated Senior Data Scientist",
    "description": "Updated job description...",
    "requirements": "Updated requirements",
    "salary_range": "$90,000 - $130,000",
    "location": "Hybrid",
    "job_type": "FULL_TIME",
    "domain": 1,
    "company_name": "Tech Corp",
    "spoc_email": "hr@techcorp.com",
    "hiring_manager_email": "manager@techcorp.com",
    "current_team_size_info": "15-20 members",
    "number_to_hire": 3,
    "position_level": "SENIOR",
    "current_process": "Technical + Behavioral + Case Study",
    "tech_stack_details": "Python, TensorFlow, SQL, AWS, Kubernetes"
}
```

### 6. Delete Job
- **URL**: `DELETE /api/jobs/{job_id}/`
- **Description**: Delete a job posting
- **Headers**: `Authorization: Token <auth_token>`

## 👥 Candidates Management Endpoints

### 1. Get All Candidates
- **URL**: `GET /api/candidates/`
- **Description**: Retrieve all candidates
- **Headers**: `Authorization: Token <auth_token>`

### 2. Create Candidate (Single Step)
- **URL**: `POST /api/candidates/`
- **Description**: Create a candidate in single step
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "work_experience": 5,
    "domain": "Data Science",
    "job": 1,
    "poc_email": "john.doe@example.com"
}
```

### 3. Multi-Step Candidate Creation

#### Step 1: Select Domain & Role
- **URL**: `POST /api/candidates/select-domain/`
- **Description**: Select domain and role for candidate creation
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "domain": "Data Science",
    "role": "Data Scientist"
}
```

#### Step 2: Data Extraction
- **URL**: `POST /api/candidates/extract-data/`
- **Description**: Upload resume for data extraction
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: multipart/form-data`
- **Body**: Form data with resume file

#### Step 3: Verification
- **URL**: `POST /api/candidates/verify/{draft_id}/`
- **Description**: Verify extracted data
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "work_experience": 5
}
```

#### Step 4: Final Submission
- **URL**: `POST /api/candidates/submit/{draft_id}/`
- **Description**: Final submission to create candidate
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "confirm_submission": true
}
```

### 4. Get Candidate Details
- **URL**: `GET /api/candidates/{candidate_id}/`
- **Description**: Get detailed information about a specific candidate
- **Headers**: `Authorization: Token <auth_token>`

### 5. Update Candidate
- **URL**: `PUT /api/candidates/{candidate_id}/`
- **Description**: Update candidate information
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "full_name": "John Doe Updated",
    "email": "john.updated@example.com",
    "phone": "+1234567890",
    "work_experience": 6,
    "domain": "Data Science",
    "job": 1,
    "poc_email": "john.updated@example.com"
}
```

### 6. Delete Candidate
- **URL**: `DELETE /api/candidates/{candidate_id}/`
- **Description**: Delete a candidate
- **Headers**: `Authorization: Token <auth_token>`

## 📄 Resumes Management Endpoints

### 1. Get All Resumes
- **URL**: `GET /api/resumes/`
- **Description**: Retrieve all resumes
- **Headers**: `Authorization: Token <auth_token>`

### 2. Upload Single Resume
- **URL**: `POST /api/resumes/`
- **Description**: Upload a single resume file
- **Headers**: `Authorization: Token <auth_token>`
- **Body**: Form data with resume file

### 3. Bulk Upload Resumes
- **URL**: `POST /api/resumes/bulk-upload/`
- **Description**: Upload multiple resume files at once
- **Headers**: `Authorization: Token <auth_token>`
- **Body**: Form data with multiple resume files
- **Response Structure**:
```json
{
    "success": true,
    "message": "Bulk upload completed successfully",
    "results": [
        {
            "filename": "resume1.pdf",
            "status": "success",
            "extracted_data": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "experience": "5 years"
            }
        },
        {
            "filename": "resume2.pdf",
            "status": "success",
            "extracted_data": {
                "name": "Jane Smith",
                "email": "jane@example.com",
                "phone": "+0987654321",
                "experience": "3 years"
            }
        }
    ],
    "total_files": 2,
    "successful_uploads": 2,
    "failed_uploads": 0
}
```

### 4. Get Resume Details
- **URL**: `GET /api/resumes/{resume_id}/`
- **Description**: Get detailed information about a specific resume
- **Headers**: `Authorization: Token <auth_token>`

### 5. Delete Resume
- **URL**: `DELETE /api/resumes/{resume_id}/`
- **Description**: Delete a resume
- **Headers**: `Authorization: Token <auth_token>`

## 🎯 Interviews Management Endpoints

### 1. Get All Interviews
- **URL**: `GET /api/interviews/`
- **Description**: Retrieve all interviews
- **Headers**: `Authorization: Token <auth_token>`

### 2. Schedule Interview
- **URL**: `POST /api/interviews/`
- **Description**: Schedule a new interview
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "candidate": 1,
    "job": 1,
    "interview_round": 1,
    "started_at": "2024-01-15T10:00:00Z",
    "status": "SCHEDULED"
}
```

### 3. Get Interview Details
- **URL**: `GET /api/interviews/{interview_id}/`
- **Description**: Get detailed information about a specific interview
- **Headers**: `Authorization: Token <auth_token>`

### 4. Update Interview
- **URL**: `PUT /api/interviews/{interview_id}/`
- **Description**: Update interview information
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "status": "COMPLETED",
    "ended_at": "2024-01-15T11:00:00Z",
    "feedback": "Excellent candidate, strong technical skills"
}
```

### 5. Delete Interview
- **URL**: `DELETE /api/interviews/{interview_id}/`
- **Description**: Delete an interview
- **Headers**: `Authorization: Token <auth_token>`

### 6. Get Interview Summary
- **URL**: `GET /api/interviews/summary/`
- **Description**: Get interview summary and statistics
- **Headers**: `Authorization: Token <auth_token>`

## 📊 Dashboard & Analytics Endpoints

### 1. Get Dashboard Data
- **URL**: `GET /api/dashboard/`
- **Description**: Get comprehensive dashboard data and analytics
- **Headers**: `Authorization: Token <auth_token>`

### 2. Get User Activity
- **URL**: `GET /api/dashboard/activity/`
- **Description**: Get user activity data
- **Headers**: `Authorization: Token <auth_token>`

### 3. Get System Performance
- **URL**: `GET /api/dashboard/performance/`
- **Description**: Get system performance metrics
- **Headers**: `Authorization: Token <auth_token>`

## 🏢 Company Management Endpoints

### 1. Get All Companies
- **URL**: `GET /companies/`
- **Description**: Retrieve all companies (Admin only)
- **Headers**: `Authorization: Token <auth_token>`

### 2. Create Company
- **URL**: `POST /companies/`
- **Description**: Create a new company (Admin only)
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "name": "New Company",
    "description": "A new company description",
    "is_active": true
}
```

### 3. Get Company Details
- **URL**: `GET /companies/{company_id}/`
- **Description**: Get detailed information about a specific company
- **Headers**: `Authorization: Token <auth_token>`

### 4. Update Company
- **URL**: `PUT /companies/{company_id}/`
- **Description**: Update company information
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "name": "Updated Company Name",
    "description": "Updated company description",
    "is_active": true
}
```

### 5. Delete Company
- **URL**: `DELETE /companies/{company_id}/`
- **Description**: Delete a company (soft delete - sets is_active to False)
- **Headers**: `Authorization: Token <auth_token>`

## 👥 Hiring Agency Management Endpoints

### 1. Get All Hiring Agencies
- **URL**: `GET /hiring_agency/`
- **Description**: Retrieve all hiring agencies (filtered by company for Company users)
- **Headers**: `Authorization: Token <auth_token>`

### 2. Create Hiring Agency User
- **URL**: `POST /hiring_agency/`
- **Description**: Create a new hiring agency user (Admin/Company only)
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@agency.com",
    "phone_number": "+1234567890",
    "role": "HIRING AGENCY",
    "company_name": "Example Company",
    "linkedin_url": "https://linkedin.com/in/johndoe"
}
```

### 3. Get Hiring Agency Details
- **URL**: `GET /hiring_agency/{hiring_agency_id}/`
- **Description**: Get detailed information about a specific hiring agency
- **Headers**: `Authorization: Token <auth_token>`

### 4. Update Hiring Agency
- **URL**: `PUT /hiring_agency/{hiring_agency_id}/`
- **Description**: Update hiring agency information
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "first_name": "John",
    "last_name": "Doe Updated",
    "email": "john.updated@agency.com",
    "phone_number": "+1234567890",
    "linkedin_url": "https://linkedin.com/in/johndoeupdated"
}
```

### 5. Delete Hiring Agency
- **URL**: `DELETE /hiring_agency/{hiring_agency_id}/`
- **Description**: Delete a hiring agency user
- **Headers**: `Authorization: Token <auth_token>`

## 👨‍💼 Recruiter Management Endpoints

### 1. Get All Recruiters
- **URL**: `GET /companies/recruiters/`
- **Description**: Retrieve all recruiters (filtered by company for Company users)
- **Headers**: `Authorization: Token <auth_token>`

### 2. Create Recruiter
- **URL**: `POST /companies/recruiters/create/`
- **Description**: Create a new recruiter (Admin/Company only)
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "username": "jane.smith",
    "full_name": "Jane Smith",
    "email": "jane.smith@company.com",
    "phone": "+0987654321",
    "role": "RECRUITER",
    "company_id": 1
}
```

### 3. Get Recruiter Details
- **URL**: `GET /companies/recruiters/{recruiter_id}/`
- **Description**: Get detailed information about a specific recruiter
- **Headers**: `Authorization: Token <auth_token>`

### 4. Update Recruiter
- **URL**: `PUT /companies/recruiters/{recruiter_id}/`
- **Description**: Update recruiter information
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "full_name": "Jane Smith Updated",
    "email": "jane.updated@company.com"
}
```

### 5. Delete Recruiter
- **URL**: `DELETE /companies/recruiters/{recruiter_id}/`
- **Description**: Delete a recruiter (soft delete - sets is_active to False)
- **Headers**: `Authorization: Token <auth_token>`

## 🔔 Notifications Endpoints

### 1. Get All Notifications
- **URL**: `GET /api/notifications/`
- **Description**: Get all notifications for the current user
- **Headers**: `Authorization: Token <auth_token>`

### 2. Mark Notification as Read
- **URL**: `PATCH /api/notifications/{notification_id}/`
- **Description**: Mark a notification as read
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "is_read": true
}
```

### 3. Mark Notification as Read (Alternative)
- **URL**: `POST /api/notifications/mark-read/`
- **Description**: Mark a notification as read using notification ID in body
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "notification_id": 1
}
```

### 4. Bulk Mark Notifications as Read
- **URL**: `POST /api/notifications/bulk-mark-read/`
- **Description**: Mark multiple notifications as read
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "notification_ids": [1, 2, 3]
}
```

### 5. Get Notification Summary
- **URL**: `GET /api/notifications/summary/`
- **Description**: Get notification summary and statistics
- **Headers**: `Authorization: Token <auth_token>`

### 6. Get Unread Notifications Count
- **URL**: `GET /api/notifications/unread-count/`
- **Description**: Get count of unread notifications
- **Headers**: `Authorization: Token <auth_token>`

### 7. Get Notification Preferences
- **URL**: `GET /api/notifications/preferences/`
- **Description**: Get user notification preferences
- **Headers**: `Authorization: Token <auth_token>`

### 8. Update Notification Preferences
- **URL**: `PUT /api/notifications/preferences/`
- **Description**: Update user notification preferences
- **Headers**: `Authorization: Token <auth_token>`, `Content-Type: application/json`
- **Body**:
```json
{
    "email_enabled": true,
    "in_app_enabled": true,
    "sms_enabled": false,
    "interview_notifications": true,
    "resume_notifications": true,
    "system_notifications": true,
    "daily_digest": false,
    "weekly_summary": true
}
```

## 🧪 Testing Workflow

### 1. Setup Environment
1. Import the Postman collection
2. Set the `base_url` variable to your server URL
3. Ensure the server is running

### 2. Authentication
1. Use the "User Login" endpoint with one of the test credentials
2. Copy the token from the response
3. The token will be automatically set in the `auth_token` variable

### 3. Test Endpoints
1. Start with simple GET requests to verify authentication
2. Test CRUD operations for each module
3. Use the multi-step candidate creation process
4. Test bulk resume upload functionality

## 📊 Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

## ⚠️ Error Handling

The API returns detailed error messages in JSON format:

```json
{
    "error": "Error message",
    "details": "Additional error details"
}
```

## 🚀 Rate Limiting

- **Authentication endpoints**: 100 requests per hour
- **Other endpoints**: 1000 requests per hour
- **Bulk upload**: 10 requests per hour

## 📁 File Upload Limits

- **Single file**: Maximum 10MB
- **Bulk upload**: Maximum 10 files per request
- **Supported formats**: PDF, DOCX, DOC

## 🔒 Security Features

- **Password Hashing**: PBKDF2 with SHA256 (industry standard)
- **Token Authentication**: Secure token-based authentication
- **CORS Protection**: Configured for frontend integration
- **Input Validation**: Comprehensive request validation
- **SQL Injection Protection**: Django ORM protection

## 📞 Support

For technical support or questions about the API:
- Check the server logs for detailed error information
- Verify authentication token is valid
- Ensure all required fields are provided in requests
- Test with the provided working credentials first

## 🔄 Auto-Token Management

The Postman collection includes automatic token management:
- Login responses automatically set the `auth_token` variable
- All subsequent requests use the stored token
- No manual token copying required

---

**🎉 Happy Testing! Use the provided working credentials to explore all API features.** 