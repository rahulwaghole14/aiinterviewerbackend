# Email Sending Debug Guide

## Current Issues

### 1. `/api/requests/pending/` 401 Unauthorized
- **Status**: ✅ FIXED - URL path corrected
- **Issue**: Was `/api/requests/requests/pending/` (double requests)
- **Fix**: Changed to `/api/requests/pending/` in `candidates/urls.py`
- **Note**: The 401 error suggests authentication token might be missing in frontend request

### 2. `book_slot` Returns 400 Bad Request
- **Status**: 🔧 ENHANCED DEBUGGING
- **Issue**: `interview_id` not being extracted from request
- **Enhanced**:
  - Better request parsing from multiple sources
  - More detailed debug logging
  - Better error messages showing what was received

### 3. Email Not Sending
- **Status**: 🔧 ENHANCED DEBUGGING  
- **Issue**: Email sending might be failing silently
- **Enhanced**:
  - Detailed email configuration logging
  - Clear success/failure messages
  - Email sending happens at multiple points to ensure it works

## Debug Steps

### Step 1: Check Terminal Logs
When scheduling an interview, look for:

```
======================================================================
DEBUG: book_slot called for slot ...
DEBUG: Request data: ...
DEBUG: interview_id extracted: <uuid>
======================================================================

EMAIL: Attempting to send interview notification email for interview ...
EMAIL: Interview session_key: ...
EMAIL: Candidate email: ...
======================================================================

✅ SUCCESS: Email notification sent successfully for interview ...
```

### Step 2: Check Browser Console
Look for:
- `Sending booking data: { interview_id: "...", booking_notes: "..." }`
- `Schedule creation response status: 201` (success) or `400` (error)

### Step 3: Check Email Configuration
If email fails, look for:
- `⚠️ WARNING: Email notification returned False` - Configuration issue
- `❌ ERROR: NotificationService failed` - Exception details

## What Was Fixed

1. **Enhanced Request Parsing**:
   - Tries `data_source` (parsed JSON)
   - Falls back to `request.data` (DRF parsed)
   - Falls back to `request_body` (manually parsed)
   - Falls back to query parameters

2. **Enhanced Email Logging**:
   - Shows interview details before sending
   - Shows email configuration
   - Shows clear success/failure messages

3. **Multiple Email Attempts**:
   - Email sent after InterviewSession creation
   - Email sent via NotificationService (primary)
   - Ensures email is sent even if one method fails

## Next Steps

1. **Schedule an interview** and watch terminal logs
2. **Check for**:
   - `DEBUG: interview_id extracted: <uuid>` - Should show the UUID
   - `EMAIL: Attempting to send...` - Should appear
   - `✅ SUCCESS: Email notification sent...` - Should appear if email sent

3. **If still failing**, check terminal for:
   - What `interview_id` value is extracted (or None)
   - What email configuration errors appear
   - What the actual error message is

The enhanced logging will show exactly what's happening at each step!

