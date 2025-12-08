# 🔧 Fix SendGrid 403 Forbidden Error

## ❌ Error: HTTP Error 403: Forbidden

This error means SendGrid is rejecting the email request. The most common cause is that the **sender email is not verified**.

## ✅ Solution: Verify Sender Email in SendGrid

### Step 1: Log in to SendGrid
1. Go to https://app.sendgrid.com
2. Log in to your SendGrid account

### Step 2: Verify Single Sender
1. Click on **"Settings"** (gear icon) in the left sidebar
2. Click on **"Sender Authentication"**
3. Click on **"Verify a Single Sender"** button
4. Fill in the form:
   - **From Email Address**: `aditya24.rsl@gmail.com`
   - **From Name**: `AI Interview Platform` (or any name)
   - **Reply To**: `aditya24.rsl@gmail.com` (same as from email)
   - **Company Address**: Your company address
   - **City**: Your city
   - **State**: Your state
   - **Country**: Your country
   - **Zip Code**: Your zip code
5. Click **"Create"**

### Step 3: Verify Email
1. Check your email inbox (`aditya24.rsl@gmail.com`)
2. Look for an email from SendGrid
3. Click the **"Verify Single Sender"** link in the email
4. You'll be redirected to SendGrid dashboard showing "Verified ✅"

### Step 4: Test Again
After verification, run the test script again:
```bash
python test_sendgrid_email.py
```

## 🔍 Alternative: Check API Key Permissions

If verification doesn't work, check API key permissions:

1. Go to **Settings** → **API Keys**
2. Find your API key (starts with `SG.ojhPglHyQ6mgk3PVu...`)
3. Click **"Edit"**
4. Ensure **"Mail Send"** permission is enabled
5. Or select **"Full Access"** for testing
6. Click **"Update"**

## 🔄 Alternative: Regenerate API Key

If the API key is invalid:

1. Go to **Settings** → **API Keys**
2. Click **"Create API Key"**
3. Name: `Render Email Service`
4. Select **"Full Access"** or **"Mail Send"**
5. Click **"Create & View"**
6. **Copy the new API key** (starts with `SG.`)
7. Update `.env` file:
   ```
   SENDGRID_API_KEY=SG.your-new-api-key-here
   ```
8. Run test again

## ✅ After Fixing

Once the sender email is verified, the test email should send successfully!

You'll see:
```
✅ SUCCESS! Email sent successfully!
   send_mail() returned: 1
   Check inbox: paturkardhananjay9075@gmail.com
```

