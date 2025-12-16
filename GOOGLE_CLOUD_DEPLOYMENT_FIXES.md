# Google Cloud Deployment - Critical Fixes & Solutions

## Issues Fixed

### 1. ✅ Settings Import Error (FIXED)
**Error:** `⚠️ Error logging no_person warning: cannot access local variable 'settings' where it is not associated with a value`

**Fix Applied:**
- Added `from django.conf import settings` import in `detect_yolo_browser_frame` function
- This ensures proctoring warning snapshots are saved correctly

**File:** `interview_app/views.py` (line ~3168)

---

### 2. ✅ Introduction Question Issue (FIXED)
**Problem:** AI was saying "Okay, I understand the instructions. Let's begin." instead of asking for introduction

**Fix Applied:**
- Updated introduction question prompt in `complete_ai_bot.py`
- Added explicit instructions to:
  - MUST ask a question (not make statements)
  - MUST explicitly ask for introduction
  - DO NOT say "Let's begin" or similar phrases
  - Provided correct and incorrect examples

**File:** `interview_app/complete_ai_bot.py` (lines ~918-943)

---

### 3. ⚠️ Question Numbering Issues
**Problem:** Questions repeating or missing sequence numbers

**Current Implementation:**
- Question numbering is handled in `complete_ai_bot.py` and `views.py`
- Only `MAIN` questions increment the counter (not follow-ups)
- Session restoration counts only `MAIN` questions

**To Verify:**
1. Check `session.current_question_number` is only incremented for MAIN questions
2. Verify session restoration logic counts correctly
3. Check that follow-up questions don't increment the counter

**Files to Check:**
- `interview_app/complete_ai_bot.py` - `upload_answer` function
- `interview_app/views.py` - `ai_start` and `ai_upload_answer` functions

---

### 4. ⚠️ PDF Download Issues

#### A. Q&A Script + AI Evaluation PDF
**Endpoint:** `/ai/transcript_pdf?session_key=...` or `?session_id=...`

**Status:** ✅ Endpoint exists and should work

**To Verify:**
1. Check that `fpdf2` and `fpdf` are in `requirements.txt` (✅ Already added)
2. Verify PDF generation function `ai_comprehensive_pdf_django` works
3. Test the endpoint: `GET /ai/transcript_pdf?session_key=<key>`

**Files:**
- `interview_app/views.py` - `ai_transcript_pdf` function (line ~5016)
- `interview_app/comprehensive_pdf.py` - `generate_comprehensive_pdf` function

#### B. Proctoring Warnings PDF
**Endpoint:** Uses `proctoring_pdf_url` from evaluation details

**Status:** ✅ PDF generation exists, but URL must be accessible

**To Verify:**
1. Check that `evaluation.details.proctoring_pdf_url` is set correctly
2. Verify PDF file exists at the path
3. Ensure MEDIA_URL is configured correctly in Cloud Run

**Files:**
- `evaluation/services.py` - `create_evaluation_from_session` function
- `evaluation/proctoring_pdf.py` - `generate_proctoring_pdf` function

**Frontend Usage:**
```javascript
// In CandidateDetails.jsx (line ~1611)
href={`${baseURL}${aiResult.proctoring_pdf_url}`}
```

---

### 5. ⚠️ Proctoring Warning Snapshots Not Saved

**Current Implementation:**
- Snapshots are saved in `detect_yolo_browser_frame` function
- Saved to: `media/proctoring_snaps/{session_key}_{warning_type}_{timestamp}.jpg`
- Also saved to database `WarningLog.snapshot_image` field

**To Verify:**
1. Check that `settings.MEDIA_ROOT` is accessible in Cloud Run
2. Verify directory permissions: `/app/media/proctoring_snaps/`
3. Check that `WarningLog` entries are created with snapshots

**Files:**
- `interview_app/views.py` - `detect_yolo_browser_frame` function (lines ~3379-3402)

---

## Google Cloud Run Deployment Checklist

### 1. Environment Variables
Ensure these are set in Cloud Run:

```bash
# Django Settings
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-cloud-run-url.run.app

# Database (Cloud SQL)
DATABASE_URL=postgresql://user:password@/dbname?host=/cloudsql/project:region:instance

# Media Files
MEDIA_ROOT=/app/media
MEDIA_URL=/media/

# API Keys
GEMINI_API_KEY=your-gemini-key
DEEPGRAM_API_KEY=your-deepgram-key
GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/my-service-key.json

# Cloud Run Specific
PORT=8080
```

### 2. Cloud SQL Connection
```bash
# Ensure Cloud SQL proxy is configured or use Unix socket
# In Cloud Run, use: /cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```

### 3. Media Files Storage
**Option A: Use Cloud Storage (Recommended)**
- Store media files in GCS bucket
- Update `MEDIA_ROOT` to use GCS
- Configure `django-storages` with GCS backend

**Option B: Use Persistent Volume (Limited)**
- Cloud Run has ephemeral storage
- Files are lost on container restart
- Use Cloud Storage for production

### 4. Required Build Dependencies
Ensure `Dockerfile` includes:
- Python 3.11
- PostgreSQL client libraries
- OpenCV dependencies
- All compilers for coding languages
- YOLO model files (`yolov8m.pt`, `yolov8m.onnx`)

### 5. PDF Generation Dependencies
✅ Already in `requirements.txt`:
- `fpdf2==2.7.9`
- `fpdf==2.7.6`
- `weasyprint==62.3`

### 6. Secret Manager Access
```bash
# Grant Cloud Run service account access to secrets
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 7. Cloud Run Service Configuration
```bash
# Deploy with proper settings
gcloud run deploy SERVICE_NAME \
  --source . \
  --region REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="DJANGO_SECRET_KEY=...,DATABASE_URL=..." \
  --set-secrets="GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/my-service-key.json:my-service-key:latest" \
  --add-cloudsql-instances=PROJECT_ID:REGION:INSTANCE_NAME \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --max-instances=10
```

---

## Verification Steps After Deployment

### 1. Test Introduction Question
1. Start a new interview
2. Verify first question asks for introduction (not "Let's begin")
3. Check that candidate's first name is used

### 2. Test Question Numbering
1. Complete an interview
2. Verify questions are numbered sequentially: 1, 2, 3, 4...
3. Check that follow-up questions don't increment the counter
4. Verify no questions are repeated

### 3. Test PDF Downloads

#### A. Q&A Script + AI Evaluation PDF
```bash
# Test endpoint
curl "https://your-service.run.app/ai/transcript_pdf?session_key=YOUR_SESSION_KEY" \
  --output interview_report.pdf
```

#### B. Proctoring PDF
1. Check evaluation details for `proctoring_pdf_url`
2. Verify PDF file exists at the path
3. Test download from frontend

### 4. Test Proctoring Snapshots
1. Trigger a warning during interview (e.g., phone detection)
2. Check Cloud Run logs for: `✅ Logged {warning_type} warning with snapshot`
3. Verify file exists: `/app/media/proctoring_snaps/{session_key}_{warning_type}_{timestamp}.jpg`
4. Check database: `WarningLog` entries with `snapshot_image` field populated

### 5. Check Media Files Access
```bash
# In Cloud Run container
ls -la /app/media/proctoring_snaps/
ls -la /app/media/proctoring_pdfs/
```

---

## Troubleshooting

### PDF Not Downloading
1. Check `fpdf2` is installed: `pip list | grep fpdf`
2. Verify PDF generation doesn't return empty bytes
3. Check Cloud Run logs for PDF generation errors
4. Verify MEDIA_ROOT is writable

### Snapshots Not Saved
1. Check `settings.MEDIA_ROOT` is correct
2. Verify directory exists and is writable
3. Check Cloud Run logs for error messages
4. Verify `WarningLog.objects.create()` is called

### Question Numbering Issues
1. Check `session.current_question_number` in logs
2. Verify only MAIN questions increment counter
3. Check session restoration logic
4. Review `complete_ai_bot.py` - `upload_answer` function

### Introduction Question Issues
1. Check LLM prompt in `complete_ai_bot.py`
2. Verify examples are clear
3. Check Gemini API response
4. Review `_shape_question` function

---

## Next Steps

1. ✅ Deploy updated code to Cloud Run
2. ✅ Test introduction question
3. ✅ Verify question numbering
4. ✅ Test PDF downloads
5. ✅ Verify proctoring snapshots are saved
6. ✅ Monitor Cloud Run logs for errors

---

## Support

If issues persist:
1. Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision"`
2. Verify all environment variables are set
3. Check database connectivity
4. Verify file system permissions
5. Review error messages in application logs

