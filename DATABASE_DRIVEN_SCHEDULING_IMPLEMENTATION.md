# Database-Driven Interview Scheduling Implementation

## ✅ Summary

The interview scheduling system has been updated to fetch all data from the database instead of using file-based scheduling. All interview details are now pulled from:
- **Candidate** model (name, email, resume)
- **Job** model (job details, coding language)
- **InterviewSchedule** model (scheduled time, slot details)

---

## 🔧 Changes Made

### 1. **Job Model - Added `coding_language` Field**

**File**: `jobs/models.py`

- Added `coding_language` field to replace `tech_stack_details` for coding interviews
- Options: `PYTHON`, `JAVASCRIPT`, `JAVA`, `PHP`, `RUBY`, `CSHARP`, `SQL`
- Default: `PYTHON`
- `tech_stack_details` kept for backward compatibility but marked as legacy

**Migration Required**:
```bash
python manage.py makemigrations jobs
python manage.py migrate
```

### 2. **Job Serializer - Updated**

**File**: `jobs/serializers.py`

- Added `coding_language` to `JobSerializer` fields
- Now accessible via API for frontend

### 3. **Database-Driven Scheduling Endpoint**

**File**: `interviews/views.py`

**New Endpoint**: `POST /api/interviews/schedules/create_interview_session/`

**Purpose**: Creates `InterviewSession` from database instead of manual file creation

**Request Body**:
```json
{
  "interview_id": "uuid-of-interview"
}
```

**What It Does**:
1. Fetches `Interview` object from database
2. Extracts candidate details from `Interview.candidate`
3. Extracts job details from `Interview.job`
4. Gets `coding_language` from `Job.coding_language`
5. Gets scheduled time from `Interview.started_at` or `InterviewSchedule.slot`
6. Extracts resume text from `Candidate.resume`
7. Creates `InterviewSession` with all fetched data
8. Generates interview link with `session_key`
9. Sends email notification to candidate
10. Returns interview link and session details

**Response**:
```json
{
  "success": true,
  "interview_link": "http://127.0.0.1:8000/?session_key=...",
  "session_key": "...",
  "session_id": "...",
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  "scheduled_at": "2024-10-20T14:30:00Z",
  "coding_language": "PYTHON",
  "email_sent": true
}
```

---

## 📋 How to Use

### Step 1: Create Migration
```bash
python manage.py makemigrations jobs
python manage.py migrate
```

### Step 2: Update Jobs with Coding Language

When creating or updating a job via frontend/admin, set the `coding_language` field:
- Via API: `POST /api/jobs/` with `{"coding_language": "PYTHON"}`
- Via Admin: Select coding language in Job form

### Step 3: Schedule Interview via Frontend

1. **Select Candidate** from database
2. **Select Job** (with coding_language set)
3. **Book Interview Slot** via `POST /api/interviews/schedules/book_interview/`
4. **Generate Interview Session** by calling:
   ```
   POST /api/interviews/schedules/create_interview_session/
   {
     "interview_id": "<interview-uuid>"
   }
   ```

### Step 4: Interview Auto-Starts

When candidate opens the interview link:
- Portal validates scheduled time
- If within valid window (30 seconds before to 10 minutes after), interview starts automatically
- All questions are generated based on job description and coding language

---

## 🔄 Data Flow

```
Frontend Scheduler
    ↓
1. Select Candidate (from Candidate DB)
    ↓
2. Select Job (from Job DB) → coding_language fetched
    ↓
3. Book Interview Slot → InterviewSchedule created
    ↓
4. Create Interview → Interview object created
    ↓
5. Call create_interview_session endpoint
    ↓
6. System fetches:
   - Candidate: name, email, resume
   - Job: description, coding_language
   - Schedule: date, time
    ↓
7. InterviewSession created with all data
    ↓
8. Email sent to candidate with interview link
    ↓
9. Candidate opens link → Interview auto-starts
```

---

## 🗄️ Database Fields Used

### From Candidate Model:
- `full_name` → `InterviewSession.candidate_name`
- `email` → `InterviewSession.candidate_email`
- `resume` → `InterviewSession.resume_text` (extracted)

### From Job Model:
- `job_title` → Job description
- `company_name` → Job description
- `job_description` → `InterviewSession.job_description`
- `coding_language` → Stored in `InterviewSession.keyword_analysis` as `CODING_LANG=XXX`
- `domain.name` → Job description

### From InterviewSchedule:
- `slot.interview_date` + `slot.start_time` → `InterviewSession.scheduled_at`
- Combined and converted to UTC for storage

---

## 📝 API Endpoint Details

### Endpoint
```
POST /api/interviews/schedules/create_interview_session/
```

### Authentication
Required (use token authentication)

### Request Body
```json
{
  "interview_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Success Response (201)
```json
{
  "success": true,
  "interview_link": "http://127.0.0.1:8000/?session_key=abc123...",
  "session_key": "abc123...",
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  "scheduled_at": "2024-10-20T14:30:00Z",
  "coding_language": "PYTHON",
  "email_sent": true
}
```

### Error Responses

**400 Bad Request**:
```json
{
  "error": "interview_id is required"
}
```

**404 Not Found**:
```json
{
  "error": "Interview not found"
}
```

**500 Internal Server Error**:
```json
{
  "error": "Failed to create interview session: <error message>"
}
```

---

## ✅ Benefits

1. **No File-Based Scheduling**: Everything stored in database
2. **Single Source of Truth**: All data comes from Candidate, Job, InterviewSchedule tables
3. **Automatic Data Fetching**: No manual entry required
4. **Coding Language from Job**: Automatically uses job's coding language
5. **Email Integration**: Automatic email notification on scheduling
6. **Auto-Start**: Interview starts automatically when link is opened within valid time window

---

## 🔄 Migration from File-Based

If you have existing scripts like `create_short_aiml_link.py`, you can now:
1. Remove manual data entry
2. Use the new endpoint instead
3. All data will be fetched from database automatically

---

## 📌 Next Steps

1. **Run Migration**:
   ```bash
   python manage.py makemigrations jobs
   python manage.py migrate
   ```

2. **Update Frontend**: 
   - Integrate `create_interview_session` endpoint call after booking interview
   - Display coding_language field in job creation/editing form

3. **Test**:
   - Create a job with `coding_language` set
   - Schedule an interview for a candidate
   - Call `create_interview_session` endpoint
   - Verify interview link is generated and email is sent
   - Test opening link and auto-start functionality

---

## 🎯 Frontend Integration Example

```javascript
// After booking interview slot
const response = await fetch(`${baseURL}/api/interviews/schedules/create_interview_session/`, {
  method: 'POST',
  headers: {
    'Authorization': `Token ${authToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    interview_id: interview.id
  })
});

const data = await response.json();
if (data.success) {
  console.log('Interview link:', data.interview_link);
  // Display link to user or send via email (already sent automatically)
}
```

