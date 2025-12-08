# Gmail Email Configuration for Interview Link Emails

## ✅ Correct Gmail SMTP Settings

Yes, your settings are **correct** for sending interview link emails via Gmail:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

## Complete Configuration Checklist

### ✅ Required Settings (All Must Be Set):

1. **EMAIL_HOST** ✅
   ```
   EMAIL_HOST=smtp.gmail.com
   ```

2. **EMAIL_PORT** ✅
   ```
   EMAIL_PORT=587
   ```
   - Port 587 = TLS (recommended)
   - Port 465 = SSL (alternative, but 587 is better)

3. **EMAIL_USE_TLS** ✅
   ```
   EMAIL_USE_TLS=True
   ```
   - **MUST be True** for port 587

4. **EMAIL_USE_SSL** ✅
   ```
   EMAIL_USE_SSL=False
   ```
   - **MUST be False** for port 587
   - ⚠️ **IMPORTANT**: Cannot be True if EMAIL_USE_TLS is True

5. **EMAIL_BACKEND** ✅
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   ```
   - **MUST be smtp backend** (not console)

6. **EMAIL_HOST_USER** ✅
   ```
   EMAIL_HOST_USER=your-email@gmail.com
   ```
   - Your Gmail address

7. **EMAIL_HOST_PASSWORD** ✅
   ```
   EMAIL_HOST_PASSWORD=your-16-character-app-password
   ```
   - ⚠️ **CRITICAL**: Must be Gmail **App Password**, not your regular Gmail password
   - 16 characters, no spaces

8. **DEFAULT_FROM_EMAIL** ✅
   ```
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```
   - Usually same as EMAIL_HOST_USER

## How to Get Gmail App Password

### Step 1: Enable 2-Step Verification
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled

### Step 2: Generate App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select **Mail** as the app
3. Select **Other (Custom name)** as the device
4. Enter "Django" or "Interview Platform"
5. Click **Generate**
6. Copy the **16-character password** (no spaces)
   - Format: `xxxx xxxx xxxx xxxx` → Remove spaces → `xxxxxxxxxxxxxxxx`

### Step 3: Use in Environment Variables
```env
EMAIL_HOST_PASSWORD=xxxxxxxxxxxxxxxx
```

## Testing Email Configuration

After setting up, test with:

```bash
python manage.py shell
```

Then in Python shell:
```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Interview Email',
    'This is a test email from Django.',
    settings.DEFAULT_FROM_EMAIL,
    ['test-email@gmail.com'],
    fail_silently=False,
)
```

## Common Issues & Solutions

### ❌ "Authentication failed" or "535 Error"
**Problem**: Using regular Gmail password instead of App Password
**Solution**: Generate and use Gmail App Password

### ❌ "Connection timeout"
**Problem**: Wrong port or firewall blocking
**Solution**: 
- Use port 587 with TLS
- Check firewall/VPN settings

### ❌ "EMAIL_BACKEND is console"
**Problem**: EMAIL_BACKEND not set to smtp
**Solution**: Set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`

### ❌ "TLS and SSL both enabled"
**Problem**: EMAIL_USE_TLS=True and EMAIL_USE_SSL=True
**Solution**: Set `EMAIL_USE_SSL=False` for port 587

## Alternative: Port 465 (SSL)

If port 587 doesn't work, you can use port 465 with SSL:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Note**: Port 587 with TLS is recommended and more reliable.

## For Render Deployment

Add these to Render Environment Variables:

1. Go to Render Dashboard → Your Service → Environment
2. Add each variable:
   - `EMAIL_HOST` = `smtp.gmail.com`
   - `EMAIL_PORT` = `587`
   - `EMAIL_USE_TLS` = `True`
   - `EMAIL_USE_SSL` = `False`
   - `EMAIL_BACKEND` = `django.core.mail.backends.smtp.EmailBackend`
   - `EMAIL_HOST_USER` = `your-email@gmail.com`
   - `EMAIL_HOST_PASSWORD` = `your-16-char-app-password` (mark as Secret)
   - `DEFAULT_FROM_EMAIL` = `your-email@gmail.com`
3. Save and redeploy

## Summary

✅ **Your settings are correct:**
- `EMAIL_HOST=smtp.gmail.com` ✅
- `EMAIL_PORT=587` ✅

✅ **Also make sure you have:**
- `EMAIL_USE_TLS=True` ✅
- `EMAIL_USE_SSL=False` ✅
- `EMAIL_BACKEND=smtp.EmailBackend` ✅
- `EMAIL_HOST_PASSWORD=app-password` (not regular password) ✅

With these settings, interview link emails will be sent successfully! 🎉

