# Interview Scheduling Fixes

## Issues Fixed

### 1. ✅ Time Mismatch Between Scheduled Time and Displayed Time

**Problem:** 
- When scheduling an interview, the time shown during scheduling didn't match the time displayed in candidate details
- Interview `started_at` and `ended_at` were not being set from the slot's `interview_date`, `start_time`, and `end_time`

**Root Cause:**
- The `Interview` model has `started_at` and `ended_at` as DateTimeField
- The `InterviewSlot` model has separate `interview_date` (DateField) and `start_time`/`end_time` (TimeField)
- When booking a slot, these weren't being combined into proper DateTime objects for the Interview

**Solution:**
- Updated `book_slot()` in `InterviewSlotViewSet` (line 943-963)
- Updated `book_interview()` in `InterviewScheduleViewSet` (line 1065-1085)
- Both now properly combine `slot.interview_date` + `slot.start_time` and `slot.interview_date` + `slot.end_time` to create DateTime objects
- These are set as `interview.started_at` and `interview.ended_at` immediately when booking

**Files Changed:**
- `interviews/views.py` - Added time synchronization when booking slots
- `notifications/services.py` - Improved time handling in email notification service

### 2. ✅ Email Not Sending After Scheduling

**Problem:**
- After scheduling an interview, the interview link email was not being sent to candidates

**Root Causes:**
1. `EMAIL_BACKEND` was set to `console` in `.env` file (emails print to console, don't actually send)
2. Email sending happens but may fail silently

**Solution:**
- Email notification code was already in place in both booking functions
- The main issue is `.env` configuration needs to be updated

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

**Email Sending Points:**
1. `book_slot()` method (line 969) - Sends email when booking via slot endpoint
2. `book_interview()` method (line 1091) - Sends email when booking via schedule endpoint

Both call `NotificationService.send_candidate_interview_scheduled_notification(interview)`

## Testing

### Test Time Synchronization:
1. Schedule an interview for a specific date and time (e.g., Nov 3, 2025 at 5:30 PM)
2. Check candidate details - should show the same date and time
3. Verify `interview.started_at` and `interview.ended_at` match the slot

### Test Email Sending:
1. Ensure `.env` has correct SMTP settings (not console backend)
2. Schedule an interview
3. Check Django logs for:
   - `✅ Interview notification sent via email: candidate@email.com` (success)
   - `❌ SMTP email failed` (configuration issue)
   - `⚠️ EMAIL_BACKEND is set to console` (wrong backend)
4. Check candidate's email inbox (and spam folder)

## Code Changes Summary

### interviews/views.py
- **Line 943-963** (`book_slot`): Added code to combine slot date + time into interview DateTime fields
- **Line 1065-1085** (`book_interview`): Added same time synchronization logic

### notifications/services.py  
- **Line 233-255**: Improved time handling to properly combine date + time when setting interview times

## Next Steps

1. ✅ Fix time synchronization - DONE
2. ⚠️ Update `.env` file to use SMTP backend (not console)
3. ✅ Test email sending with `test_email_credentials.py`
4. Test interview scheduling end-to-end
5. Verify times match between scheduling and candidate details

## Notes

- Interview times are now always synced with slot times when booking
- Email sending will work once `.env` is configured with SMTP settings
- If EMAIL_BACKEND is console, emails print to Django console output but don't actually send
- Email failures are logged but don't break the booking process (booking still succeeds)

