# How to Disable SendGrid Click Tracking

## Problem
SendGrid is wrapping interview links with tracking URLs instead of sending direct links:
- **Bad**: `https://u57887134.ct.sendgrid.net/ls/click?upn=...`
- **Good**: `https://aiinterviewerbackend-2.onrender.com/interview/?session_key=xxx`

## Solution 1: Disable in SendGrid Dashboard (Recommended)

1. **Login to SendGrid Dashboard**: https://app.sendgrid.com
2. **Go to Settings → Tracking**:
   - Click on "Settings" in the left sidebar
   - Click on "Tracking"
3. **Disable ALL Click Tracking Options**:
   - **"Click Tracking"**: Set to **DISABLED** ✅
   - **"Also enable click tracking in plain text emails"**: Set to **DISABLED** ✅ (IMPORTANT - Our emails are plain text!)
   - **"Track links in emails that are clicked"**: Set to **DISABLED** ✅
4. **Save Changes**

**CRITICAL**: Since we send **plain text emails**, you MUST disable "Also enable click tracking in plain text emails" - this is likely why links are still being wrapped even if main click tracking is disabled!

## Solution 2: Code-Level Fix (Already Implemented)

The code now uses SendGrid API directly with click tracking disabled per email:

```python
mail.tracking_settings = {
    "click_tracking": {
        "enable": False
    }
}
```

However, if the SendGrid API call fails, it falls back to Django's `send_mail()` which may still have click tracking enabled.

## Solution 3: Verify SendGrid Package

Make sure `sendgrid` package is installed:
```bash
pip install sendgrid>=3.5.0,<4.0.0
```

## Recommended Action

**Disable click tracking in SendGrid Dashboard** (Solution 1) - this is the most reliable method and will ensure all emails have direct links.

## After Disabling

1. Test by scheduling a new interview
2. Check the email - the interview link should be direct:
   - ✅ `https://aiinterviewerbackend-2.onrender.com/interview/?session_key=xxx`
   - ❌ NOT `https://u57887134.ct.sendgrid.net/ls/click?upn=...`

