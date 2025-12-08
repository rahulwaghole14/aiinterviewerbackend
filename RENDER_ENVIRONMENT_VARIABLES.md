# Complete Render Environment Variables Configuration

## 📋 All Environment Variables for Render Deployment

Copy and paste these into your Render Dashboard → Backend Service → Environment tab.

---

## 🔐 **1. Django Core Settings**

```env
DJANGO_SECRET_KEY=your-secret-key-here-generate-strong-key
DJANGO_DEBUG=False
```

**How to generate SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🗄️ **2. Database Configuration (PostgreSQL)**

```env
DATABASE_URL=postgresql://ai_interview_platform_db_user:B5NCPLg8er6rFaKRUp6HWUnL7WjYt0GO@dpg-d4pt6ikhg0os73ftr9l0-a.singapore-postgres.render.com/ai_interview_platform_db
USE_POSTGRESQL=True
```

**Note:** Use your actual PostgreSQL database URL from Render PostgreSQL dashboard.

---

## 📧 **3. Email Configuration (Gmail SMTP)**

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=aditya24.rsl@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password-here
DEFAULT_FROM_EMAIL=aditya24.rsl@gmail.com
```

**Important:**
- `EMAIL_HOST_PASSWORD` must be Gmail App Password (16 characters, no spaces)
- Generate at: https://myaccount.google.com/apppasswords
- Mark this as **"Secret"** in Render

---

## 🔗 **4. Backend URL (For Interview Links)**

```env
BACKEND_URL=https://aiinterviewerbackend-2.onrender.com
```

**Important:**
- Replace with your actual Render backend service URL
- No trailing slash!
- Use `https://` not `http://`

---

## 🤖 **5. AI/ML API Keys**

```env
GEMINI_API_KEY=your-gemini-api-key-here
DEEPGRAM_API_KEY=your-deepgram-api-key-here
```

**How to get:**
- **GEMINI_API_KEY:** https://makersuite.google.com/app/apikey
- **DEEPGRAM_API_KEY:** https://console.deepgram.com/

**Note:** Mark these as **"Secret"** in Render

---

## 📝 **Complete List (Copy All)**

Here's the complete list to copy into Render:

```
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DATABASE_URL=postgresql://ai_interview_platform_db_user:B5NCPLg8er6rFaKRUp6HWUnL7WjYt0GO@dpg-d4pt6ikhg0os73ftr9l0-a.singapore-postgres.render.com/ai_interview_platform_db
USE_POSTGRESQL=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=aditya24.rsl@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=aditya24.rsl@gmail.com
BACKEND_URL=https://aiinterviewerbackend-2.onrender.com
GEMINI_API_KEY=your-gemini-api-key
DEEPGRAM_API_KEY=your-deepgram-api-key
```

---

## 🚀 **Step-by-Step: Adding to Render**

### Step 1: Go to Render Dashboard
1. Navigate to https://dashboard.render.com
2. Click on your **Backend Service** (e.g., `aiinterviewerbackend`)

### Step 2: Open Environment Tab
1. Click on **"Environment"** tab
2. You'll see existing environment variables (if any)

### Step 3: Add Each Variable
For each variable above:

1. Click **"Add Environment Variable"** button
2. Enter the **Key** (left side)
3. Enter the **Value** (right side)
4. For sensitive values (passwords, API keys), check **"Secret"** checkbox
5. Click **"Save Changes"**

### Step 4: Variables to Mark as "Secret"
Mark these as **Secret** (they won't be visible in logs):
- `DJANGO_SECRET_KEY`
- `EMAIL_HOST_PASSWORD`
- `GEMINI_API_KEY`
- `DEEPGRAM_API_KEY`
- `DATABASE_URL` (contains password)

### Step 5: Save and Deploy
1. After adding all variables, click **"Save Changes"**
2. Render will automatically redeploy your service
3. Wait for deployment to complete (check logs)

---

## ✅ **Verification Checklist**

After deployment, verify these in Render logs:

- ✅ `[OK] Using PostgreSQL database from DATABASE_URL`
- ✅ `✅ Gemini API configured successfully`
- ✅ No email configuration errors
- ✅ No `EMAIL_BACKEND is set to console` warnings
- ✅ Application starts successfully

---

## 🔍 **Troubleshooting**

### Email Not Sending
- Check `EMAIL_BACKEND` is `smtp.EmailBackend` (not `console`)
- Verify `EMAIL_HOST_PASSWORD` is Gmail App Password
- Ensure `EMAIL_USE_TLS=True` and `EMAIL_USE_SSL=False` for port 587

### Database Connection Failed
- Verify `DATABASE_URL` is correct from Render PostgreSQL dashboard
- Check database is not paused (free tier pauses after inactivity)
- Ensure `USE_POSTGRESQL=True`

### Interview Links Wrong
- Check `BACKEND_URL` is your Render backend URL (not localhost)
- No trailing slash in `BACKEND_URL`
- Use `https://` not `http://`

### API Keys Not Working
- Verify API keys are correct and active
- Check API key permissions/quotas
- Review logs for specific error messages

---

## 📊 **Quick Reference Table**

| Variable | Value | Required | Secret |
|----------|-------|----------|--------|
| `DJANGO_SECRET_KEY` | Generated key | ✅ Yes | ✅ Yes |
| `DJANGO_DEBUG` | `False` | ✅ Yes | ❌ No |
| `DATABASE_URL` | PostgreSQL URL | ✅ Yes | ✅ Yes |
| `USE_POSTGRESQL` | `True` | ✅ Yes | ❌ No |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | ✅ Yes | ❌ No |
| `EMAIL_HOST` | `smtp.gmail.com` | ✅ Yes | ❌ No |
| `EMAIL_PORT` | `587` | ✅ Yes | ❌ No |
| `EMAIL_USE_TLS` | `True` | ✅ Yes | ❌ No |
| `EMAIL_USE_SSL` | `False` | ✅ Yes | ❌ No |
| `EMAIL_HOST_USER` | Your Gmail | ✅ Yes | ❌ No |
| `EMAIL_HOST_PASSWORD` | Gmail App Password | ✅ Yes | ✅ Yes |
| `DEFAULT_FROM_EMAIL` | Your Gmail | ✅ Yes | ❌ No |
| `BACKEND_URL` | Your Render URL | ✅ Yes | ❌ No |
| `GEMINI_API_KEY` | API key | ✅ Yes | ✅ Yes |
| `DEEPGRAM_API_KEY` | API key | ⚠️ Optional | ✅ Yes |

---

## 🎯 **Summary**

**Total Variables to Add:** 15

**Required:** 14  
**Optional:** 1 (DEEPGRAM_API_KEY)

**Mark as Secret:** 5 variables (passwords and API keys)

After adding all variables and redeploying, your application will:
- ✅ Connect to PostgreSQL database
- ✅ Send interview emails via Gmail
- ✅ Generate correct interview links
- ✅ Use AI features (Gemini, Deepgram)

---

## 📞 **Need Help?**

If deployment fails:
1. Check Render deployment logs
2. Verify all environment variables are set correctly
3. Ensure no typos in variable names or values
4. Check that secrets are marked as "Secret"

