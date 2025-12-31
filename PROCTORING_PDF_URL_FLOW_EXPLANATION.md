# Proctoring PDF URL: Complete Flow Explanation

## 📋 Overview
This document explains the complete functionality of how proctoring PDF URLs are generated, stored in the database, and accessed from the frontend.

---

## 🔄 Complete Flow

### **STEP 1: PDF Generation & URL Creation**

**Location:** `evaluation/proctoring_pdf.py` - `generate_proctoring_pdf()`

**Process:**
1. After interview completion, the system generates a proctoring PDF containing all warnings and snapshots
2. PDF is created using `fpdf2` library with warnings grouped by type
3. PDF bytes are generated in memory
4. **Two storage methods are attempted:**

   **A. Google Cloud Storage (Primary):**
   - Uploads PDF bytes to GCS bucket
   - File path format: `proctoring_pdfs/proctoring_report_{interview_id}_{timestamp}.pdf`
   - Sets blob to public read access
   - Returns **clean GCS public URL**: `https://storage.googleapis.com/{bucket_name}/proctoring_pdfs/proctoring_report_{id}_{timestamp}.pdf`

   **B. Local Storage (Fallback):**
   - If GCS upload fails, saves PDF to `media/proctoring_pdfs/`
   - Returns relative path: `proctoring_pdfs/proctoring_report_{id}_{timestamp}.pdf`

**Code Reference:**
```python
# evaluation/proctoring_pdf.py:271-310
# Upload to Google Cloud Storage if configured
gcs_url = upload_pdf_to_gcs(pdf_bytes, gcs_file_path)

# Return GCS URL if available, otherwise return relative path
if gcs_url:
    return {'gcs_url': gcs_url, 'local_path': relative_path}
return relative_path
```

**GCS Upload Function:**
```python
# interview_app/gcs_storage.py:36-84
def upload_pdf_to_gcs(pdf_bytes, file_path):
    blob.upload_from_string(pdf_bytes, content_type='application/pdf')
    blob.make_public()  # Make publicly accessible
    return blob.public_url  # Returns: https://storage.googleapis.com/bucket/path/file.pdf
```

---

### **STEP 2: URL Cleaning & Validation**

**Location:** `evaluation/services.py` - `create_evaluation_from_session()` (lines 418-536)

**Process:**
1. Receives GCS URL from PDF generation
2. **CRITICAL: Cleans URL to remove malformed prefixes**
   - Removes patterns like: `run.apphttps//`, `https//`, etc.
   - Extracts only the GCS part: `storage.googleapis.com/...`
   - Validates URL format: must start with `https://storage.googleapis.com/`
3. If URL is invalid, stores `None` and uses local path instead

**URL Cleaning Logic:**
```python
# evaluation/services.py:418-476
if 'storage.googleapis.com' in gcs_url:
    # Extract everything from storage.googleapis.com onwards
    gcs_index = gcs_url.find('storage.googleapis.com')
    clean_url = gcs_url[gcs_index:]
    
    # Remove malformed prefixes
    clean_url = re.sub(r'^https?\/\/+', '', clean_url)
    clean_url = re.sub(r'^https?:\/\/+', '', clean_url)
    
    # Construct clean URL
    if clean_url.startswith('storage.googleapis.com'):
        clean_gcs_url = f"https://{clean_url}"
        
        # Final validation
        if clean_gcs_url.startswith('https://storage.googleapis.com/'):
            # URL is valid - store it
```

---

### **STEP 3: Database Storage**

**Location:** `evaluation/services.py` - `create_evaluation_from_session()` (lines 518-536)

**Process:**
The cleaned GCS URL is stored in **TWO places** for redundancy:

**A. ProctoringPDF Table (PRIMARY SOURCE):**
```python
# evaluation/services.py:521-527
proctoring_pdf, created = ProctoringPDF.objects.update_or_create(
    interview=interview,
    defaults={
        'gcs_url': clean_gcs_url,  # Clean, validated GCS URL
        'local_path': local_path,   # Local file path (backup)
    }
)
```

**Database Schema:**
```sql
-- Table: evaluation_proctoringpdf
CREATE TABLE evaluation_proctoringpdf (
    id INTEGER PRIMARY KEY,
    interview_id INTEGER REFERENCES interviews_interview(id),
    gcs_url VARCHAR(500),      -- PRIMARY: Clean GCS URL
    local_path VARCHAR(500),   -- Backup: Local file path
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**B. Evaluation.details (JSONField - Secondary/Fallback):**
```python
# evaluation/services.py:511-512
details['proctoring_pdf_gcs_url'] = clean_gcs_url
details['proctoring_pdf_url'] = clean_gcs_url
details['proctoring_pdf'] = local_path
```

**Database Schema:**
```sql
-- Table: evaluation_evaluation
CREATE TABLE evaluation_evaluation (
    id INTEGER PRIMARY KEY,
    interview_id INTEGER REFERENCES interviews_interview(id),
    details JSONB,  -- Contains proctoring_pdf_url, proctoring_pdf_gcs_url, proctoring_pdf
    ...
);
```

**Why Two Storage Locations?**
- **ProctoringPDF table**: Dedicated table for easy querying and primary source
- **Evaluation.details**: Fallback if ProctoringPDF record doesn't exist

---

### **STEP 4: URL Retrieval (Backend API)**

**Location:** `interviews/serializers.py` - `get_proctoring_pdf()` (lines 753-819)

**Process:**
1. Frontend requests interview data via `/api/interviews/`
2. Serializer queries **ProctoringPDF table first** (PRIMARY SOURCE)
3. **Cleans URL again** (safety check) to remove any malformed prefixes
4. Validates URL format
5. Returns clean URL in API response

**Code:**
```python
# interviews/serializers.py:753-819
def get_proctoring_pdf(self, obj):
    proctoring_pdf = ProctoringPDF.objects.filter(interview=obj).first()
    if proctoring_pdf and proctoring_pdf.gcs_url:
        # Clean URL again (safety check)
        original_url = proctoring_pdf.gcs_url.strip()
        clean_url = clean_gcs_url(original_url)  # Remove malformed prefixes
        
        if clean_url.startswith('https://storage.googleapis.com/'):
            return {
                'gcs_url': clean_url,
                'local_path': proctoring_pdf.local_path,
                'created_at': proctoring_pdf.created_at.isoformat(),
                'updated_at': proctoring_pdf.updated_at.isoformat(),
            }
    return None
```

**API Response Format:**
```json
{
  "id": "interview-uuid",
  "proctoring_pdf": {
    "gcs_url": "https://storage.googleapis.com/bucket-name/proctoring_pdfs/proctoring_report_123_20240115_101530.pdf",
    "local_path": "proctoring_pdfs/proctoring_report_123_20240115_101530.pdf",
    "created_at": "2024-01-15T10:15:30Z",
    "updated_at": "2024-01-15T10:15:30Z"
  },
  "ai_result": {
    "proctoring_pdf_url": "https://storage.googleapis.com/bucket-name/proctoring_pdfs/proctoring_report_123_20240115_101530.pdf"
  }
}
```

---

### **STEP 5: Frontend Display & Access**

**Location:** `frontend/src/components/CandidateDetails.jsx` (lines 1559-1584)

**Process:**
1. Frontend receives URL in `aiResult.proctoring_pdf_url` or `interview.proctoring_pdf.gcs_url`
2. Displays download link button
3. When user clicks, opens URL directly in new tab

**Code:**
```javascript
// frontend/src/components/CandidateDetails.jsx:1562-1572
{aiResult.proctoring_pdf_url ? (
  <div className="proctoring-download-section">
    <a 
      href={aiResult.proctoring_pdf_url}
      target="_blank"
      rel="noopener noreferrer"
      className="proctoring-download-link"
    >
      <span className="download-icon">📄</span>
      <span>Download Proctoring Warnings Report</span>
    </a>
  </div>
) : (
  <div>No proctoring warnings report available</div>
)}
```

---

### **STEP 6: PDF Access (When URL is Opened)**

**Process:**
1. User clicks download link
2. Browser makes **direct HTTP GET request** to Google Cloud Storage URL
3. **NO backend processing** - URL is direct link to GCS
4. GCS serves PDF file directly to browser
5. Browser displays PDF in new tab or downloads it

**Important Notes:**
- ✅ **No Django backend processing** when URL is opened
- ✅ **Direct GCS access** - URL points directly to Google Cloud Storage
- ✅ **Public access** - PDF is publicly readable (if bucket permissions allow)
- ✅ **No authentication required** - GCS serves file directly

**URL Format:**
```
https://storage.googleapis.com/{BUCKET_NAME}/proctoring_pdfs/proctoring_report_{INTERVIEW_ID}_{TIMESTAMP}.pdf
```

**Example:**
```
https://storage.googleapis.com/ai-interview-pdfs-eastern-team-480811-e6/proctoring_pdfs/proctoring_report_0f4b3cc9-6142-4a2e-9cfd-fa9c7a9fedb2_20251223_080048.pdf
```

---

## 🔍 Key Points Summary

### **1. URL Generation:**
- Generated during evaluation creation (`create_evaluation_from_session`)
- PDF is created and uploaded to GCS
- Returns clean GCS public URL: `https://storage.googleapis.com/bucket/path/file.pdf`

### **2. Database Storage:**
- **PRIMARY:** `evaluation_proctoringpdf.gcs_url` (URLField)
- **SECONDARY:** `evaluation_evaluation.details['proctoring_pdf_url']` (JSONField)
- URL is cleaned and validated before storage

### **3. URL Retrieval:**
- Serializer queries `ProctoringPDF` table first
- Cleans URL again (safety check)
- Returns in API response as `proctoring_pdf.gcs_url` or `ai_result.proctoring_pdf_url`

### **4. Frontend Access:**
- URL is displayed as download link
- Clicking opens URL directly in new tab
- **No backend API call** when opening PDF

### **5. PDF Opening:**
- **NO backend processing** - direct GCS access
- Browser requests PDF directly from Google Cloud Storage
- GCS serves file with public read access
- PDF displays in browser or downloads

---

## 🛡️ Safety Measures

### **Triple URL Cleaning:**
1. **Storage time** (`evaluation/services.py`) - Cleans before storing
2. **Serialization time** (`interviews/serializers.py`) - Cleans before returning
3. **Frontend (optional)** - Can clean again if needed

### **URL Validation:**
- Must start with: `https://storage.googleapis.com/`
- Removes patterns: `run.apphttps//`, `https//`, etc.
- Returns `None` if URL is invalid

---

## 📊 Flow Diagram

```
Interview Completion
    ↓
generate_proctoring_pdf()
    ↓
Upload to GCS → Returns: https://storage.googleapis.com/bucket/path/file.pdf
    ↓
Clean URL (remove malformed prefixes)
    ↓
Store in Database:
  - ProctoringPDF.gcs_url (PRIMARY)
  - Evaluation.details['proctoring_pdf_url'] (FALLBACK)
    ↓
Frontend requests /api/interviews/
    ↓
Serializer queries ProctoringPDF table
    ↓
Clean URL again (safety check)
    ↓
Return in API response
    ↓
Frontend displays download link
    ↓
User clicks link
    ↓
Browser opens: https://storage.googleapis.com/bucket/path/file.pdf
    ↓
GCS serves PDF directly (NO backend processing)
    ↓
PDF displayed in browser
```

---

## 🛠️ Troubleshooting

### **Issue: PDF URL is `null` or missing**
**Possible Causes:**
1. Interview not completed yet
2. Evaluation not created
3. PDF generation failed
4. GCS upload failed
5. URL not saved to database

**Solution:**
```python
# Check if ProctoringPDF record exists
from evaluation.models import ProctoringPDF
proctoring_pdf = ProctoringPDF.objects.filter(interview_id=interview_id).first()
if proctoring_pdf:
    print(f"GCS URL: {proctoring_pdf.gcs_url}")
else:
    print("No ProctoringPDF record found")
```

### **Issue: URL is malformed**
**Solution:**
- Check URL cleaning logic in `evaluation/services.py:418-476`
- Ensure `upload_pdf_to_gcs()` returns clean URL
- Verify URL format: must start with `https://storage.googleapis.com/`

### **Issue: PDF opens but shows 404 or Access Denied**
**Possible Causes:**
1. GCS bucket permissions not set correctly
2. File was deleted from GCS
3. URL is incorrect

**Solution:**
- Check GCS bucket permissions (public read access)
- Verify file exists in GCS bucket
- Test URL directly in browser

---

## 📝 Summary

**Proctoring PDF URL Flow:**
1. ✅ **Generated** during evaluation creation after interview completion
2. ✅ **Stored** in `ProctoringPDF` table (primary) and `Evaluation.details` (fallback)
3. ✅ **Retrieved** by serializer from `ProctoringPDF` table
4. ✅ **Displayed** as download link in frontend
5. ✅ **Opened** directly from GCS - **NO backend processing** when accessed

**When PDF is opened:**
- Browser makes direct HTTP request to GCS
- GCS serves PDF file directly
- No Django backend involvement
- No authentication required (if bucket is public)

