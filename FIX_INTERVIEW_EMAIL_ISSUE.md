# Fix: Interview Email Not Received / Wrong Interview Link

## ✅ Good News: Email IS Being Sent!

The test confirmed that:
- ✅ Email configuration is correct
- ✅ Email was sent successfully to: `paturakrdhananjay9075@gmail.com`
- ✅ SMTP connection is working

## ❌ Problem Found: BACKEND_URL Not Set

The interview link in the email is using `localhost:8000` instead of your Render URL because `BACKEND_URL` is not configured.

**Current (Wrong):**
```
http://localhost:8000/?session_key=xxx
```

**Should Be:**
```
https://aiinterviewerbackend-2.onrender.com/?session_key=xxx
```

## 🔧 Solution: Add BACKEND_URL

### For Local Development (.env file)

Add this line to your `.env` file (around line 50-55):

```env
BACKEND_URL=https://aiinterviewerbackend-2.onrender.com
```

**Important:** 
- Use your actual Render backend URL
- No trailing slash!
- Use `https://` not `http://`

### For Render Deployment

1. Go to **Render Dashboard** → Your Backend Service → **Environment**
2. Click **"Add Environment Variable"**
3. Set:
   - **Key:** `BACKEND_URL`
   - **Value:** `https://aiinterviewerbackend-2.onrender.com`
   - (Replace with your actual Render backend URL)
4. Click **"Save Changes"**
5. Render will automatically redeploy

## 📧 Check Your Email

1. **Check Inbox** at `paturakrdhananjay9075@gmail.com`
2. **Check Spam/Junk Folder** - Gmail sometimes filters automated emails
3. **Search for:** "Interview Scheduled" or "Data Science intern_06_12"

## 🔍 What to Look For in Email

The email should contain:
- Subject: "Interview Scheduled - [Job Title] at [Company]"
- Interview details (date, time, duration)
- Interview link (currently pointing to localhost, will be fixed after adding BACKEND_URL)

## 📋 Complete .env Configuration

Make sure your `.env` file has these lines (check lines 15-17 and 26-27 you mentioned):

```env
# Database (lines 15-17)
DATABASE_URL=postgresql://ai_interview_platform_db_user:B5NCPLg8er6rFaKRUp6HWUnL7WjYt0GO@dpg-d4pt6ikhg0os73ftr9l0-a.singapore-postgres.render.com/ai_interview_platform_db
USE_POSTGRESQL=True

# Email (lines 26-27)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=aditya24.rsl@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=aditya24.rsl@gmail.com

# Backend URL (ADD THIS - around line 50)
BACKEND_URL=https://aiinterviewerbackend-2.onrender.com
```

## ✅ After Adding BACKEND_URL

1. Restart your Django server (if local)
2. Or wait for Render to redeploy (if on Render)
3. Schedule a new interview or resend the email
4. The interview link will now point to your Render URL instead of localhost

## 🧪 Test Again

After adding BACKEND_URL, run:
```bash
python test_interview_email.py
```

This will verify:
- ✅ Email is sent
- ✅ Interview link uses correct Render URL
- ✅ All configuration is correct

## Summary

**Issue:** BACKEND_URL not set → Interview links use localhost  
**Fix:** Add `BACKEND_URL=https://your-render-url.onrender.com` to .env and Render  
**Status:** Email sending works ✅, just need to fix the URL in the link

