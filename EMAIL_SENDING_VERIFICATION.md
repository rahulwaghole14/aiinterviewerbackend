# Email Sending Verification & Troubleshooting

## ✅ Implementation Status

### **Auto-Email Sending in Both Endpoints**

1. **`book_interview` endpoint** (`/api/interviews/schedules/book_interview/`)
   - ✅ Auto-creates InterviewSession
   - ✅ Sends email using `send_interview_session_email`
   - ✅ Email includes interview link with session_key

2. **`book_slot` endpoint** (`/api/interviews/slots/{id}/book_slot/`)
   - ✅ Auto-creates InterviewSession (just added)
   - ✅ Sends email using `send_interview_session_email`
   - ✅ Email includes interview link with session_key

3. **`NotificationService.send_candidate_interview_scheduled_notification`**
   - ✅ Improved to fetch session_key from InterviewSession if not in Interview
   - ✅ Generates proper interview URL
   - ✅ Sends email with interview link

---

## 🔍 How to Verify Email is Sending

### Check Server Logs

When an interview is scheduled, look for these messages:

**Success Messages:**
```
✅ InterviewSession created for interview {id}, session_key: {key}
✅ Email sent to {email} with interview link: {link}
```

**Failure Messages:**
```
⚠️ Email sending failed for {email} - check email configuration
[EMAIL NOT SENT] EMAIL_BACKEND is 'console'
[EMAIL NOT SENT] EMAIL_HOST is not set
[EMAIL NOT SENT] Email credentials incomplete
```

---

## ⚙️ Email Configuration Required

### **`.env` File Settings:**

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### **Important for Gmail:**
- ❌ **Don't use** your regular Gmail password
- ✅ **Use** Google App Password (16 characters)
- Generate at: https://myaccount.google.com/apppasswords

---

## 🔧 Debugging Steps

### 1. **Check if InterviewSession is Created**

```python
# In Django shell
from interview_app.models import InterviewSession
from interviews.models import Interview

interview = Interview.objects.get(id='<interview-id>')
print(f"Session key: {interview.session_key}")

if interview.session_key:
    session = InterviewSession.objects.get(session_key=interview.session_key)
    print(f"Session exists: {session.id}")
    print(f"Candidate email: {session.candidate_email}")
```

### 2. **Check Email Configuration**

```python
# In Django shell
from django.conf import settings

print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_HOST_PASSWORD: {'SET' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
```

### 3. **Test Email Sending**

```bash
python test_email_credentials.py
```

### 4. **Check Server Console**

When scheduling interview, watch for:
- InterviewSession creation messages
- Email sending attempts
- Error messages

---

## 🐛 Common Issues

### Issue 1: "EMAIL_BACKEND is 'console'"
**Symptom**: Emails print to console but don't send
**Fix**: Set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` in `.env`

### Issue 2: "EMAIL_HOST is not set"
**Symptom**: Email configuration incomplete
**Fix**: Set `EMAIL_HOST=smtp.gmail.com` in `.env`

### Issue 3: "Email credentials incomplete"
**Symptom**: Missing EMAIL_HOST_USER or EMAIL_HOST_PASSWORD
**Fix**: Set both in `.env` file

### Issue 4: "Authentication failed" (535 error)
**Symptom**: Wrong password type for Gmail
**Fix**: Use Google App Password, not regular password

### Issue 5: InterviewSession not created
**Symptom**: No session_key in Interview
**Fix**: Check that `book_slot` or `book_interview` endpoint is called successfully

### Issue 6: Interview URL not generated
**Symptom**: Email sent but no link in email
**Fix**: Ensure InterviewSession is created with session_key

---

## 📧 Email Content

The email sent includes:
- ✅ Candidate name (from Candidate.full_name)
- ✅ Job title and company (from Job)
- ✅ Scheduled date and time (IST format)
- ✅ Interview link: `http://127.0.0.1:8000/?session_key={session_key}`
- ✅ Instructions and requirements

---

## ✅ Verification Checklist

When scheduling an interview:

1. [ ] Check server console for InterviewSession creation message
2. [ ] Check server console for email sending message
3. [ ] Verify email configuration in `.env` file
4. [ ] Check candidate's email inbox (and spam folder)
5. [ ] Verify interview link works when opened
6. [ ] Check Django logs for any error messages

---

## 🔄 Flow Diagram

```
Frontend: Schedule Interview
    ↓
POST /api/interviews/slots/{id}/book_slot/
    ↓
Backend: book_slot endpoint
    ↓
1. Creates InterviewSchedule
2. Updates Interview.started_at
3. ✅ Auto-creates InterviewSession
   - Fetches: Candidate, Job, Resume
   - Stores: coding_language
   - Generates: session_key
    ↓
4. ✅ Sends Email
   - Uses: send_interview_session_email
   - Link: http://127.0.0.1:8000/?session_key={key}
   - To: Candidate.email
    ↓
✅ Email Received by Candidate
```

---

## 📝 Next Steps

1. **Verify `.env` file has correct email settings**
2. **Check server console when scheduling interview**
3. **Look for success/error messages**
4. **Check candidate email inbox**










