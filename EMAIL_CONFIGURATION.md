# Email Configuration for Interview Scheduling

## Problem
Emails are not being sent when interviews are scheduled because `EMAIL_BACKEND` is set to `console`, which only prints emails to the console instead of actually sending them.

## Solution

### 1. Update `.env` file with email settings:

```env
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### 2. For Gmail specifically:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
   - Use this 16-character password in `EMAIL_HOST_PASSWORD`

### 3. For other email providers:

**Outlook/Hotmail:**
```env
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

**Yahoo:**
```env
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

**Custom SMTP:**
```env
EMAIL_HOST=your-smtp-server.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

### 4. For Render.com deployment:

Add these environment variables in Render Dashboard:
1. Go to your service → Environment
2. Add each variable:
   - `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
   - `EMAIL_HOST=smtp.gmail.com`
   - `EMAIL_PORT=587`
   - `EMAIL_USE_TLS=True`
   - `EMAIL_USE_SSL=False`
   - `EMAIL_HOST_USER=your-email@gmail.com`
   - `EMAIL_HOST_PASSWORD=your-app-password`
   - `DEFAULT_FROM_EMAIL=your-email@gmail.com`

### 5. Test email configuration:

After updating `.env`, restart your Django server and test by scheduling an interview. Check the logs to see if emails are being sent.

## Fixed Issues

✅ **ModuleNotFoundError: No module named 'interview_app_11'**
   - Fixed incorrect import paths in `interviews/views.py`
   - Changed `interview_app_11.views` to `interview_app.views`
   - Removed non-existent `send_interview_session_email` function calls
   - Now using `NotificationService.send_candidate_interview_scheduled_notification()` directly

✅ **Email Backend Configuration**
   - Updated code to use NotificationService consistently
   - Added proper error handling

## Current Status

- ✅ Import errors fixed
- ⚠️ Email backend needs to be configured in `.env` file
- ⚠️ For production, update environment variables on Render.com

## Verification

After configuration, you should see in logs:
```
✅ Email sent to candidate@example.com
```

Instead of:
```
[EMAIL NOT SENT] EMAIL_BACKEND is 'console' - email would print to console only
```

