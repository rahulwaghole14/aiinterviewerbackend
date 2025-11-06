# Complete Email Flow Fix

## Problem
Emails are not being sent when scheduling interviews from the frontend UI, even though the test script works.

## Root Cause Analysis

### 1. Email Configuration
✅ Test script (`test_email_sending_live.py`) works - configuration is correct

### 2. Email Sending Flow
The flow when scheduling from UI:
1. Frontend creates interview via `/api/interviews/` POST
2. Frontend calls `/api/interviews/slots/{slot_id}/book_slot/` POST with `interview_id`
3. `book_slot` method should:
   - Create InterviewSchedule
   - Create InterviewSession with session_key
   - Update Interview with session_key
   - Send email via NotificationService

### 3. Issue Identified
- Email sending is being called but may be failing silently
- Need to ensure session_key is set before email is sent
- Need to verify email link format matches interview_portal view

## Fixes Applied

### 1. Enhanced Debug Logging
Added comprehensive debug logging in:
- `interviews/views.py` - `book_slot` method
- `notifications/services.py` - `send_candidate_interview_scheduled_notification` method

### 2. Email Link Format
Ensured email link format matches what `interview_portal` expects:
- Format: `http://localhost:8000/?session_key={session_key}`
- This matches the `interview_portal` view which expects `session_key` in query params

### 3. Session Key Validation
- Verify session_key exists before sending email
- Create InterviewSession if it doesn't exist
- Update Interview with session_key before email sending

### 4. Email Sending Flow
The email sending happens in this order:
1. Create InterviewSession (if needed)
2. Set session_key on Interview
3. Call NotificationService.send_candidate_interview_scheduled_notification()
4. NotificationService generates URL and sends email

## What to Check in Terminal

When scheduling an interview, you should see:

```
======================================================================
EMAIL: Attempting to send interview notification email for interview <id>
EMAIL: Interview session_key: <session_key>
EMAIL: Candidate email: <email>
======================================================================

======================================================================
[EMAIL DEBUG] send_candidate_interview_scheduled_notification called
  Interview ID: <uuid>
======================================================================

EMAIL: Configuration check:
  EMAIL_BACKEND: django.core.mail.backends.smtp.EmailBackend
  EMAIL_HOST: smtp.gmail.com
  ...

[EMAIL DEBUG] Generated interview URL: http://localhost:8000/?session_key=xxx
[EMAIL DEBUG] About to call send_mail()

[SUCCESS] Interview notification email sent successfully!
  ✅ send_mail() returned without exception
  ✅ Recipient: candidate@email.com
  ✅ Interview URL: http://localhost:8000/?session_key=xxx
```

## Interview Portal Flow

When candidate clicks the link:
1. URL: `/?session_key={session_key}`
2. `interview_portal` view handles it
3. Validates session_key exists
4. Checks timing (allows 30 seconds before, expires 10 minutes after)
5. Grants microphone/video access
6. Starts interview process

## Next Steps

1. **Schedule an interview from UI** and watch terminal output
2. **Check for debug messages** - they will show exactly where it's failing
3. **Verify email is sent** - look for `[SUCCESS]` message
4. **Test interview link** - click the link in email to verify it opens interview portal

If emails still don't send, the debug logs will show exactly what's failing.

