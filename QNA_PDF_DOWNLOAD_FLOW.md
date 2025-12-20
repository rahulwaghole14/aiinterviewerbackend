# Q&A Script + AI Evaluation PDF Download Flow

## Overview
This document explains how the "Download Q&A Script + AI Evaluation PDF" button fetches and serves the PDF from Google Cloud Storage.

---

## 🔄 Complete Flow Diagram

```
Frontend (CandidateDetails.jsx)
    ↓
    User clicks "Download Q&A Script + AI Evaluation PDF" button
    ↓
    Browser navigates to: /ai/transcript_pdf?session_key=xxx
    ↓
Backend (interview_app/views.py - download_comprehensive_pdf)
    ↓
    1. Validates session_key/session_id
    2. Calls comprehensive_pdf.py to generate PDF
    ↓
comprehensive_pdf.py (generate_comprehensive_pdf)
    ↓
    1. Fetches InterviewSession from database
    2. Retrieves Q&A data from InterviewQuestion model
    3. Retrieves coding submissions from CodeSubmission model
    4. Retrieves AI evaluation from Evaluation model
    5. Generates PDF using fpdf2 library
    ↓
Backend (views.py - download_comprehensive_pdf)
    ↓
    1. Receives PDF bytes from comprehensive_pdf.py
    2. Uploads PDF to Google Cloud Storage (GCS)
    3. Stores GCS URL in Evaluation.details['qna_pdf_gcs_url']
    4. Serves PDF directly to user (HttpResponse)
    ↓
Google Cloud Storage
    ↓
    PDF stored at: evaluation_pdfs/qna_evaluation_{session_key}_{timestamp}.pdf
    ↓
Frontend
    ↓
    PDF downloads to user's computer
```

---

## 📋 Step-by-Step Function Details

### 1. **Frontend Button (CandidateDetails.jsx)**

**Location:** `frontend/src/components/CandidateDetails.jsx` (Line ~1750)

```javascript
<a 
  href={`${baseURL}/ai/transcript_pdf?${interview.session_key ? `session_key=${interview.session_key}` : `session_id=${interview.id}`}`}
  target="_blank"
  rel="noopener noreferrer"
  className="proctoring-download-link"
>
  <span>Download Q&A Script + AI Evaluation PDF</span>
</a>
```

**What it does:**
- Creates a link to `/ai/transcript_pdf` endpoint
- Passes `session_key` or `session_id` as query parameter
- Opens in new tab (`target="_blank"`)

---

### 2. **Backend Endpoint (views.py - download_comprehensive_pdf)**

**Location:** `interview_app/views.py` (Line ~5130)

**URL Pattern:** `/ai/transcript_pdf`

**Function Flow:**

```python
@csrf_exempt
def download_comprehensive_pdf(request):
    """
    Generate and serve comprehensive Q&A + AI Evaluation PDF
    """
    session_key = request.GET.get('session_key')
    session_id = request.GET.get('session_id')
    
    # Step 1: Validate session exists
    session = InterviewSession.objects.get(session_key=session_key)
    
    # Step 2: Generate PDF bytes
    from .comprehensive_pdf import ai_comprehensive_pdf_django
    pdf_bytes = ai_comprehensive_pdf_django(session_key)
    
    # Step 3: Upload to Google Cloud Storage (if configured)
    if pdf_bytes:
        gcs_file_path = f"evaluation_pdfs/qna_evaluation_{session_key}_{timestamp}.pdf"
        gcs_url = upload_pdf_to_gcs(pdf_bytes, gcs_file_path)
        
        # Step 4: Store GCS URL in Evaluation model
        if gcs_url:
            evaluation = Evaluation.objects.filter(interview=interview).first()
            if evaluation:
                evaluation.details['qna_pdf_gcs_url'] = gcs_url
                evaluation.save(update_fields=['details'])
    
    # Step 5: Serve PDF directly to user
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="interview_report_{session_key}.pdf"'
    return response
```

**Key Points:**
- ✅ Generates PDF on-demand (not pre-generated)
- ✅ Uploads to GCS **after** generation
- ✅ Stores GCS URL in `Evaluation.details['qna_pdf_gcs_url']` for future reference
- ✅ Serves PDF directly to user (doesn't redirect to GCS URL)
- ✅ Works even if GCS upload fails (serves PDF directly)

---

### 3. **PDF Generation (comprehensive_pdf.py)**

**Location:** `interview_app/comprehensive_pdf.py`

**Function:** `ai_comprehensive_pdf_django(session_key: str) -> bytes`

**What it does:**

1. **Fetches Session Data:**
   ```python
   session = InterviewSession.objects.get(session_key=session_key)
   ```

2. **Retrieves Q&A Data from Database:**
   ```python
   questions_from_db = InterviewQuestion.objects.filter(
       session=session
   ).order_by('conversation_sequence', 'order', 'id')
   ```
   - Gets all questions and answers from `InterviewQuestion` model
   - Orders by `conversation_sequence` to maintain correct order
   - Pairs AI questions with interviewee answers

3. **Retrieves Coding Submissions:**
   ```python
   coding_submissions = CodeSubmission.objects.filter(session=session).order_by('created_at')
   ```
   - Gets all coding challenge submissions
   - Includes test results (passed/failed)

4. **Retrieves AI Evaluation:**
   ```python
   evaluation = Evaluation.objects.filter(interview=interview).first()
   ai_analysis = evaluation.details.get('ai_analysis', {})
   ```
   - Gets overall scores, strengths, weaknesses
   - Gets technical, behavioral, coding analysis

5. **Generates PDF using fpdf2:**
   ```python
   pdf = FPDF()
   pdf.add_page()
   # Add content:
   # - Candidate Information
   # - Technical Q&A Transcript
   # - Coding Challenge Results
   # - AI Evaluation Summary
   pdf_bytes = pdf.output(dest='S')  # Returns bytes
   ```

**PDF Sections:**
- 📄 **Header:** "AI Interview Report"
- 👤 **Candidate Information:** Name, Email, Date, Session ID
- 💬 **Technical Q&A Transcript:** All questions and answers in order
- 💻 **Coding Challenge Results:** Problem, submitted code, test results
- 🤖 **AI Evaluation:** Scores, strengths, weaknesses, detailed feedback

---

### 4. **Google Cloud Storage Upload (gcs_storage.py)**

**Location:** `interview_app/gcs_storage.py`

**Function:** `upload_pdf_to_gcs(pdf_bytes: bytes, file_path: str) -> Optional[str]`

**What it does:**

```python
def upload_pdf_to_gcs(pdf_bytes: bytes, file_path: str) -> Optional[str]:
    """
    Upload PDF bytes to Google Cloud Storage
    
    Args:
        pdf_bytes: PDF file content as bytes
        file_path: Path within bucket (e.g., 'evaluation_pdfs/filename.pdf')
    
    Returns:
        GCS public URL if successful, None otherwise
    """
    # Step 1: Get GCS client
    client = get_gcs_client()  # Uses GOOGLE_APPLICATION_CREDENTIALS or default credentials
    
    # Step 2: Get bucket name from settings
    bucket_name = get_gcs_bucket_name()  # From GCS_BUCKET_NAME env var
    
    # Step 3: Create blob (file) in bucket
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    
    # Step 4: Upload PDF bytes
    blob.upload_from_string(pdf_bytes, content_type='application/pdf')
    
    # Step 5: Make blob publicly readable
    blob.make_public()
    
    # Step 6: Get public URL
    public_url = blob.public_url
    # Returns: https://storage.googleapis.com/{bucket_name}/{file_path}
    
    return public_url
```

**GCS File Path Format:**
```
evaluation_pdfs/qna_evaluation_{session_key}_{timestamp}.pdf
```

**Example:**
```
evaluation_pdfs/qna_evaluation_2c9e0669785f43538a2e1c5ec5dbb052_20251219_175116.pdf
```

**GCS Public URL Format:**
```
https://storage.googleapis.com/{bucket_name}/evaluation_pdfs/qna_evaluation_{session_key}_{timestamp}.pdf
```

**Example:**
```
https://storage.googleapis.com/ai-interview-pdfs-eastern-team-480811-e6/evaluation_pdfs/qna_evaluation_2c9e0669785f43538a2e1c5ec5dbb052_20251219_175116.pdf
```

---

### 5. **GCS URL Storage (Evaluation Model)**

**Location:** `evaluation/models.py`

**Storage:**
```python
evaluation = Evaluation.objects.filter(interview=interview).first()
if evaluation:
    if not evaluation.details:
        evaluation.details = {}
    evaluation.details['qna_pdf_gcs_url'] = gcs_url
    evaluation.save(update_fields=['details'])
```

**Where it's stored:**
- `Evaluation.details` is a JSONField
- GCS URL is stored as: `evaluation.details['qna_pdf_gcs_url']`
- This allows frontend to retrieve the URL later if needed

---

## 🔍 How PDF is Fetched from GCS

### Current Implementation (On-Demand Generation)

**Current Flow:**
1. User clicks button → Backend generates PDF → Uploads to GCS → Serves PDF directly

**Why PDF is NOT fetched from GCS:**
- PDF is generated **on-demand** each time the button is clicked
- This ensures the PDF always has the latest data
- GCS upload is **optional** (for backup/reference)
- PDF is served directly from backend to user

### Alternative: Fetch from GCS (If Pre-Generated)

If you want to fetch from GCS instead of generating on-demand:

```python
# In views.py - download_comprehensive_pdf
def download_comprehensive_pdf(request):
    session_key = request.GET.get('session_key')
    
    # Check if PDF exists in GCS
    evaluation = Evaluation.objects.filter(interview__session_key=session_key).first()
    if evaluation and evaluation.details.get('qna_pdf_gcs_url'):
        gcs_url = evaluation.details['qna_pdf_gcs_url']
        
        # Option 1: Redirect to GCS URL
        return HttpResponseRedirect(gcs_url)
        
        # Option 2: Download from GCS and serve
        from .gcs_storage import download_pdf_from_gcs
        file_path = gcs_url.split('/')[-1]  # Extract file path
        pdf_bytes = download_pdf_from_gcs(f"evaluation_pdfs/{file_path}")
        if pdf_bytes:
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="interview_report_{session_key}.pdf"'
            return response
    
    # Fallback: Generate PDF on-demand
    pdf_bytes = ai_comprehensive_pdf_django(session_key)
    # ... rest of code
```

---

## 📊 Data Flow Summary

| Step | Component | Action | Output |
|------|-----------|--------|--------|
| 1 | Frontend | User clicks button | HTTP GET to `/ai/transcript_pdf?session_key=xxx` |
| 2 | Backend (views.py) | Validates session | `InterviewSession` object |
| 3 | Backend (views.py) | Calls PDF generator | Calls `ai_comprehensive_pdf_django(session_key)` |
| 4 | comprehensive_pdf.py | Fetches Q&A data | `InterviewQuestion` objects |
| 5 | comprehensive_pdf.py | Fetches coding data | `CodeSubmission` objects |
| 6 | comprehensive_pdf.py | Fetches AI evaluation | `Evaluation.details['ai_analysis']` |
| 7 | comprehensive_pdf.py | Generates PDF | PDF bytes (using fpdf2) |
| 8 | Backend (views.py) | Uploads to GCS | `upload_pdf_to_gcs(pdf_bytes, file_path)` |
| 9 | gcs_storage.py | Uploads to bucket | GCS public URL |
| 10 | Backend (views.py) | Stores GCS URL | `evaluation.details['qna_pdf_gcs_url'] = gcs_url` |
| 11 | Backend (views.py) | Serves PDF | `HttpResponse(pdf_bytes, content_type='application/pdf')` |
| 12 | Browser | Downloads PDF | PDF file saved to user's computer |

---

## 🔧 Configuration Requirements

### 1. **Environment Variables**

```bash
# Google Cloud Storage Configuration
GCS_BUCKET_NAME=ai-interview-pdfs-eastern-team-480811-e6
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
# OR use default credentials (if running on GCP)
```

### 2. **GCS Bucket Setup**

```bash
# Create bucket (if not exists)
gsutil mb -p eastern-team-480811-e6 -l asia-southeast1 gs://ai-interview-pdfs-eastern-team-480811-e6

# Make bucket publicly readable (for public URLs)
gsutil iam ch allUsers:objectViewer gs://ai-interview-pdfs-eastern-team-480811-e6
```

### 3. **Service Account Permissions**

The service account needs:
- `roles/storage.objectAdmin` - To upload files
- `roles/storage.objectViewer` - To read files (if fetching from GCS)

---

## 🐛 Troubleshooting

### Issue: PDF not generating
**Check:**
- `fpdf2` is installed: `pip install fpdf2`
- Session exists in database
- `InterviewQuestion` records exist for the session

### Issue: GCS upload failing
**Check:**
- `GCS_BUCKET_NAME` environment variable is set
- Service account has `storage.objectAdmin` permission
- Bucket exists and is accessible
- Network connectivity to GCS

### Issue: PDF not downloading
**Check:**
- Backend endpoint is accessible: `/ai/transcript_pdf`
- Session key is valid
- PDF bytes are not empty
- Browser allows downloads

---

## 📝 Notes

1. **PDF is generated on-demand** - Not pre-generated and stored
2. **GCS upload is optional** - PDF works even if GCS upload fails
3. **GCS URL is stored for reference** - Can be used later to fetch from GCS
4. **PDF is served directly** - Not redirected to GCS URL (unlike proctoring PDF)
5. **Always has latest data** - Since it's generated on-demand, it always includes the latest Q&A and evaluation

---

## 🔄 Future Enhancements

1. **Cache PDF in GCS** - Generate once, serve from GCS on subsequent requests
2. **Pre-generate PDFs** - Generate PDFs after interview completion
3. **Use signed URLs** - For private access instead of public URLs
4. **Add PDF versioning** - Store multiple versions if evaluation is updated

