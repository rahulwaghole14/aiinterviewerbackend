# Scheduling Interview Issues - Fix Guide

## Issue 1: "Not Found" Errors (Harmless - Can Ignore)

The terminal shows these 404 errors:
```
Not Found: /api/evaluation/crud/
Not Found: /api/requests/pending
```

**These are HARMLESS** - they're just the frontend trying to access endpoints that don't exist. They don't affect email sending or interview scheduling.

### To Fix (Optional):
Add these endpoints to your Django URLs if you want to remove the warnings, but they're not critical.

---

## Issue 2: Email Not Sending (Real Problem - Needs Fix)

Emails aren't being sent when scheduling interviews. Here's how to debug:

### Step 1: Check if `book_slot` is Called

When you schedule an interview, look in the **terminal** for:
```
======================================================================
DEBUG: book_slot called for slot ...
DEBUG: Request method: POST
DEBUG: Request data: ...
```

**If you DON'T see this**, the frontend isn't calling `book_slot` - check browser console for JavaScript errors.

### Step 2: Check if `interview_id` is Received

In the terminal, look for:
```
DEBUG: interview_id from data_source: <some-uuid>
```

**If you see `None`**, the `interview_id` isn't being sent correctly from the frontend.

**I've fixed this** by improving `interview_id` extraction from multiple sources (request.data, request.body, etc.)

### Step 3: Check Email Sending

If `book_slot` succeeds, you should see:
```
EMAIL: Starting email send for interview ...
EMAIL: Configuration check:
  EMAIL_BACKEND: ...
  EMAIL_HOST: ...
EMAIL: Sending interview notification email
[SUCCESS] Interview notification email sent successfully!
```

**If you DON'T see these logs**, email sending failed. Check for:
```
[EMAIL NOT SENT] ...
[EMAIL FAILED] ...
```

### Step 4: Check Browser Console

Open browser developer console (F12) and look for:
```
=== CREATING SCHEDULE RELATIONSHIP ===
Sending booking data: { interview_id: "...", booking_notes: "..." }
Schedule creation response status: 201 (or 400)
```

**If status is 400**, check the error message in the console.

---

## What I Fixed

### 1. Enhanced `interview_id` Extraction
- Now tries multiple sources: `request.data`, `request.body`, `data_source`
- Better error messages showing all data sources
- More detailed debug logging

### 2. Email Sending Flow
- `book_slot` calls `NotificationService.send_candidate_interview_scheduled_notification(interview)` at line 1138
- This uses the same reliable email sending approach as the test script
- Detailed logging for email configuration and sending status

---

## Testing Steps

1. **Schedule an interview** via the UI
2. **Check terminal** for:
   - `DEBUG: book_slot called...` ✅
   - `DEBUG: interview_id from data_source: <uuid>` ✅
   - `EMAIL: Starting email send...` ✅
   - `[SUCCESS] Email sent...` ✅

3. **Check browser console** (F12) for:
   - `Schedule creation response status: 201` ✅
   - No JavaScript errors ✅

4. **Check email inbox** for interview link email ✅

---

## Common Issues & Fixes

### Issue: `book_slot` Returns 400
**Symptom**: Browser console shows `Schedule creation response status: 400`
**Cause**: `interview_id` not being sent correctly
**Fix**: Check terminal for detailed error message showing what data was received

### Issue: `book_slot` Succeeds but No Email
**Symptom**: Terminal shows `SUCCESS: Slot booking completed` but no email logs
**Cause**: Email configuration issue or email sending code not executing
**Fix**: Check terminal for `[EMAIL NOT SENT]` or `[EMAIL FAILED]` messages

### Issue: No `book_slot` Call at All
**Symptom**: No `DEBUG: book_slot` logs in terminal
**Cause**: Frontend JavaScript error or API call not being made
**Fix**: Check browser console for JavaScript errors

---

## Next Steps

1. **Try scheduling an interview** and watch the terminal
2. **Report what you see**:
   - Do you see `DEBUG: book_slot called...`? ✅/❌
   - Do you see `DEBUG: interview_id from data_source: <uuid>`? ✅/❌
   - Do you see `EMAIL: Starting email send...`? ✅/❌
   - Do you see `[SUCCESS] Email sent...`? ✅/❌
   - What's the browser console response status? (201/400/500)

This will help identify exactly where the issue is!

