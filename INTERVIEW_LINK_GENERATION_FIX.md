# Interview Link Generation and Email Sending Fix

## Issues Fixed

### 1. **`generate_interview_link` Function** (lines 214-390)

**Problems:**
- Email configuration checks were too simple
- No TLS/SSL conflict handling
- No detailed error messages
- Used `os.getenv` instead of Django settings

**Fixes Applied:**
- ✅ Added same reliable email sending approach as `test_email_sending_live.py`
- ✅ Auto-fixes TLS/SSL conflicts (disables SSL for port 587)
- ✅ Validates all email configuration before sending
- ✅ Detailed debug logging showing configuration
- ✅ Clear error messages with fix suggestions
- ✅ Uses `DEFAULT_FROM_EMAIL` from settings

### 2. **`create_interview_invite` Function** (lines 150-212)

**Problems:**
- Used `os.getenv('EMAIL_HOST_USER')` instead of Django settings
- No TLS/SSL conflict handling
- No configuration validation
- Basic error messages

**Fixes Applied:**
- ✅ Uses Django settings instead of `os.getenv`
- ✅ Auto-fixes TLS/SSL conflicts
- ✅ Validates email configuration before attempting to send
- ✅ Detailed error messages
- ✅ Enhanced email content with better formatting
- ✅ Uses `DEFAULT_FROM_EMAIL` from settings

## Complete Flow

### Interview Link Generation Flow

1. **Create Interview Session**
   - Function: `generate_interview_link` or `create_interview_invite`
   - Creates `InterviewSession` with `session_key`
   - Sets `scheduled_at` in IST timezone

2. **Generate Interview Link**
   - Format: `{BACKEND_URL}/?session_key={session_key}`
   - Example: `http://localhost:8000/?session_key=abc123def456...`

3. **Email Configuration Check**
   - Validates `EMAIL_BACKEND` (not console)
   - Validates `EMAIL_HOST` is set
   - Validates `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
   - Auto-fixes TLS/SSL conflicts

4. **Send Email**
   - Uses same reliable approach as `test_email_sending_live.py`
   - Sends to `candidate_email`
   - Includes interview link in email body
   - Times displayed in IST

5. **Candidate Clicks Link**
   - `interview_app/views.py` - `interview_portal` function handles it
   - Validates `session_key`
   - Checks timing (not too early/late)
   - Grants permission access (no login required)
   - Renders interview portal
   - JavaScript automatically starts interview

## Email Content

Both functions now send emails with:
- **Subject**: "Your Interview Has Been Scheduled - {job_title}" or "Your Talaro Interview Invitation"
- **Interview Details**: Date, time (in IST), position
- **Interview Link**: Clickable URL with `session_key`
- **Important Instructions**: Join time, technical requirements, ID verification

## Debug Logging

Enhanced logging shows:
```
EMAIL: Sending interview invitation email
EMAIL: Configuration:
  EMAIL_BACKEND: ...
  EMAIL_HOST: ...
  EMAIL_PORT: ...
  EMAIL_USE_TLS: ...
  EMAIL_USE_SSL: ...
  EMAIL_HOST_USER: ...
  EMAIL_HOST_PASSWORD: SET
  DEFAULT_FROM_EMAIL: ...
EMAIL: To: candidate@example.com
EMAIL: Subject: ...
EMAIL: Interview Link: http://localhost:8000/?session_key=...
[SUCCESS] Email sent successfully to candidate@example.com
```

## Testing

### Test `generate_interview_link`:
```bash
POST /generate_interview_link/
Body: {
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  "job_description": "Software Engineer",
  "scheduled_at": "2025-11-04T14:30"
}
```

### Test `create_interview_invite`:
- Use the form at `/create_interview_invite/`
- Fill in all fields
- Submit form

## Troubleshooting

If email not sending, check terminal for:
- `[ERROR] EMAIL_BACKEND is set to console...`
- `[ERROR] EMAIL_HOST is not set...`
- `[ERROR] Email credentials incomplete...`
- `[EMAIL FAILED] Error sending email...`

All errors include specific fix instructions!

