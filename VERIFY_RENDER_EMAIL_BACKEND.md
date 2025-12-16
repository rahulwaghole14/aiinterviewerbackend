# Verify Email Backend on Render

## ✅ Yes, Your Email Backend Should Be:

```
django.core.mail.backends.smtp.EmailBackend
```

## How to Check/Set on Render

### Step 1: Go to Render Dashboard
1. Navigate to [Render Dashboard](https://dashboard.render.com)
2. Select your **Backend Service** (e.g., `aiinterviewerbackend`)
3. Click on **"Environment"** tab

### Step 2: Check EMAIL_BACKEND Variable

Look for the environment variable:
- **Key:** `EMAIL_BACKEND`
- **Value:** Should be `django.core.mail.backends.smtp.EmailBackend`

### Step 3: If Not Set or Wrong

1. Click **"Add Environment Variable"** (or edit existing)
2. Set:
   - **Key:** `EMAIL_BACKEND`
   - **Value:** `django.core.mail.backends.smtp.EmailBackend`
3. Click **"Save Changes"**
4. Render will automatically redeploy

## ❌ Wrong Values (Will NOT Send Emails)

These values will NOT send actual emails:

- ❌ `django.core.mail.backends.console.EmailBackend` (prints to console only)
- ❌ `django.core.mail.backends.locmem.EmailBackend` (stores in memory only)
- ❌ `django.core.mail.backends.filebased.EmailBackend` (saves to file only)

## ✅ Correct Value (Will Send Emails)

- ✅ `django.core.mail.backends.smtp.EmailBackend` (sends via SMTP)

## Complete Email Configuration for Render

Make sure you have ALL these environment variables set:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

## Quick Verification

After setting on Render, check the deployment logs for:
- ✅ No errors about email configuration
- ✅ No "EMAIL_BACKEND is set to console" warnings
- ✅ Successful email sending in logs (if testing)

## Test After Deployment

Once deployed, you can test by:
1. Scheduling an interview for a candidate
2. Check if the candidate receives the email
3. Check Render logs for email sending status

## Summary

✅ **Your email backend should be:**
```
django.core.mail.backends.smtp.EmailBackend
```

✅ **Verify it's set correctly on Render dashboard**
✅ **Make sure it's NOT set to `console` backend**


