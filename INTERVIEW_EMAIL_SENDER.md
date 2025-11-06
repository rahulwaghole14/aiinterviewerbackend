# Interview Email Sender Script

## Overview
This script (`send_interview_emails.py`) uses the **exact same email sending functionality** as `test_email_sending_live.py` to send interview scheduling emails to candidates.

## Key Features

### ✅ Same Reliable Approach
- Uses same email sending logic as `test_email_sending_live.py`
- Same TLS/SSL conflict handling
- Same configuration validation
- Same error handling

### ✅ Gets Candidate Email from Scheduled Interviews
- Finds all scheduled interviews from database
- Extracts candidate email from `interview.candidate.email`
- Gets interview details (job, company, time, link)

### ✅ Sends Interview Scheduling Message
- Personalized email with candidate name
- Interview details (date, time in IST, duration)
- Interview link for joining
- Important instructions

## Usage

### Option 1: Interactive Mode
```bash
python send_interview_emails.py
```
Shows list of scheduled interviews and lets you choose which to send.

### Option 2: Send to All
```bash
python send_interview_emails.py --all
```
Sends emails to all scheduled interviews.

### Option 3: Send to Specific Interview
```bash
python send_interview_emails.py <interview_id>
```
Sends email to a specific interview by ID.

## Email Content

The email includes:
- **Subject**: "Interview Scheduled - [Job Title] at [Company Name]"
- **Personalized greeting**: "Dear [Candidate Name]"
- **Interview Details**:
  - Position/Job Title
  - Company Name
  - Date & Time (in IST)
  - End Time (in IST)
  - Duration
  - Interview Type
- **Interview Link**: Clickable URL to join the interview
- **Important Instructions**: 
  - Join 5-10 minutes early
  - Link activation timing
  - Technical requirements
  - ID verification reminder

## How It Works

1. **Loads Django settings** (same as test script)
2. **Finds scheduled interviews** from database
3. **Gets candidate email** from `interview.candidate.email`
4. **Gets interview details**:
   - Job title, company name
   - Interview times (converted to IST)
   - Interview link/URL
5. **Validates email config** (same checks as test script)
6. **Sends email** using same `send_mail()` approach
7. **Shows summary** of sent/failed emails

## Email Configuration

Uses same configuration as `test_email_sending_live.py`:
- Reads from `.env` via Django settings
- Auto-fixes TLS/SSL conflicts
- Validates all settings before sending
- Provides clear error messages

## Integration

This script can be used:
- **Manually**: Run when you want to send interview emails
- **Automated**: Can be scheduled via cron/scheduler
- **On-demand**: After scheduling interviews via the UI

The notification service (`notifications/services.py`) also uses the same approach automatically when interviews are scheduled through the UI.

## Example Output

```
======================================================================
  Send Interview Emails to Candidates
======================================================================

Found 5 scheduled interview(s)

Sending interview email to: candidate@example.com
   Interview ID: abc-123-def
   Candidate: John Doe
   Scheduled Time: January 15, 2025 at 2:00 PM IST
   Interview URL: http://localhost:8000/?session_key=xyz789
[SUCCESS] Interview email sent successfully to candidate@example.com!

Summary:
  Total: 5
  Sent: 5
  Failed: 0
```

## Files

- `send_interview_emails.py` - Main script to send interview emails
- `test_email_sending_live.py` - Test script (same email sending approach)
- `notifications/services.py` - Automatic notification service (uses same approach)

All three use the **exact same reliable email sending mechanism**!

