# 🚨 CRITICAL: Fix Render Email & Interview Link Issues

## Problems Found:
1. ❌ **BACKEND_URL NOT SET** → Interview links use `localhost:8000` instead of Render URL
2. ❌ **Email timeout** → SMTP connection timing out (>30 seconds), causing worker timeout

## ✅ IMMEDIATE ACTION REQUIRED

### Step 1: Add BACKEND_URL to Render (CRITICAL!)

**This is the MOST IMPORTANT fix:**

1. Go to **Render Dashboard** → Your Backend Service → **Environment** tab
2. Click **"Add Environment Variable"**
3. Set:
   - **Key:** `BACKEND_URL`
   - **Value:** `https://aiinterviewerbackend-2.onrender.com`
   - **DO NOT** check "Secret" (this is a public URL)
4. Click **"Save Changes"**
5. Render will automatically redeploy

**After this, interview links will use Render URL instead of localhost!**

### Step 2: Verify Email Configuration

Make sure these are set in Render Environment Variables:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=aditya24.rsl@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=aditya24.rsl@gmail.com
```

**Important:** `EMAIL_HOST_PASSWORD` must be Gmail App Password (16 characters, no spaces)

### Step 3: Code Fixes Applied

I've made these code changes:
- ✅ Email sending is now **asynchronous** (won't timeout)
- ✅ Gunicorn timeout increased to 120 seconds
- ✅ Better error logging for BACKEND_URL

**After adding BACKEND_URL and redeploying, everything should work!**

## 🔍 How to Verify

After adding BACKEND_URL and redeploying:

1. **Check Render logs** for:
   - ✅ `Generated interview URL: https://aiinterviewerbackend-2.onrender.com/?session_key=xxx` (NOT localhost)
   - ✅ `✅ Interview notification sent via email successfully`
   - ✅ No `WORKER TIMEOUT` errors

2. **Test by scheduling an interview:**
   - Schedule a new interview for a candidate
   - Check candidate's email inbox
   - Verify interview link uses Render URL (not localhost)

## 📋 Complete Environment Variables Checklist

Make sure ALL these are set in Render:

```
✅ DJANGO_SECRET_KEY
✅ DJANGO_DEBUG=False
✅ DATABASE_URL
✅ USE_POSTGRESQL=True
✅ EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
✅ EMAIL_HOST=smtp.gmail.com
✅ EMAIL_PORT=587
✅ EMAIL_USE_TLS=True
✅ EMAIL_USE_SSL=False
✅ EMAIL_HOST_USER=aditya24.rsl@gmail.com
✅ EMAIL_HOST_PASSWORD=your-app-password
✅ DEFAULT_FROM_EMAIL=aditya24.rsl@gmail.com
✅ BACKEND_URL=https://aiinterviewerbackend-2.onrender.com  ← ADD THIS NOW!
✅ GEMINI_API_KEY
✅ DEEPGRAM_API_KEY (optional)
```

## ⚠️ Why Email Was Timing Out

The SMTP connection to Gmail was taking >30 seconds, causing Gunicorn worker timeout.

**Fix Applied:**
- Email sending is now **asynchronous** (runs in background thread)
- Won't block the HTTP request
- Won't cause worker timeout

## 🎯 Summary

**Action Required:**
1. ✅ Add `BACKEND_URL=https://aiinterviewerbackend-2.onrender.com` to Render
2. ✅ Verify email configuration is correct
3. ✅ Wait for Render to redeploy
4. ✅ Test by scheduling a new interview

**Code Changes:**
- ✅ Email sending is asynchronous (prevents timeout)
- ✅ Gunicorn timeout increased
- ✅ Better BACKEND_URL detection and warnings

After adding BACKEND_URL, interview links will work correctly and emails will send without timeout!

