# Email Configuration Guide

## Problem
Emails are not being sent because `EMAIL_BACKEND` is set to `console` backend, which only prints emails to the console instead of actually sending them.

## Solution

### For Local Development (.env file)

Add these settings to your `.env` file:

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

### For Gmail

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Generate a password for "Mail" and "Other (Custom name)" → "Django"
   - Use this 16-character password (not your regular Gmail password)

3. **Settings for Gmail:**
   ```env
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_USE_SSL=False
   ```

### For Other Email Providers

#### Outlook/Hotmail:
```env
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
```

#### Yahoo:
```env
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
```

#### Custom SMTP:
```env
EMAIL_HOST=your-smtp-server.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
```

### For Render Deployment

1. Go to Render Dashboard → Your Backend Service
2. Click "Environment" tab
3. Add these environment variables:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

4. Save changes - Render will automatically redeploy

## Testing Email Configuration

After updating your `.env` file, restart your Django server and test:

```bash
python manage.py shell
```

Then in the shell:
```python
from django.core.mail import send_mail
from django.conf import settings

print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")

# Test email
send_mail(
    'Test Email',
    'This is a test email from Django.',
    settings.DEFAULT_FROM_EMAIL,
    ['your-test-email@gmail.com'],
    fail_silently=False,
)
```

## Common Issues

### 1. "EMAIL_BACKEND is set to console"
- **Fix**: Set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` in `.env`

### 2. "Authentication failed"
- **Fix**: Use App Password for Gmail (not regular password)
- **Fix**: Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct

### 3. "Connection timeout"
- **Fix**: Check firewall/VPN settings
- **Fix**: Verify EMAIL_HOST and EMAIL_PORT are correct

### 4. "TLS/SSL error"
- **Fix**: For port 587, use `EMAIL_USE_TLS=True` and `EMAIL_USE_SSL=False`
- **Fix**: For port 465, use `EMAIL_USE_TLS=False` and `EMAIL_USE_SSL=True`

## Current Status

The code has been fixed to:
- ✅ Remove incorrect `interview_app_11` import
- ✅ Use correct `interview_app.views` import for `get_text_from_file`
- ✅ Use `NotificationService` for all email sending (already working)

You just need to configure the email settings in your `.env` file or Render environment variables.

