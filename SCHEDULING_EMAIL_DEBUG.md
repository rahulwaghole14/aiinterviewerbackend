# Scheduling Email Debugging Guide

## Issues Found

### 1. "Not Found" Errors (Harmless)
The following 404 errors are **harmless** and don't affect email sending:
- `/api/evaluation/crud/` - Frontend trying to access non-existent endpoint
- `/api/requests/pending` - Frontend trying to access non-existent endpoint

These can be ignored or fixed by adding the endpoints later.

### 2. Email Not Sending (Real Issue)
The real problem is that emails aren't being sent when scheduling interviews. This could be because:
- `book_slot` endpoint is not being called successfully (400 error)
- `book_slot` is called but email sending fails silently
- `book_slot` is not being called at all

## Debugging Steps

### Step 1: Check Terminal Logs
When scheduling an interview, look for:
```
DEBUG: book_slot called for slot ...
DEBUG: Request data: ...
DEBUG: interview_id from data_source: ...
```

If you DON'T see these logs, `book_slot` is not being called.

### Step 2: Check Browser Console
Open browser developer console (F12) and look for:
```
=== CREATING SCHEDULE RELATIONSHIP ===
Sending booking data: { interview_id: "...", booking_notes: "..." }
Schedule creation response status: 400 (or 201)
```

If status is 400, check the error message in console.

### Step 3: Check Email Logs
If `book_slot` is called successfully, you should see:
```
EMAIL: Starting email send for interview ...
EMAIL: Configuration check:
EMAIL: Sending interview notification email
[SUCCESS] Interview notification email sent successfully!
```

If you don't see these, email sending is failing.

## Enhanced Debugging Added

I've added more detailed logging to `book_slot`:
- Shows all request data sources
- Shows interview_id extraction attempts
- Shows detailed error messages with all data sources

## Testing

Try scheduling an interview and check:
1. **Terminal logs** - Should show `DEBUG: book_slot called...`
2. **Browser console** - Should show `Schedule creation response status: 201`
3. **Terminal logs** - Should show `EMAIL: Starting email send...`

If any step fails, the logs will show exactly what went wrong.

## Common Issues

### Issue 1: book_slot Returns 400
**Symptom**: Browser console shows "Schedule creation response status: 400"
**Cause**: `interview_id` not being sent correctly
**Fix**: Check browser console for the exact error message

### Issue 2: book_slot Returns 201 but No Email
**Symptom**: Terminal shows "SUCCESS: Slot booking completed" but no email logs
**Cause**: Email sending code not executing or failing silently
**Fix**: Check terminal for email configuration errors

### Issue 3: No book_slot Call at All
**Symptom**: No `DEBUG: book_slot` logs in terminal
**Cause**: Frontend not calling `book_slot` endpoint
**Fix**: Check browser console for JavaScript errors

## Next Steps

1. Schedule an interview via the UI
2. Check terminal for `DEBUG: book_slot` logs
3. Check browser console for response status
4. Check terminal for email sending logs
5. Report what you see in each step

