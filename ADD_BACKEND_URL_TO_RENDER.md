# 🚨 URGENT: Add BACKEND_URL to Render NOW

## The Problem

Your logs show:
```
Generated interview URL: http://localhost:8000/?session_key=xxx
```

This means `BACKEND_URL` is **NOT SET** in Render environment variables!

## ✅ THE FIX (Do This Now!)

### Step-by-Step Instructions:

1. **Go to Render Dashboard**
   - Navigate to: https://dashboard.render.com
   - Click on your backend service: `aiinterviewerbackend`

2. **Open Environment Tab**
   - Click on **"Environment"** tab at the top

3. **Add BACKEND_URL Variable**
   - Click **"Add Environment Variable"** button
   - Enter:
     - **Key:** `BACKEND_URL`
     - **Value:** `https://aiinterviewerbackend-2.onrender.com`
     - **DO NOT** check "Secret" checkbox (this is a public URL)
   - Click **"Save Changes"**

4. **Wait for Redeploy**
   - Render will automatically redeploy your service
   - Wait 2-3 minutes for deployment to complete

5. **Verify**
   - Check Render logs
   - Look for: `Generated interview URL: https://aiinterviewerbackend-2.onrender.com/?session_key=xxx`
   - Should **NOT** say `localhost:8000` anymore

## 📧 Email Timeout Fix

I've also fixed the email timeout issue:
- ✅ Email sending is now **asynchronous** (won't cause worker timeout)
- ✅ Gunicorn timeout increased to 120 seconds
- ✅ Email sends in background thread

## ✅ After Adding BACKEND_URL

1. Interview links will use: `https://aiinterviewerbackend-2.onrender.com/?session_key=xxx`
2. Emails will send without timeout
3. Candidates can access interviews from any computer

## ⚠️ Important Notes

- **BACKEND_URL** must be your Render backend URL
- Use `https://` not `http://`
- **NO trailing slash** (correct: `https://aiinterviewerbackend-2.onrender.com`)
- This is a **public URL**, don't mark as "Secret"

## 🎯 Summary

**ACTION REQUIRED:**
1. Add `BACKEND_URL=https://aiinterviewerbackend-2.onrender.com` to Render Environment Variables
2. Wait for redeploy
3. Test by scheduling a new interview

**Code Already Fixed:**
- ✅ Email sending is asynchronous (no timeout)
- ✅ Better BACKEND_URL detection
- ✅ Improved error logging

**After adding BACKEND_URL, everything will work!** 🎉

