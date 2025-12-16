# Render Environment Variables Setup Guide

## Quick Setup for Render Deployment

### Step 1: Go to Render Dashboard
1. Navigate to [Render Dashboard](https://dashboard.render.com)
2. Select your **Backend Service** (e.g., `aiinterviewerbackend`)
3. Click on **"Environment"** tab

### Step 2: Add Environment Variables

Add each of these variables one by one:

#### **Required Variables:**

```env
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DATABASE_URL=postgresql://ai_interview_platform_db_user:B5NCPLg8er6rFaKRUp6HWUnL7WjYt0GO@dpg-d4pt6ikhg0os73ftr9l0-a.singapore-postgres.render.com/ai_interview_platform_db
USE_POSTGRESQL=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
GEMINI_API_KEY=your-gemini-api-key
DEEPGRAM_API_KEY=your-deepgram-api-key
BACKEND_URL=https://aiinterviewerbackend-2.onrender.com
```

### Step 3: Generate Secret Key

Generate a Django secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and use it for `DJANGO_SECRET_KEY`.

### Step 4: Get Gmail App Password

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled
3. Go to **App passwords**
4. Select **Mail** and **Other (Custom name)** → Enter "Django"
5. Copy the 16-character password (no spaces)
6. Use this for `EMAIL_HOST_PASSWORD`

### Step 5: Get API Keys

#### Gemini API Key:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy and use for `GEMINI_API_KEY`

#### Deepgram API Key:
1. Go to [Deepgram Console](https://console.deepgram.com/)
2. Sign up/Login
3. Get your API key from dashboard
4. Use for `DEEPGRAM_API_KEY`

### Step 6: Update BACKEND_URL

Replace `BACKEND_URL` with your actual Render backend URL:
- Example: `https://aiinterviewerbackend-2.onrender.com`
- **Important**: No trailing slash!

### Step 7: Save and Deploy

1. Click **"Save Changes"** in Render
2. Render will automatically redeploy your service
3. Check deployment logs for any errors

## Complete Environment Variables List

### Core Django Settings
| Variable | Value | Required | Notes |
|----------|-------|----------|-------|
| `DJANGO_SECRET_KEY` | Random string | ✅ Yes | Generate using Django command |
| `DJANGO_DEBUG` | `False` | ✅ Yes | Always False in production |

### Database
| Variable | Value | Required | Notes |
|----------|-------|----------|-------|
| `DATABASE_URL` | PostgreSQL URL | ✅ Yes | From Render PostgreSQL dashboard |
| `USE_POSTGRESQL` | `True` | ✅ Yes | Enable PostgreSQL |

### Email Configuration
| Variable | Value | Required | Notes |
|----------|-------|----------|-------|
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | ✅ Yes | For actual email sending |
| `EMAIL_HOST` | `smtp.gmail.com` | ✅ Yes | Gmail SMTP server |
| `EMAIL_PORT` | `587` | ✅ Yes | Gmail port for TLS |
| `EMAIL_USE_TLS` | `True` | ✅ Yes | Required for port 587 |
| `EMAIL_USE_SSL` | `False` | ✅ Yes | Must be False for port 587 |
| `EMAIL_HOST_USER` | Your Gmail | ✅ Yes | Your Gmail address |
| `EMAIL_HOST_PASSWORD` | App Password | ✅ Yes | Gmail App Password (16 chars) |
| `DEFAULT_FROM_EMAIL` | Your Gmail | ✅ Yes | Sender email address |

### API Keys
| Variable | Value | Required | Notes |
|----------|-------|----------|-------|
| `GEMINI_API_KEY` | API key | ✅ Yes | From Google AI Studio |
| `DEEPGRAM_API_KEY` | API key | ⚠️ Optional | For speech-to-text features |

### URLs
| Variable | Value | Required | Notes |
|----------|-------|----------|-------|
| `BACKEND_URL` | Render URL | ✅ Yes | Your Render backend service URL |

## Verification

After deployment, check logs for:
- ✅ `[OK] Using PostgreSQL database from DATABASE_URL`
- ✅ `✅ Gemini API configured successfully`
- ✅ No email configuration errors

## Troubleshooting

### Email Not Sending
- Check `EMAIL_BACKEND` is set to `smtp.EmailBackend` (not `console`)
- Verify `EMAIL_HOST_PASSWORD` is Gmail App Password (not regular password)
- Ensure `EMAIL_USE_TLS=True` and `EMAIL_USE_SSL=False` for port 587

### Database Connection Failed
- Verify `DATABASE_URL` is correct from Render PostgreSQL dashboard
- Check database is not paused (free tier pauses after inactivity)
- Ensure `USE_POSTGRESQL=True`

### API Keys Not Working
- Verify API keys are correct and active
- Check API key permissions/quotas
- Review logs for specific error messages

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `.env` file to Git
- Use Render's "Secret" option for sensitive values
- Rotate API keys regularly
- Use strong `DJANGO_SECRET_KEY` in production
- Keep `DJANGO_DEBUG=False` in production



