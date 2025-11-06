# Timezone and Email Fixes

## Issues Fixed

### 1. ✅ Timezone Mismatch (12:50 PM showing as 6:20 PM)

**Problem:** 
- Scheduled interview at 12:50 PM but displayed as 6:20 PM - 6:30 PM in candidate details
- 5.5 hour difference = timezone conversion issue (IST vs UTC)

**Root Cause:**
- Slot times are stored as `TimeField` (no timezone info) like "12:50:00"
- When combined with date, Django was using server timezone (UTC) by default
- Frontend was displaying raw slot times which don't account for timezone
- Browser was interpreting times incorrectly

**Solution:**
1. **Backend Changes:**
   - Modified `book_slot()` and `book_interview()` to interpret slot times as IST (Asia/Kolkata)
   - Convert IST times to UTC for storage (Django stores in UTC)
   - This ensures times are stored correctly regardless of server timezone

2. **Frontend Changes:**
   - Updated `CandidateDetails.jsx` to **prefer `interview.started_at` and `interview.ended_at`** for display
   - These are proper DateTime objects with timezone info (UTC)
   - Browser automatically converts UTC to local timezone for display
   - Fallback to `slot_details` only if `started_at`/`ended_at` not available

**Code Changes:**
- `interviews/views.py` - Lines 943-968, 1092-1117: Interpret slot times as IST, convert to UTC
- `notifications/services.py` - Lines 233-259: Same timezone handling
- `frontend/src/components/CandidateDetails.jsx` - Prioritize `started_at`/`ended_at` for display

### 2. ✅ Email Not Sending After Scheduling

**Problem:** Interview link emails not being sent to candidates after scheduling

**Root Cause:**
- `EMAIL_BACKEND` is NOT SET in `.env` file
- Django defaults to `django.core.mail.backends.console.EmailBackend`
- Emails print to console instead of actually sending

**Solution:**
- Update `.env` file with SMTP configuration

**Required .env Settings:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=aditya24.rsl@gmail.com
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=aditya24.rsl@gmail.com
```

**Note:** The email sending code is already in place and working - it just needs proper SMTP configuration.

## Testing

### Test Timezone Fix:
1. Schedule an interview for 12:50 PM
2. Check candidate details - should show 12:50 PM (or converted to your browser's timezone correctly)
3. Verify the time matches what was scheduled

### Test Email Fix:
1. Update `.env` with SMTP settings (see above)
2. Schedule a new interview
3. Check Django logs for: `✅ Interview notification sent via email: candidate@email.com`
4. Check candidate's email inbox (and spam folder)

## How It Works Now

### Time Flow:
1. **User schedules:** 12:50 PM (in IST, assumed)
2. **Backend:** Interprets as IST → Converts to UTC for storage
   - 12:50 PM IST = 7:20 AM UTC (IST is UTC+5:30)
3. **Database:** Stores as UTC datetime
4. **Frontend:** Receives UTC datetime → Browser converts to local timezone for display
   - If browser is in IST: Shows 12:50 PM ✅
   - If browser is in UTC: Shows 7:20 AM (correct for UTC)

### Email Flow:
1. Interview scheduled → `book_slot()` or `book_interview()` called
2. Email notification triggered: `NotificationService.send_candidate_interview_scheduled_notification(interview)`
3. If `EMAIL_BACKEND=smtp`: Email sent via SMTP
4. If `EMAIL_BACKEND=console`: Email printed to console (for development)

## Next Steps

1. ✅ Timezone fix applied - test by scheduling new interview
2. ⚠️ **ACTION REQUIRED:** Update `.env` file with SMTP settings to enable email sending
3. Test email sending after updating `.env`
4. Verify times display correctly in candidate details

## Important Notes

- For existing interviews scheduled before this fix, you may need to reschedule them for times to display correctly
- The timezone fix assumes slot times are in IST (Asia/Kolkata) - if your users are in a different timezone, we can adjust
- Email sending will work once `.env` is configured with SMTP settings

