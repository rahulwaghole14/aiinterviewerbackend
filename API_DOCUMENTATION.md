# AI Interviewer Platform - API Documentation

## 🚀 Overview
This platform provides comprehensive AI-powered interviewing capabilities including resume processing, job management, interview scheduling, and hiring agency management.

## 📋 Available Endpoints

### 🔐 Authentication
All endpoints require authentication using Token Authentication.
```
Authorization: Token your-auth-token-here
```

---

## 📄 Resume Processing APIs

### 1. Bulk Resume Upload
**POST** `/api/resumes/bulk-upload/`

Upload multiple resumes (up to 10 files) simultaneously with concurrent processing.

**Request:**
```bash
curl -X POST http://localhost:8000/api/resumes/bulk-upload/ \
  -H "Authorization: Token your-token" \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.docx" \
  -F "files=@resume3.pdf"
```

**Response:**
```json
{
  "message": "Processed 3 resumes: 2 successful, 1 failed",
  "results": [
    {
      "success": true,
      "filename": "john_doe.pdf",
      "resume_id": "uuid-here",
      "extracted_data": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "work_experience": 5
      }
    },
    {
      "success": false,
      "filename": "invalid.txt",
      "error_message": "Unsupported file type. Only PDF, DOCX, and DOC files are allowed."
    }
  ],
  "summary": {
    "total_files": 3,
    "successful": 2,
    "failed": 1
  }
}
```

### 2. Single Resume Upload
**POST** `/api/resumes/`

Upload a single resume file.

**Request:**
```bash
curl -X POST http://localhost:8000/api/resumes/ \
  -H "Authorization: Token your-token" \
  -F "file=@resume.pdf"
```

**Response:**
```json
{
  "id": "uuid-here",
  "file": "/media/resumes/resume.pdf",
  "parsed_text": "Extracted text content...",
  "uploaded_at": "2024-01-15T10:30:00Z"
}
```

### 3. List All Resumes
**GET** `/api/resumes/`

Get all resumes for the authenticated user.

**Response:**
```json
[
  {
    "id": "uuid-here",
    "file": "/media/resumes/resume1.pdf",
    "parsed_text": "Extracted text...",
    "uploaded_at": "2024-01-15T10:30:00Z"
  }
]
```

### 4. Get Specific Resume
**GET** `/api/resumes/{id}/`

Get details of a specific resume.

### 5. Update Resume
**PUT** `/api/resumes/{id}/`

Update resume details.

### 6. Delete Resume
**DELETE** `/api/resumes/{id}/`

Delete a resume.

---

## 💼 Job Management APIs

### 1. List/Create Jobs
**GET/POST** `/api/jobs/`

**GET Response:**
```json
[
  {
    "id": 1,
    "job_title": "Data Scientist",
    "company_name": "Tech Corp",
    "spoc_email": "hr@techcorp.com",
    "hiring_manager_email": "manager@techcorp.com",
    "current_team_size_info": "10-15 people",
    "number_to_hire": 3,
    "position_level": "IC",
    "current_process": "Current hiring process...",
    "tech_stack_details": "Python, ML, SQL",
    "jd_file": "/media/job_descriptions/jd.pdf",
    "jd_link": "https://example.com/jd",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### 2. Job Details
**GET/PUT/DELETE** `/api/jobs/{id}/`

### 3. Job Titles
**GET** `/api/jobs/titles/`

---

## 👥 Candidate Management APIs

### 1. List/Create Candidates
**GET/POST** `/api/candidates/`

### 2. Candidate Details
**GET/PUT/DELETE** `/api/candidates/{id}/`

---

## 📅 Interview Scheduling APIs

### 1. List/Create Interviews
**GET/POST** `/api/interviews/`

**Response:**
```json
[
  {
    "id": "uuid-here",
    "candidate": "candidate-id",
    "job": "job-id",
    "status": "scheduled",
    "interview_round": "Technical Round 1",
    "feedback": "",
    "started_at": null,
    "ended_at": null,
    "video_url": "",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

### 2. Interview Details
**GET/PUT/DELETE** `/api/interviews/{id}/`

---

## 🏢 Hiring Agency Management APIs

### 1. List Hiring Agency Users
**GET** `/hiring_agency/`

### 2. Add Hiring Agency User
**POST** `/hiring_agency/add_user/`

### 3. Edit Hiring Agency User (Company Only)
**PUT/PATCH** `/hiring_agency/{id}/`

*Note: Only users with 'COMPANY' role can edit hiring agency data.*

---

## 🏢 Company Management APIs

### 1. Company Endpoints
**GET/POST** `/company/`

---

## 🔐 Authentication APIs

### 1. Login
**POST** `/auth/login/`

### 2. Register
**POST** `/auth/register/`

### 3. Token Refresh
**POST** `/auth/token/refresh/`

---

## 📊 Evaluation APIs

### 1. Evaluation Endpoints
**GET/POST** `/api/evaluation/`

---

## 🛠️ Testing the APIs

### 1. Start the Server
```bash
python manage.py runserver
```

### 2. Test Bulk Resume Upload
```bash
# Using curl
curl -X POST http://localhost:8000/api/resumes/bulk-upload/ \
  -H "Authorization: Token your-token" \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.docx"

# Using Python requests
import requests

files = {
    'files': [
        ('resume1.pdf', open('resume1.pdf', 'rb')),
        ('resume2.docx', open('resume2.docx', 'rb'))
    ]
}

headers = {'Authorization': 'Token your-token'}
response = requests.post('http://localhost:8000/api/resumes/bulk-upload/', 
                        files=files, headers=headers)
print(response.json())
```

### 3. Test Single Resume Upload
```bash
curl -X POST http://localhost:8000/api/resumes/ \
  -H "Authorization: Token your-token" \
  -F "file=@resume.pdf"
```

---

## 🔧 Features

### ✅ Bulk Resume Processing
- Upload up to 10 resumes simultaneously
- Concurrent processing for better performance
- Automatic text extraction from PDF/DOCX files
- Field extraction: name, email, phone, experience
- Detailed success/failure reporting

### ✅ Job Management
- Create and manage job postings
- Upload job descriptions
- Track hiring requirements

### ✅ Interview Scheduling
- Schedule interviews between candidates and jobs
- Track interview status and feedback
- Video URL management

### ✅ Role-based Access Control
- Company users can edit hiring agency data
- Admin and company role management
- Secure authentication

---

## 📝 Notes

1. **File Types Supported**: PDF, DOCX, DOC
2. **Concurrent Processing**: Up to 5 workers for bulk uploads
3. **Authentication**: Token-based authentication required
4. **File Size Limits**: Configured in Django settings
5. **Error Handling**: Comprehensive error reporting for failed uploads 