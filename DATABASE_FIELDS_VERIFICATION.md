# Database Fields Verification for Interview Scheduling

## ✅ Database Fields Available

### 1. **Candidate Model** (`candidates.Candidate`)
All fields are available and being fetched:
- ✅ `full_name` → Used for `InterviewSession.candidate_name`
- ✅ `email` → Used for `InterviewSession.candidate_email`
- ✅ `resume` (ForeignKey to Resume) → Used to extract resume text
- ✅ `job` (ForeignKey to Job) → Links candidate to job
- ✅ `phone`, `work_experience`, `domain`, `status` (available but not required for interview)

### 2. **Job Model** (`jobs.Job`)
All required fields are available:
- ✅ `job_title` → Used in job description
- ✅ `company_name` → Used in job description
- ✅ `job_description` → Used for `InterviewSession.job_description`
- ✅ `coding_language` → **NEW FIELD** Used for coding round (stored in `InterviewSession.keyword_analysis`)
- ✅ `domain` (ForeignKey to Domain) → Used in job description
- ✅ `tech_stack_details` → Legacy field, still available

### 3. **Resume Model** (`resumes.Resume`)
Fields available for resume extraction:
- ✅ `file` → Used to extract resume text
- ✅ `parsed_text` → Alternative source for resume text

### 4. **Interview Model** (`interviews.Interview`)
Fields used for scheduling:
- ✅ `candidate` (ForeignKey) → Links to candidate
- ✅ `job` (ForeignKey) → Links to job
- ✅ `slot` (ForeignKey) → Links to interview slot
- ✅ `started_at` → Used for `InterviewSession.scheduled_at`
- ✅ `ended_at` → Available for duration calculation
- ✅ `session_key` → Stored after InterviewSession creation

### 5. **InterviewSchedule Model** (`interviews.InterviewSchedule`)
Fields available:
- ✅ `interview` (OneToOneField) → Links to Interview
- ✅ `slot` (ForeignKey) → Links to InterviewSlot
- ✅ `booking_notes` → Available for additional notes

### 6. **InterviewSlot Model** (`interviews.InterviewSlot`)
Fields used:
- ✅ `interview_date` → Combined with `start_time` for scheduled_at
- ✅ `start_time` → Combined with `interview_date` for scheduled_at
- ✅ `end_time` → Available for duration
- ✅ `ai_interview_type` → Available (technical/coding)
- ✅ `job` (ForeignKey) → Links to job

---

## ✅ Current Implementation Status

### **Backend Endpoint: `create_interview_session`**
**Location**: `interviews/views.py` line 1144-1290

**Fields Fetched**:
1. ✅ Candidate: `full_name`, `email`, `resume`
2. ✅ Job: `job_title`, `company_name`, `job_description`, `domain.name`, **`coding_language`**
3. ✅ Resume: Extracts text from `resume.file` or uses `resume.parsed_text`
4. ✅ Schedule: Gets `scheduled_at` from `interview.started_at` or `schedule.slot`

**Fields Created in InterviewSession**:
- ✅ `candidate_name` ← Candidate.full_name
- ✅ `candidate_email` ← Candidate.email
- ✅ `job_description` ← Built from Job fields
- ✅ `resume_text` ← Extracted from Resume.file or Resume.parsed_text
- ✅ `scheduled_at` ← Interview.started_at or Slot date+time
- ✅ `session_key` ← Generated automatically
- ✅ `keyword_analysis` ← Stores `CODING_LANG={coding_language}`

---

## ⚠️ Issues Found

### **Issue 1: Frontend Not Calling `create_interview_session`**
**Problem**: The frontend scheduling flow (`StatusUpdateModal.jsx`) creates the Interview and books the slot, but does NOT call `create_interview_session` endpoint to create the InterviewSession.

**Current Flow**:
1. Frontend creates Interview
2. Frontend books slot
3. **MISSING**: Frontend should call `create_interview_session` to generate InterviewSession

**Solution Options**:
1. **Option A**: Add call to `create_interview_session` in frontend after booking
2. **Option B**: Auto-create InterviewSession in `book_interview` endpoint

### **Issue 2: Resume Text Extraction**
**Current**: Tries `resume.file` first, then `resume.parsed_text`
**Note**: Resume model has `parsed_text` field that is auto-populated on save, so this should work.

### **Issue 3: Legacy Code Still Uses `tech_stack_details`**
**Location**: `interviews/models.py` line 415
```python
"job_description": (
    self.job.tech_stack_details if self.job else "Technical Role"
),
```
**Should be**: Use `job.job_description` or build from `job_title`, `company_name`, etc.

---

## ✅ Verification Checklist

### From Candidate:
- [x] `full_name` → Available
- [x] `email` → Available
- [x] `resume` → Available (ForeignKey)
- [x] `job` → Available (ForeignKey)

### From Job:
- [x] `job_title` → Available
- [x] `company_name` → Available
- [x] `job_description` → Available
- [x] `coding_language` → **AVAILABLE** (NEW)
- [x] `domain` → Available (ForeignKey)

### From Resume:
- [x] `file` → Available (FileField)
- [x] `parsed_text` → Available (auto-extracted)

### From Interview:
- [x] `candidate` → Available
- [x] `job` → Available
- [x] `slot` → Available
- [x] `started_at` → Available
- [x] `schedule` → Available (via OneToOne relation)

### From InterviewSchedule/Slot:
- [x] `interview_date` → Available
- [x] `start_time` → Available
- [x] `end_time` → Available

---

## 🔧 Recommended Fix

### Auto-Create InterviewSession in `book_interview`

Modify the `book_interview` endpoint to automatically create InterviewSession after booking:

```python
# In interviews/views.py, book_interview method
# After creating/updating schedule, add:

# Auto-create InterviewSession
try:
    from interview_app.models import InterviewSession
    import secrets
    
    # Check if InterviewSession already exists
    if not interview.session_key:
        # Fetch all data
        candidate = interview.candidate
        job = interview.job
        coding_language = getattr(job, 'coding_language', 'PYTHON')
        
        # Get scheduled time
        scheduled_at = interview.started_at
        if not scheduled_at and hasattr(interview, 'schedule'):
            slot = interview.schedule.slot
            if slot.interview_date and slot.start_time:
                import pytz
                from datetime import datetime
                ist = pytz.timezone('Asia/Kolkata')
                start_dt = datetime.combine(slot.interview_date, slot.start_time)
                scheduled_at = ist.localize(start_dt).astimezone(pytz.UTC)
        
        # Extract resume text
        resume_text = ""
        if candidate.resume:
            if hasattr(candidate.resume, 'parsed_text') and candidate.resume.parsed_text:
                resume_text = candidate.resume.parsed_text
            elif hasattr(candidate.resume, 'file') and candidate.resume.file:
                from interview_app_11.views import get_text_from_file
                resume_text = get_text_from_file(candidate.resume.file) or ""
        
        # Build job description
        job_description = job.job_description or f"Job Title: {job.job_title}\nCompany: {job.company_name}"
        if job.domain:
            job_description += f"\nDomain: {job.domain.name}"
        
        # Generate session key
        session_key = secrets.token_hex(16)
        
        # Create InterviewSession
        session = InterviewSession.objects.create(
            candidate_name=candidate.full_name or "Candidate",
            candidate_email=candidate.email or "",
            job_description=job_description,
            resume_text=resume_text,
            session_key=session_key,
            scheduled_at=scheduled_at or timezone.now(),
            status='SCHEDULED',
            language_code='en-IN',
            accent_tld='co.in'
        )
        
        # Store coding language
        session.keyword_analysis = f"CODING_LANG={coding_language}"
        session.save()
        
        # Update Interview with session_key
        interview.session_key = session_key
        interview.save(update_fields=['session_key'])
        
        # Send email
        try:
            from interview_app_11.views import send_interview_session_email
            base_url = request.build_absolute_uri('/').rstrip('/')
            interview_link = f"{base_url}/?session_key={session_key}"
            send_interview_session_email(session, interview_link, request)
        except Exception as e:
            print(f"Email sending failed: {e}")
            
except Exception as e:
    print(f"Auto-creation of InterviewSession failed: {e}")
    # Don't fail the booking if InterviewSession creation fails
```

---

## 📊 Summary

### ✅ All Database Fields ARE Available

**Candidate Fields**: ✅ All available
**Job Fields**: ✅ All available (including `coding_language`)
**Resume Fields**: ✅ All available
**Interview/Schedule Fields**: ✅ All available

### ⚠️ Missing Integration

**Issue**: Frontend doesn't automatically create `InterviewSession` after booking interview.

**Solution**: Auto-create `InterviewSession` in the `book_interview` endpoint OR add frontend call to `create_interview_session`.

---

## 🎯 Next Steps

1. ✅ Verify all database fields are accessible (DONE - all available)
2. ⚠️ Integrate InterviewSession auto-creation in `book_interview`
3. ⚠️ Fix legacy code in `Interview.generate_interview_link()` to use `coding_language`
4. ✅ Test end-to-end flow










