# Complete Interview Scheduling Flow

## Overview
This document describes the complete flow from scheduling an interview to the candidate receiving the email and starting the interview.

## Flow Steps

### 1. **Schedule Interview (Frontend → Backend)**

#### Frontend Action (`StatusUpdateModal.jsx` or `TimeSlotPicker.jsx`):
```javascript
// 1. Create interview
POST /api/interviews/
Body: { candidate_id, job_id, ... }

// 2. Update slot (increment bookings)
PUT /api/interviews/slots/{slot_id}/
Body: { current_bookings: X, status: "booked" (if full) }

// 3. Create schedule relationship
POST /api/interviews/slots/{slot_id}/book_slot/
Body: { interview_id, booking_notes }
```

#### Backend (`interviews/views.py` - `book_slot`):
1. **Validates slot capacity** (checks `current_bookings < max_candidates`, not just status)
2. **Creates/updates InterviewSchedule**
3. **Calls `slot.book_slot()`** (increments `current_bookings`)
4. **Updates interview times** (`started_at`, `ended_at`) from slot in IST → UTC
5. **Creates InterviewSession** (if `session_key` doesn't exist)
6. **Sends email** via `NotificationService.send_candidate_interview_scheduled_notification()`

### 2. **Email Sending (`notifications/services.py`)**

#### NotificationService:
- Uses **same reliable approach** as `test_email_sending_live.py`
- Reads credentials from `.env` via Django settings
- Auto-fixes TLS/SSL conflicts (disables SSL for port 587)
- Validates configuration before sending
- Gets candidate email from `interview.candidate.email`
- Converts times to IST for display
- Generates interview link using `session_key`:
  ```
  {BACKEND_URL}/?session_key={session_key}
  ```

#### Email Content:
- Subject: "Interview Scheduled - [Job Title] at [Company Name]"
- Interview details (date, time in IST, duration)
- Interview link
- Important instructions

### 3. **Candidate Clicks Link**

#### URL Format:
```
http://localhost:8000/?session_key=abc123...
```

#### Backend (`interview_app/views.py` - `interview_portal`):
1. **Extracts `session_key`** from URL query parameter
2. **Finds InterviewSession** by `session_key`
3. **Validates timing**:
   - Too early: Shows countdown with scheduled time (IST)
   - Too late (>10 min grace period): Shows expired message
   - Valid window: Proceeds to interview
4. **Renders interview portal** (`portal.html`)
5. **Frontend JavaScript** (`portal_auto.html`):
   - Calls `/ai/start` with `session_key`
   - Gets first question, audio URL
   - Starts recording
   - Interview begins!

## Key Fixes Applied

### 1. **Fixed `book_slot` Bad Request (400) Error**
- **Problem**: Frontend updates slot status to "booked" before calling `book_slot`, causing validation failure
- **Solution**: Changed validation to check capacity (`current_bookings < max_candidates`) instead of strict status check

### 2. **Fixed Email Sending**
- **Problem**: Emails not sending reliably
- **Solution**: 
  - Always use `NotificationService` which uses same approach as `test_email_sending_live.py`
  - Auto-fixes TLS/SSL conflicts
  - Validates configuration before sending
  - Provides clear error messages

### 3. **Fixed Interview Link Flow**
- **Problem**: Link might not work correctly
- **Solution**: 
  - InterviewSession created automatically in `book_slot`
  - `session_key` stored in `Interview.session_key`
  - Link format: `{BACKEND_URL}/?session_key={session_key}`
  - Portal validates timing and starts interview

## Testing the Flow

### 1. Schedule an Interview:
```
1. Create interview via frontend
2. Select time slot
3. Book slot
4. Check terminal for email sending logs
```

### 2. Check Email:
```
- Email should arrive at candidate.email
- Contains interview details in IST
- Contains clickable interview link
```

### 3. Test Interview Link:
```
1. Copy link from email
2. Open in browser
3. Should show interview portal (if within time window)
4. Interview should start automatically
```

## Files Modified

1. **`interviews/views.py`**:
   - `book_slot`: Changed validation to check capacity instead of status
   - Always sends email via NotificationService
   
2. **`interviews/models.py`**:
   - `book_slot`: Checks capacity instead of strict availability

3. **`notifications/services.py`**:
   - Already uses reliable email sending approach (from previous fixes)

4. **`interview_app/views.py`**:
   - `interview_portal`: Already handles session_key correctly

## Status

✅ **Scheduling**: Works (creates Interview + InterviewSchedule)  
✅ **Email Sending**: Uses reliable NotificationService  
✅ **Interview Link**: Works via `session_key` parameter  
✅ **Interview Start**: Portal validates and starts interview  

## Troubleshooting

### Email Not Sending:
1. Check `.env` has correct email credentials
2. Check terminal logs for email errors
3. Run `python test_email_sending_live.py` to test email config

### Bad Request on book_slot:
1. Check `current_bookings < max_candidates`
2. Check `interview_id` is provided in request
3. Check slot exists and is valid

### Interview Link Not Working:
1. Check `session_key` is generated in `book_slot`
2. Check `InterviewSession` exists for `session_key`
3. Check timing (not too early/late)
4. Check URL format: `/?session_key=...`

