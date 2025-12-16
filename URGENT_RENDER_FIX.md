# 🚨 URGENT: Fix Render Deployment Issues

## Problems Found:
1. ❌ **BACKEND_URL not set** → Interview links use `localhost:8000` instead of Render URL
2. ❌ **Email not sending** → Need to check email configuration and errors

## ✅ IMMEDIATE FIX: Add BACKEND_URL to Render

### Step 1: Go to Render Dashboard
1. Navigate to https://dashboard.render.com
2. Click on your **Backend Service** (`aiinterviewerbackend`)
3. Click **"Environment"** tab

### Step 2: Add BACKEND_URL
1. Click **"Add Environment Variable"**
2. Set:
   - **Key:** `BACKEND_URL`
   - **Value:** `https://aiinterviewerbackend-2.onrender.com`
   - (Replace with your actual Render backend URL - NO trailing slash!)
3. Click **"Save Changes"**

### Step 3: Verify Email Configuration
Make sure these are set correctly:

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

### Step 4: Check Render Logs
After redeploy, check logs for:
- ✅ `BACKEND_URL` is being used (not localhost)
- ✅ Email sending errors (if any)
- ✅ Any SMTP connection errors

## 🔍 Debugging Email Issues

If email still doesn't send, check Render logs for:
1. **SMTP Authentication errors** → Check EMAIL_HOST_PASSWORD is App Password
2. **Connection timeout** → Check EMAIL_HOST and EMAIL_PORT
3. **TLS/SSL errors** → Ensure EMAIL_USE_TLS=True and EMAIL_USE_SSL=False for port 587

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
✅ BACKEND_URL=https://aiinterviewerbackend-2.onrender.com  ← ADD THIS!
✅ GEMINI_API_KEY
✅ DEEPGRAM_API_KEY (optional)
```

## 🎯 After Adding BACKEND_URL

1. Render will automatically redeploy
2. Wait for deployment to complete
3. Test by scheduling a new interview
4. Check email - link should now use Render URL instead of localhost

## ⚠️ Important Notes

- **BACKEND_URL** must be your Render backend URL (not localhost)
- Use `https://` not `http://`
- **NO trailing slash** (e.g., `https://aiinterviewerbackend-2.onrender.com` not `https://aiinterviewerbackend-2.onrender.com/`)
- Email will only work if EMAIL_BACKEND is `smtp.EmailBackend` (not `console`)


