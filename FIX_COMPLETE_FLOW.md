# Complete Interview Flow Fix

## Issues to Fix

1. **`book_slot` returning 400 Bad Request** - Interview ID not being received
2. **Email not sending** - Need to ensure email is sent after successful booking
3. **Interview link generation** - Must work when candidate clicks
4. **Interview starts** - Permission access and interview portal
5. **Evaluation results** - Show in evaluation section after completion

## Fixes Applied

### 1. Enhanced `book_slot` Debugging and Data Parsing

**File**: `interviews/views.py`

- Added comprehensive debug logging to see exactly what data is received
- Enhanced request body parsing to handle cases where `request.data` might be empty
- Better error messages showing what was actually received

### 2. Email Sending Flow

**File**: `interviews/views.py` (already fixed in previous updates)

- After creating schedule, always calls `NotificationService.send_candidate_interview_scheduled_notification(interview)`
- Uses same reliable approach as `test_email_sending_live.py`
- Auto-fixes TLS/SSL conflicts
- Gets candidate email from `interview.candidate.email`

### 3. Interview Link Generation

**Files**: 
- `interviews/views.py` - Creates InterviewSession with `session_key`
- `notifications/services.py` - Generates interview URL using `session_key`
- Format: `{BACKEND_URL}/?session_key={session_key}`

### 4. Interview Portal Access

**File**: `interview_app/views.py` - `interview_portal` function

- Validates `session_key` from URL
- Checks timing (not too early/late)
- Grants permission access (no login required)
- Renders interview portal
- JavaScript automatically starts interview

### 5. Evaluation Results

**Files**:
- `interview_app/views.py` - `end_interview_session` triggers evaluation
- `interview_app_11/comprehensive_evaluation_service.py` - Evaluates interview
- Frontend `CandidateDetails.jsx` - Displays evaluation results

## Complete Flow

### Step 1: Schedule Interview
1. Frontend creates interview: `POST /api/interviews/`
2. Frontend updates slot: `PUT /api/interviews/slots/{id}/`
3. Frontend books slot: `POST /api/interviews/slots/{id}/book_slot/`
   - **Sends**: `{ "interview_id": "...", "booking_notes": "..." }`

### Step 2: Backend Processes Booking
1. Validates slot capacity
2. Creates/updates `InterviewSchedule`
3. Updates `interview.started_at` and `ended_at` (IST → UTC)
4. Creates `InterviewSession` if needed
5. Generates `session_key`
6. **Sends email** via `NotificationService`

### Step 3: Candidate Receives Email
- Email contains interview link: `http://localhost:8000/?session_key=abc123...`
- Times displayed in IST
- Instructions for joining

### Step 4: Candidate Clicks Link
1. Opens: `/?session_key=abc123...`
2. Backend validates timing
3. If valid, renders interview portal
4. JavaScript automatically starts interview
5. Permission prompts for camera/microphone

### Step 5: Interview Completion
1. Candidate completes interview
2. `end_interview_session` called
3. Evaluation service runs
4. Results stored in database
5. Frontend shows evaluation in `CandidateDetails`

## Testing Checklist

- [ ] Schedule interview - no 400 errors
- [ ] Check terminal for email sending logs
- [ ] Verify email received at candidate email
- [ ] Click interview link - interview portal opens
- [ ] Camera/microphone permission granted
- [ ] Interview starts automatically
- [ ] Complete interview
- [ ] Check evaluation results in CandidateDetails

## Debug Commands

If `book_slot` still fails, check terminal logs for:
- `DEBUG: Request data: ...`
- `DEBUG: interview_id from data_source: ...`
- `DEBUG: ERROR - interview_id is required...`

This will show exactly what the backend is receiving.

