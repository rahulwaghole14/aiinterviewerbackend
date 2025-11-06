# Email Interview Link Sending - Diagnosis & Fix Summary

## Issues Found and Fixed

### 1. ❌ Missing Import
**Problem:** The `notifications/services.py` file was using `datetime.combine()` without importing `datetime`.

**Fix:** Added `from datetime import datetime` to the imports.

### 2. ⚠️ Silent Email Failures
**Problem:** Email sending failures were being logged but the function was still returning `True`, making it hard to diagnose issues.

**Fix:** 
- Added explicit email configuration checks before attempting to send
- Improved error logging with specific error messages for authentication and connection failures
- Changed return value to `False` when email actually fails to send (console fallback doesn't count as success)

### 3. ⚠️ Poor Error Messages
**Problem:** When emails failed, error messages weren't helpful for diagnosing the issue.

**Fix:** Added specific error messages:
- Authentication errors → Points to App Password requirement for Gmail
- Connection errors → Points to correct SMTP settings

## Common Issues That Prevent Email Sending

### Issue 1: Using Console Backend (Default)
**Symptom:** Emails print to console but don't actually send.

**Solution:** Set `EMAIL_BACKEND` environment variable:
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

### Issue 2: Missing Email Credentials
**Symptom:** Error logs show "Email configuration incomplete"

**Solution:** Set these environment variables:
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### Issue 3: Wrong Password Type (Gmail)
**Symptom:** Authentication failed (535 error)

**Solution:** Use Google App Password, not your regular Gmail password:
1. Go to: https://myaccount.google.com/apppasswords
2. Enable 2-Step Verification if needed
3. Generate App Password for "Mail"
4. Use that 16-character password

### Issue 4: Wrong Port/TLS Settings (Gmail)
**Symptom:** Connection errors

**Solution:** Use correct settings for Gmail:
- Port: 587 with TLS (not 465)
- EMAIL_USE_TLS=True
- EMAIL_USE_SSL=False

## Testing Your Email Configuration

### Step 1: Run the Diagnostic Script
```bash
python test_interview_email_sending.py
```

This will:
- ✅ Check your email configuration
- ✅ Test SMTP connection
- ✅ Send a test email
- ✅ Test interview notification email

### Step 2: Check Logs
After booking an interview, check your Django logs for:
- `✅ Interview notification sent via email:` - Success!
- `❌ SMTP email failed` - Configuration issue
- `⚠️ Interview notification sent to console` - Using console backend

### Step 3: Verify Environment Variables
Make sure your `.env` file or environment variables include:
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

## How Interview Link Emails Work

1. **Trigger:** When an interview slot is booked via:
   - `POST /api/interviews/slots/{slot_id}/book_slot/`
   - `POST /api/interviews/schedules/book_interview/`

2. **Service Call:** `NotificationService.send_candidate_interview_scheduled_notification(interview)`

3. **Email Content:**
   - Candidate name and email
   - Job title and company
   - Interview date, time, and duration
   - **Interview link** (secure, time-limited access)
   - Instructions for joining

4. **Email Delivery:**
   - Primary: SMTP via configured email provider
   - Fallback: Console (prints to terminal if SMTP fails)

## Files Modified

1. **`notifications/services.py`**
   - Added missing `datetime` import
   - Improved error logging
   - Added email configuration checks
   - Better error messages

2. **Created `test_interview_email_sending.py`**
   - Comprehensive diagnostic script
   - Tests all aspects of email functionality

## Next Steps

1. **Set up email credentials** (see `EMAIL_HOST_PASSWORD_GUIDE.md`)
2. **Run diagnostic script**: `python test_interview_email_sending.py`
3. **Test interview booking** and check logs
4. **Verify emails are received** by candidates

## Quick Fix Checklist

- [ ] Set `EMAIL_BACKEND` to `smtp` (not `console`)
- [ ] Set `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
- [ ] For Gmail: Use App Password (generate at https://myaccount.google.com/apppasswords)
- [ ] For Gmail: Use port 587 with TLS (not 465)
- [ ] Test with: `python test_interview_email_sending.py`
- [ ] Check Django logs after booking an interview
- [ ] Verify candidate receives email

## Support Resources

- **Email Setup Guide:** `EMAIL_HOST_PASSWORD_GUIDE.md`
- **Interactive Setup:** Run `python setup_email_password.py`
- **Test Script:** Run `python test_interview_email_sending.py`
- **Email Test:** Run `python test_email.py`

