# 🚨 FINAL FIX: Email Sending & BACKEND_URL Issues

## Problems Identified:

1. ❌ **BACKEND_URL NOT SET** - Logs show: `⚠️ BACKEND_URL not set in Render!`
2. ❌ **Email sending timing out** - No success/failure message after `send_mail()` call
3. ❌ **Worker timeout on startup** - TextBlob/NLTK import causing 30s timeout

## ✅ Code Fixes Applied:

### 1. Made TextBlob Import Optional (Prevents Startup Timeout)
- TextBlob now imports lazily with try/except
- Prevents NLTK data download from blocking startup

### 2. Added Email Timeout Handling
- 30-second timeout for SMTP connections
- Better error messages for timeout vs other errors
- Prevents worker timeout during email sending

### 3. Improved BACKEND_URL Detection
- Better warnings when BACKEND_URL is not set
- Clear instructions in logs

## 🚨 CRITICAL ACTION REQUIRED:

### Add BACKEND_URL to Render Environment Variables

**This is the MOST IMPORTANT step:**

1. Go to **Render Dashboard** → Your Backend Service (`aiinterviewerbackend`)
2. Click **"Environment"** tab
3. Click **"Add Environment Variable"**
4. Enter:
   - **Key:** `BACKEND_URL`
   - **Value:** `https://aiinterviewerbackend-2.onrender.com`
   - **DO NOT** check "Secret"
5. Click **"Save Changes"**
6. Wait for Render to redeploy (2-3 minutes)

**After this, interview links will use Render URL instead of localhost!**

## 📧 Email Configuration Checklist

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
BACKEND_URL=https://aiinterviewerbackend-2.onrender.com  ← ADD THIS!
```

**Important:** `EMAIL_HOST_PASSWORD` must be Gmail App Password (16 characters, no spaces)

## 🔍 How to Verify Email is Working

After adding BACKEND_URL and redeploying:

1. **Check Render logs** for:
   - ✅ `Generated interview URL: https://aiinterviewerbackend-2.onrender.com/?session_key=xxx` (NOT localhost)
   - ✅ `✅ Interview notification sent via email successfully`
   - ✅ No timeout errors

2. **Test by scheduling an interview:**
   - Schedule a new interview
   - Check candidate's email inbox
   - Verify interview link uses Render URL

## ⚠️ Common Email Issues

### If email still doesn't send:

1. **Check Render logs** for specific error messages
2. **Verify EMAIL_HOST_PASSWORD** is Gmail App Password (not regular password)
3. **Check SMTP timeout** - If you see timeout errors, Gmail might be blocking
4. **Verify EMAIL_BACKEND** is `django.core.mail.backends.smtp.EmailBackend` (not `console`)

### If you see "SMTP connection timeout":
- Gmail might be blocking Render's IP
- Try using a different email provider (SendGrid, Mailgun)
- Or upgrade Render plan for better network

## 📋 Summary

**Code Fixed:**
- ✅ TextBlob lazy loading (prevents startup timeout)
- ✅ Email timeout handling (30s timeout)
- ✅ Better error messages

**Action Required:**
- ✅ Add `BACKEND_URL=https://aiinterviewerbackend-2.onrender.com` to Render
- ✅ Verify email configuration is correct
- ✅ Test by scheduling a new interview

**After adding BACKEND_URL, everything should work!** 🎉

