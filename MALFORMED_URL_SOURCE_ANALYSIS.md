# Malformed URL Source Analysis

## Problem
The proctoring PDF URL is malformed:
```
https://talaroai-310576915040.asia-southeast1.run.apphttps//storage.googleapis.com/ai-interview-pdfs-eastern-team-480811-e6/proctoring_pdfs/proctoring_report_0f4b3cc9-6142-4a2e-9cfd-fa9c7a9fedb2_20251223_080048.pdf
```

## Expected Format
```
https://storage.googleapis.com/ai-interview-pdfs-eastern-team-480811-e6/proctoring_pdfs/proctoring_report_0f4b3cc9-6142-4a2e-9cfd-fa9c7a9fedb2_20251223_080048.pdf
```

## Where URLs Are Created and Stored

### 1. URL Creation (`interview_app/gcs_storage.py`)
- **Function:** `upload_pdf_to_gcs()`
- **Line:** 72
- **Returns:** `blob.public_url` - This should be a clean GCS URL
- **Status:** ✅ Correct - Returns clean URL from Google Cloud Storage

### 2. URL Storage (`evaluation/services.py`)
- **Function:** `create_evaluation_from_session()`
- **Lines:** 416-536
- **Process:**
  1. Gets `gcs_url` from `generate_proctoring_pdf()` → `upload_pdf_to_gcs()`
  2. **Cleans the URL** (lines 418-476) - Removes malformed prefixes
  3. **Saves to `Evaluation.details`** (lines 510-512)
  4. **Saves to `ProctoringPDF` table** (lines 518-536)

### 3. URL Migration (`evaluation/migrations/0011_migrate_existing_proctoring_urls.py`)
- **Purpose:** Copy URLs from `Evaluation.details` to `ProctoringPDF` table
- **Problem:** ⚠️ **Original migration did NOT clean URLs before copying**
- **Fix:** Updated migration now cleans URLs before storing

## Root Cause Analysis

The malformed URL pattern `https://talaroai-...run.apphttps//storage.googleapis.com/...` suggests:

1. **App URL concatenation:** The Cloud Run app URL (`https://talaroai-310576915040.asia-southeast1.run.app`) was somehow concatenated with the GCS URL
2. **When it happened:** 
   - Before URL cleaning logic was added (old code)
   - OR during migration that copied URLs without cleaning
   - OR from `blob.public_url` if GCS client was misconfigured

## Where URLs Are Stored

### Database Tables:
1. **`evaluation_evaluation.details`** (JSONField)
   - Field: `proctoring_pdf_gcs_url`
   - Field: `proctoring_pdf_url`
   - Field: `proctoring_pdf` (local path)

2. **`evaluation_proctoringpdf`** (Dedicated table)
   - Field: `gcs_url` (URLField)
   - Field: `local_path` (CharField)

## Solution

### 1. Backend Serializer (`interviews/serializers.py`)
- **Function:** `get_proctoring_pdf()`
- **Status:** ✅ Fixed - Cleans URLs before returning

### 2. Frontend (`frontend/src/components/CandidateDetails.jsx`)
- **Status:** ✅ Fixed - Cleans URLs before opening

### 3. Database Migration (`evaluation/migrations/0012_clean_proctoringpdf_malformed_urls.py`)
- **Status:** ✅ Created - Cleans existing malformed URLs in database

### 4. Migration 0011 Update
- **Status:** ✅ Updated - Now cleans URLs before copying from `Evaluation.details`

## Next Steps

1. **Run migrations:**
   ```bash
   python manage.py migrate evaluation
   ```

2. **Verify URLs are cleaned:**
   - Check `ProctoringPDF` table for clean URLs
   - Check `Evaluation.details` for clean URLs

3. **Test proctoring PDF download:**
   - Should open clean GCS URL directly
   - No app URL concatenation

## Prevention

- ✅ URL cleaning in `evaluation/services.py` before storing
- ✅ URL cleaning in serializer before returning
- ✅ URL cleaning in frontend before opening
- ✅ Migration 0011 now cleans URLs during migration
- ✅ Migration 0012 cleans existing malformed URLs

