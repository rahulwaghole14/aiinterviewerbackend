# Complete Flow: Proctoring PDF URL from Database to Download Button

## 📋 Overview
This document traces the complete flow of the proctoring PDF URL from database storage to the download button click on the evaluation page.

---

## 🔄 Complete Step-by-Step Flow

### **STEP 1: URL Storage in Database** 
**Location:** `evaluation/services.py` (lines 518-536)

**Process:**
1. After interview completion, `create_evaluation_from_session()` is called
2. `generate_proctoring_pdf()` creates the PDF and uploads to GCS
3. `upload_pdf_to_gcs()` returns clean GCS URL: `https://storage.googleapis.com/bucket/path/file.pdf`
4. URL is cleaned to remove any malformed prefixes (lines 418-476)
5. **Stored in TWO places:**
   - `Evaluation.details['proctoring_pdf_gcs_url']` (JSONField)
   - `ProctoringPDF.gcs_url` (URLField) ← **PRIMARY SOURCE**

**Database Tables:**
```sql
-- Table 1: evaluation_evaluation
details = {
  "proctoring_pdf_gcs_url": "https://storage.googleapis.com/...",
  "proctoring_pdf_url": "https://storage.googleapis.com/...",
  "proctoring_pdf": "proctoring_pdfs/file.pdf"
}

-- Table 2: evaluation_proctoringpdf (PRIMARY SOURCE)
gcs_url = "https://storage.googleapis.com/..."
local_path = "proctoring_pdfs/file.pdf"
```

**Code:**
```python
# evaluation/services.py:521-527
proctoring_pdf, created = ProctoringPDF.objects.update_or_create(
    interview=interview,
    defaults={
        'gcs_url': clean_gcs_url,  # Clean URL stored here
        'local_path': local_path,
    }
)
```

---

### **STEP 2: Frontend Requests Interview Data**
**Location:** `frontend/src/components/CandidateDetails.jsx` (lines 361-377)

**Process:**
1. Component mounts or candidate changes
2. `fetchInterviews()` function is called
3. Makes GET request to `/api/interviews/`
4. Includes authentication token in headers

**Code:**
```javascript
// CandidateDetails.jsx:367-375
const interviewsResponse = await fetch(`${baseURL}/api/interviews/`, {
  method: "GET",
  headers: {
    Authorization: `Token ${authToken}`,
    "Content-Type": "application/json",
    Accept: "application/json",
  },
  credentials: "include",
});
```

---

### **STEP 3: Backend API Endpoint Processes Request**
**Location:** `interviews/views.py` (InterviewViewSet)

**Process:**
1. Django REST Framework receives GET `/api/interviews/`
2. `InterviewViewSet.list()` or `retrieve()` is called
3. Queries `Interview` objects from database
4. Uses `InterviewSerializer` to serialize data

**What happens:**
- Fetches `Interview` objects
- Includes related `Evaluation` objects
- Includes related `ProctoringPDF` objects via serializer

---

### **STEP 4: Serializer Retrieves Proctoring PDF URL**
**Location:** `interviews/serializers.py` (lines 774-840)

**Process:**
1. `InterviewSerializer` serializes each interview
2. `get_proctoring_pdf()` method is called (SerializerMethodField)
3. Queries `ProctoringPDF` table: `ProctoringPDF.objects.filter(interview=obj).first()`
4. **URL Cleaning happens here:**
   - Extracts GCS URL from `proctoring_pdf.gcs_url`
   - Removes malformed prefixes (e.g., `run.apphttps//`)
   - Validates URL starts with `https://storage.googleapis.com/`
   - Returns clean URL or `None`

**Code:**
```python
# interviews/serializers.py:780-821
proctoring_pdf = ProctoringPDF.objects.filter(interview=obj).first()
if proctoring_pdf and proctoring_pdf.gcs_url:
    original_url = proctoring_pdf.gcs_url.strip()
    # Clean URL to remove malformed prefixes
    clean_url = clean_gcs_url(original_url)  # Cleaning logic
    if clean_url and clean_url.startswith('https://storage.googleapis.com/'):
        return {
            'gcs_url': clean_url,  # Clean URL returned
            'local_path': proctoring_pdf.local_path,
            ...
        }
```

**Returned JSON Structure:**
```json
{
  "id": 123,
  "candidate": {...},
  "proctoring_pdf": {
    "gcs_url": "https://storage.googleapis.com/bucket/path/file.pdf",
    "local_path": "proctoring_pdfs/file.pdf",
    "created_at": "2025-12-23T08:00:48Z",
    "updated_at": "2025-12-23T08:00:48Z"
  },
  "evaluation": {...}
}
```

---

### **STEP 5: Frontend Receives and Processes Data**
**Location:** `frontend/src/components/CandidateDetails.jsx` (lines 377-525)

**Process:**
1. Response received: `interviewsResponse.json()`
2. Data is processed and stored in `interviews` state
3. Each interview object contains `proctoring_pdf` object
4. `proctoring_pdf.gcs_url` is available for use

**Code:**
```javascript
// CandidateDetails.jsx:377-465
const interviewsData = await interviewsResponse.json();
// Process and store in state
setInterviews(processedInterviews);
```

**State Structure:**
```javascript
interviews = [
  {
    id: 123,
    proctoring_pdf: {
      gcs_url: "https://storage.googleapis.com/...",
      local_path: "...",
      ...
    },
    evaluation: {...}
  }
]
```

---

### **STEP 6: Frontend Renders Download Button**
**Location:** `frontend/src/components/CandidateDetails.jsx` (lines 1610-1680)

**Process:**
1. Component renders interview details
2. Checks if `interview.evaluation` exists
3. If exists, renders "Proctoring Warnings Report" card
4. Displays download button with text "Download Proctoring Warnings Report"

**Code:**
```javascript
// CandidateDetails.jsx:1611-1614
{interview.evaluation && (
  <div className="evaluation-card proctoring-report-card">
    <h4 className="card-title">Proctoring Warnings Report</h4>
    <div className="proctoring-download-section">
      <button type="button" onClick={...}>
        Download Proctoring Warnings Report
      </button>
    </div>
  </div>
)}
```

---

### **STEP 7: User Clicks Download Button**
**Location:** `frontend/src/components/CandidateDetails.jsx` (lines 1617-1680)

**Process:**
1. User clicks "Download Proctoring Warnings Report" button
2. `onClick` handler is triggered
3. **Retrieves URL:** `interview.proctoring_pdf?.gcs_url`
4. **Safety Check:** Validates URL exists
5. **Client-Side URL Cleaning (safety check):**
   - Extracts GCS URL part (from `storage.googleapis.com` onwards)
   - Removes malformed prefixes (e.g., `run.apphttps//`)
   - Validates URL format
6. **Opens URL:** `window.open(cleanUrl, '_blank')`

**Code:**
```javascript
// CandidateDetails.jsx:1626-1680
onClick={(e) => {
  e.preventDefault();
  e.stopPropagation();
  
  // Step 1: Get URL from state
  let gcsUrl = interview.proctoring_pdf?.gcs_url;
  
  // Step 2: Validate URL exists
  if (!gcsUrl) {
    alert('Proctoring PDF not available...');
    return;
  }
  
  // Step 3: Clean URL (safety check)
  const originalUrl = gcsUrl;
  if (gcsUrl.includes('storage.googleapis.com')) {
    // Extract GCS part
    const gcsIndex = gcsUrl.indexOf('storage.googleapis.com');
    let cleanUrl = gcsUrl.substring(gcsIndex);
    
    // Remove malformed prefixes
    cleanUrl = cleanUrl.replace(/^https?\/\/+/g, '');
    cleanUrl = cleanUrl.replace(/^https?:\/\/+/g, '');
    cleanUrl = cleanUrl.replace(/^[^/]+\.(app|run|com)https?\/\/+/g, '');
    
    // Construct clean URL
    if (cleanUrl.startsWith('storage.googleapis.com')) {
      gcsUrl = `https://${cleanUrl}`;
    }
  }
  
  // Step 4: Validate final URL
  if (!gcsUrl.startsWith('https://storage.googleapis.com/')) {
    alert('Error: Invalid PDF URL format...');
    return;
  }
  
  // Step 5: Open URL in new tab
  try {
    const urlObj = new URL(gcsUrl);
    window.open(gcsUrl, '_blank', 'noopener,noreferrer');
  } catch (urlError) {
    alert('Error: Invalid PDF URL format...');
  }
}}
```

---

### **STEP 8: Browser Opens PDF**
**Process:**
1. Browser receives clean GCS URL: `https://storage.googleapis.com/bucket/path/file.pdf`
2. Makes HTTP GET request to Google Cloud Storage
3. GCS serves the PDF file (public blob)
4. Browser displays PDF in new tab or downloads it

**Final URL Format:**
```
https://storage.googleapis.com/ai-interview-pdfs-eastern-team-480811-e6/proctoring_pdfs/proctoring_report_0f4b3cc9-6142-4a2e-9cfd-fa9c7a9fedb2_20251223_080048.pdf
```

---

## 🔍 Key Points

### **URL Cleaning Locations:**
1. ✅ **Backend Storage** (`evaluation/services.py`) - Cleans before storing
2. ✅ **Backend Serializer** (`interviews/serializers.py`) - Cleans before returning
3. ✅ **Frontend Button** (`CandidateDetails.jsx`) - Cleans before opening (safety check)

### **Primary Data Source:**
- **`ProctoringPDF.gcs_url`** is the PRIMARY source
- Frontend uses `interview.proctoring_pdf.gcs_url`
- No fallbacks to `Evaluation.details` anymore

### **URL Format Validation:**
- Must start with: `https://storage.googleapis.com/`
- Removes patterns: `run.apphttps//`, `https//`, etc.
- Returns `None` if URL is invalid

### **Error Handling:**
- If URL is missing: Shows alert "Proctoring PDF not available..."
- If URL is invalid: Shows alert "Error: Invalid PDF URL format..."
- If URL is malformed: Cleans it automatically

---

## 📊 Flow Diagram

```
Database (ProctoringPDF.gcs_url)
    ↓
Backend Serializer (get_proctoring_pdf)
    ↓ [Cleans URL]
API Response (JSON)
    ↓
Frontend State (interview.proctoring_pdf.gcs_url)
    ↓
Button Click Handler
    ↓ [Cleans URL again - safety check]
window.open(cleanUrl)
    ↓
Browser Opens GCS URL
    ↓
PDF Displayed/Downloaded
```

---

## 🛡️ Safety Measures

1. **Triple Cleaning:**
   - Storage time (backend)
   - Serialization time (backend)
   - Button click time (frontend)

2. **Validation:**
   - URL format validation at each step
   - Returns `None` if invalid
   - Shows user-friendly error messages

3. **No Fallbacks:**
   - Only uses `ProctoringPDF.gcs_url`
   - No fallback to `Evaluation.details`
   - Ensures single source of truth

---

## 📝 Summary

The proctoring PDF URL flows through these steps:
1. **Stored** in `ProctoringPDF` table with clean URL
2. **Retrieved** by serializer and cleaned again
3. **Sent** to frontend via API
4. **Stored** in React state
5. **Displayed** in button
6. **Cleaned** again when button clicked (safety)
7. **Opened** in browser as clean GCS URL

Each step includes URL cleaning and validation to ensure only clean GCS URLs are used.

