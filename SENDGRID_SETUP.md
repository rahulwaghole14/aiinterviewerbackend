# 📧 SendGrid Email Setup Guide

## Why SendGrid?

SendGrid is recommended for Render deployments because:
- ✅ More reliable than Gmail SMTP (no network blocking issues)
- ✅ Better for cloud deployments
- ✅ Free tier: 100 emails/day
- ✅ No App Password setup needed
- ✅ Better deliverability

## 🚀 Quick Setup Steps

### Step 1: Create SendGrid Account

1. Go to https://sendgrid.com
2. Sign up for a free account
3. Verify your email address

### Step 2: Create API Key

1. Log in to SendGrid dashboard
2. Go to **Settings** → **API Keys**
3. Click **"Create API Key"**
4. Name it: `Render Email Service`
5. Select **"Full Access"** or **"Mail Send"** permissions
6. Click **"Create & View"**
7. **Copy the API key** (starts with `SG.`) - you won't see it again!

### Step 3: Verify Sender Email

1. Go to **Settings** → **Sender Authentication**
2. Click **"Verify a Single Sender"**
3. Enter your email (e.g., `aditya24.rsl@gmail.com`)
4. Fill in the form and submit
5. Check your email and click the verification link

### Step 4: Add to Render Environment Variables

1. Go to Render Dashboard → Your Backend Service
2. Click **"Environment"** tab
3. Add these variables:

```
USE_SENDGRID=True
SENDGRID_API_KEY=SG.your-api-key-here
DEFAULT_FROM_EMAIL=aditya24.rsl@gmail.com
```

4. Mark `SENDGRID_API_KEY` as **"Secret"**
5. Click **"Save Changes"**

### Step 5: Deploy

The code will automatically use SendGrid when `USE_SENDGRID=True` is set.

## ✅ Verification

After deployment, schedule a test interview. Check Render logs for:

```
[EMAIL DEBUG] Using SendGrid API
[SUCCESS] Interview notification email sent successfully via SendGrid!
```

## 🔧 Troubleshooting

### Error: "SENDGRID_API_KEY is not set"
- Make sure `USE_SENDGRID=True` is set
- Make sure `SENDGRID_API_KEY` is set and marked as Secret

### Error: "From email is not verified"
- Verify your sender email in SendGrid dashboard
- Wait a few minutes after verification

### Error: "API key is invalid"
- Regenerate API key in SendGrid
- Make sure you copied the full key (starts with `SG.`)

## 📊 SendGrid Free Tier Limits

- **100 emails/day** (free tier)
- **Unlimited** emails/month (free tier)
- Upgrade to paid plan for more emails/day

## 🔄 Switching Back to Gmail SMTP

If you want to use Gmail instead:

1. Set `USE_SENDGRID=False` in Render
2. Add Gmail SMTP variables (see `RENDER_ENVIRONMENT_VARIABLES.md`)

