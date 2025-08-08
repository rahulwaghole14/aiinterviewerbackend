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

### 1. List All Candidates
**GET** `/api/candidates/`

**Description**: Retrieve all candidates with POC email information.

**Access Control**:
- **Admin**: Sees all candidates
- **Company User**: Sees candidates from their company
- **Hiring Agency**: Sees candidates they created

**Response Example**:
```json
[
    {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "poc_email": "contact@agency.com",
        "experience_years": 5,
        "domain": "Technology",
        "resume": "/media/resumes/john_doe.pdf",
        "created_at": "2025-08-08T10:30:00Z"
    }
]
```

### 2. Create Candidate
**POST** `/api/candidates/`

**Description**: Create a new candidate with POC email support.

**Required Fields**:
- `name` (string): Candidate name
- `email` (string): Candidate email
- `phone` (string): Phone number
- `experience_years` (integer): Years of experience
- `domain` (string): Domain/field

**Optional Fields**:
- `poc_email` (string): Point of contact email
- `resume` (file): Resume file

**Request Example**:
```json
{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "poc_email": "contact@agency.com",
    "experience_years": 5,
    "domain": "Technology"
}
```

### 3. Bulk Create Candidates
**POST** `/api/candidates/bulk-create/?step=extract`

**Description**: Extract candidate data from uploaded files (first step).

**POST** `/api/candidates/bulk-create/?step=submit`

**Description**: Submit extracted candidate data with POC email support.

**Request Example**:
```json
{
    "candidates": [
        {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "poc_email": "contact@agency.com",
            "experience_years": 5,
            "domain": "Technology"
        }
    ],
    "poc_email": "agency@example.com"
}
```

### 4. Candidate Details
**GET/PUT/DELETE** `/api/candidates/{id}/`

**Description**: Get, update, or delete a specific candidate.

---

**🔒 Security Notes**:
- POC email field is included in responses
- Bulk creation supports POC email for all candidates
- Company-specific data isolation

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
**GET** `/api/hiring_agency/`

**Description**: Retrieve all hiring agencies with role-based filtering and company-specific access control.

**Access Control**:
- **Admin**: Sees all hiring agencies from all companies
- **Company User**: Sees only hiring agencies from their own company
- **Other Users**: Empty list (no access)

**Security Features**:
- ✅ **Role Filtering**: Returns ONLY hiring agencies (role='Hiring Agency')
- ✅ **Data Isolation**: Prevents exposure of other user roles (Recruiter, Company, etc.)
- ✅ **Company Filtering**: Company users only see their own hiring agencies

**Response Example**:
```json
[
    {
        "id": 1,
        "email": "agency@example.com",
        "role": "Hiring Agency",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890",
        "company_name": "Example Company",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "permission_granted": "2025-08-08",
        "created_by": 1
    }
]
```

### 2. Create Hiring Agency User
**POST** `/api/hiring_agency/add_user/`

**Description**: Create a new hiring agency user with password support and company relationship management.

**Required Fields**:
- `email` (string): Unique email address
- `role` (string): Must be "Hiring Agency"
- `first_name` (string): First name
- `last_name` (string): Last name
- `phone_number` (string): Phone number

**Optional Fields**:
- `password` (string): Password for authentication (write-only)
- `company_name` (string): Company name (auto-set for company users)
- `linkedin_url` (string): LinkedIn profile URL

**Access Control**:
- **Admin**: Can create hiring agencies for any company
- **Company User**: Can create hiring agencies (auto-assigned to their company)
- **Other Users**: No access

**Request Example**:
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@agency.com",
    "password": "agency123",
    "phone_number": "+1234567890",
    "role": "Hiring Agency",
    "company_name": "Example Company",
    "linkedin_url": "https://linkedin.com/in/johndoe"
}
```

**Response Example**:
```json
{
    "id": 1,
    "email": "john.doe@agency.com",
    "role": "Hiring Agency",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "company_name": "Example Company",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "permission_granted": "2025-08-08",
    "created_by": 1
}
```

### 3. Get Hiring Agency Details
**GET** `/api/hiring_agency/{id}/`

**Description**: Get detailed information about a specific hiring agency.

**Access Control**:
- **Admin**: Can view any hiring agency
- **Company User**: Can only view hiring agencies from their company
- **Other Users**: No access

### 4. Update Hiring Agency
**PUT/PATCH** `/api/hiring_agency/{id}/`

**Description**: Update hiring agency information.

**Access Control**:
- **Admin**: Can update any hiring agency
- **Company User**: Can only update hiring agencies from their company
- **Other Users**: No access

### 5. Delete Hiring Agency
**DELETE** `/api/hiring_agency/{id}/`

**Description**: Delete a hiring agency user.

**Access Control**:
- **Admin**: Can delete any hiring agency
- **Company User**: Can only delete hiring agencies from their company
- **Other Users**: No access

---

**🔒 Security Notes**:
- All endpoints require authentication
- Role-based access control enforced
- Company-specific data isolation
- Password field is write-only (never returned in responses)
- Only hiring agencies are returned (no other user roles)

---

## 🏢 Company Management APIs

### 1. List All Companies
**GET** `/api/companies/`

**Description**: Retrieve all companies with email information.

**Access Control**:
- **Admin**: Sees all companies
- **Company User**: Sees only their own company
- **Other Users**: Limited access

**Response Example**:
```json
[
    {
        "id": 1,
        "name": "Example Company",
        "email": "contact@example.com",
        "description": "A technology company",
        "is_active": true
    }
]
```

### 2. Create Company
**POST** `/api/companies/`

**Description**: Create a new company with email and password support.

**Required Fields**:
- `name` (string): Company name
- `description` (string): Company description

**Optional Fields**:
- `email` (string): Company contact email
- `password` (string): Company password (write-only)

**Request Example**:
```json
{
    "name": "New Company",
    "email": "contact@newcompany.com",
    "password": "company123",
    "description": "A new technology company"
}
```

**Response Example**:
```json
{
    "id": 2,
    "name": "New Company",
    "email": "contact@newcompany.com",
    "description": "A new technology company",
    "is_active": true
}
```

### 3. Get Company Details
**GET** `/api/companies/{id}/`

### 4. Update Company
**PUT/PATCH** `/api/companies/{id}/`

### 5. Delete Company
**DELETE** `/api/companies/{id}/`

---

**🔒 Security Notes**:
- Email field is returned in responses
- Password field is write-only (never returned)
- Company users can only access their own company data

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

### ✅ Enhanced Security & Data Integrity
- **Role-based filtering**: Hiring agency API returns only hiring agencies
- **Company relationships**: Strong ForeignKey relationships for data integrity
- **Password support**: Secure password fields for companies and hiring agencies
- **Email integration**: POC email support for candidates and company contact emails
- **Data isolation**: Company-specific access control for all endpoints

---

## 🆕 Recent Updates

### 🔒 Hiring Agency Role Filtering (Latest)
- **Issue Fixed**: Hiring agency API was returning users with other roles (Recruiter, Company)
- **Solution**: Added role filtering to return only hiring agencies (role='Hiring Agency')
- **Security**: Prevents data leakage and ensures API consistency
- **Testing**: Comprehensive test scripts verify role filtering and company-specific access

### 🏢 Company Email & Password Support
- **New Fields**: Added email and password fields to Company model
- **API Updates**: Company creation and listing now support email/password
- **Security**: Password field is write-only (never returned in responses)
- **Response**: Email field included in company listing responses

### 👥 Candidate POC Email Support
- **New Field**: Added poc_email field to Candidate model
- **Bulk Creation**: POC email support in bulk candidate creation
- **API Integration**: POC email included in candidate responses
- **Workflow**: Supports both direct and two-step bulk creation processes

### 🔗 Hiring Agency Company Relationship
- **Architecture**: Converted weak text-based relationship to strong ForeignKey
- **Performance**: Database joins instead of string matching
- **Data Integrity**: Referential constraints and automatic updates
- **Backward Compatibility**: Maintains existing functionality while improving structure

### 🔑 Hiring Agency Password Support
- **New Field**: Added password field to Hiring Agency UserData model
- **Authentication**: Support for hiring agency login with email/password
- **Security**: Password field is write-only and properly handled
- **Flexibility**: Optional password field maintains backward compatibility
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