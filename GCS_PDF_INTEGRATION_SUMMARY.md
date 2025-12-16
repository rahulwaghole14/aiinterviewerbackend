# Google Cloud Storage PDF Integration - Summary

## Overview

Successfully integrated Google Cloud Storage (GCS) for storing and serving PDFs (proctoring reports and Q&A evaluation PDFs) in the AI Interview Portal. This provides scalable, reliable storage that survives container restarts and reduces storage requirements on Cloud Run instances.

## Changes Made

### 1. New Files Created

- **`interview_app/gcs_storage.py`**: Utility module for GCS operations
  - `upload_pdf_to_gcs()`: Upload PDF bytes to GCS
  - `download_pdf_from_gcs()`: Download PDF from GCS
  - `get_gcs_signed_url()`: Generate signed URLs for private access
  - `delete_pdf_from_gcs()`: Delete PDF from GCS

- **`GCS_SETUP_GUIDE.md`**: Comprehensive setup guide for GCS integration

### 2. Updated Files

#### Backend Files

- **`requirements.txt`**: Added `google-cloud-storage==2.18.2`

- **`interview_app/settings.py`**: Added GCS configuration
  ```python
  GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", None)
  GCS_USE_SIGNED_URLS = os.environ.get("GCS_USE_SIGNED_URLS", "false").lower() == "true"
  ```

- **`evaluation/proctoring_pdf.py`**: Updated to upload PDFs to GCS
  - Generates PDF bytes
  - Uploads to GCS if `GCS_BUCKET_NAME` is configured
  - Returns dict with `{'gcs_url': ..., 'local_path': ...}` if GCS upload succeeds
  - Falls back to local storage if GCS is not configured

- **`evaluation/services.py`**: Updated to handle GCS URLs
  - Handles both dict (GCS) and string (local) results from PDF generation
  - Stores GCS URL in `evaluation.details['proctoring_pdf_gcs_url']`
  - Uses GCS URL as primary download URL

- **`interview_app/views.py`**: Updated download endpoints
  - `download_proctoring_pdf()`: Checks for GCS URL first, redirects if available
  - `download_comprehensive_pdf()`: Uploads Q&A PDF to GCS and stores URL in evaluation

#### Frontend Files

- **`frontend/src/components/CandidateDetails.jsx`**: Updated to use GCS URLs
  - Extracts `proctoring_pdf_gcs_url` from evaluation details
  - Uses GCS URL directly if available, otherwise falls back to API endpoint

## How It Works

### PDF Generation Flow

1. **Proctoring PDF** (generated when interview completes):
   - PDF generated with warnings and snapshots
   - Uploaded to `gs://bucket/proctoring_pdfs/proctoring_report_{interview_id}_{timestamp}.pdf`
   - GCS URL stored in `evaluation.details['proctoring_pdf_gcs_url']`
   - Local copy also saved as fallback

2. **Q&A Evaluation PDF** (generated on-demand):
   - PDF generated with Q&A transcript, coding results, and AI evaluation
   - Uploaded to `gs://bucket/evaluation_pdfs/qna_evaluation_{session_key}_{timestamp}.pdf`
   - GCS URL stored in `evaluation.details['qna_pdf_gcs_url']`

### PDF Access Flow

1. **Frontend requests PDF**:
   - User clicks "Download Proctoring Warnings Report" or "Download Q&A Script + AI Evaluation PDF"

2. **Backend checks**:
   - First: Check for GCS URL in `evaluation.details`
   - If GCS URL exists: Redirect to GCS public URL (fast, scalable)
   - If not: Try to download from GCS using file path
   - Fallback: Serve from local file system

3. **User downloads**:
   - PDF served directly from GCS (preferred) or from backend (fallback)

## Setup Instructions

### 1. Create GCS Bucket

```bash
export PROJECT_ID="your-project-id"
export BUCKET_NAME="ai-interview-pdfs-${PROJECT_ID}"

# Create bucket
gsutil mb -p ${PROJECT_ID} -l asia-southeast1 gs://${BUCKET_NAME}

# Make bucket publicly readable (for PDF downloads)
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}
```

### 2. Configure Cloud Run Environment Variable

```bash
gcloud run services update talaroai \
  --region asia-southeast1 \
  --update-env-vars="GCS_BUCKET_NAME=${BUCKET_NAME}" \
  --project=${PROJECT_ID}
```

### 3. Grant Permissions

```bash
# Get Cloud Run service account
export CLOUD_RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant Storage Object Admin role
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${CLOUD_RUN_SA}" \
    --role="roles/storage.objectAdmin"
```

### 4. Deploy Updated Code

Push to GitHub (if using Cloud Build trigger) or deploy manually:

```bash
git add -A
git commit -m "Add GCS integration for PDF storage"
git push origin main
```

## Benefits

1. **Scalability**: No storage limits on Cloud Run instances
2. **Reliability**: Persistent storage that survives container restarts
3. **Performance**: Fast CDN-like access to PDFs via public URLs
4. **Cost-effective**: Pay only for storage and bandwidth used (~$0.05/month for typical usage)
5. **Accessibility**: PDFs accessible via public URLs from anywhere

## Fallback Behavior

- If `GCS_BUCKET_NAME` is not set: PDFs stored locally only
- If GCS upload fails: PDFs still saved locally, system continues normally
- If GCS URL not available: Backend serves PDFs from local storage

## Testing

1. **Test PDF generation**:
   - Complete an interview
   - Check Cloud Run logs for "✅ PDF uploaded to GCS"
   - Verify PDF appears in GCS bucket: `gsutil ls gs://${BUCKET_NAME}/proctoring_pdfs/`

2. **Test PDF download**:
   - Click "Download Proctoring Warnings Report" in frontend
   - Should redirect to GCS URL or serve from GCS
   - Verify PDF downloads correctly

3. **Test fallback**:
   - Temporarily disable GCS (remove `GCS_BUCKET_NAME`)
   - Verify PDFs still work from local storage

## File Structure in GCS

```
gs://your-bucket/
├── proctoring_pdfs/
│   ├── proctoring_report_123_20251216_143022.pdf
│   └── proctoring_report_456_20251216_150530.pdf
└── evaluation_pdfs/
    ├── qna_evaluation_abc123_20251216_143022.pdf
    └── qna_evaluation_def456_20251216_150530.pdf
```

## Troubleshooting

### Issue: "Permission denied" when uploading

**Solution**: Grant Storage Object Admin role to Cloud Run service account (see Setup Instructions #3)

### Issue: PDFs not accessible publicly

**Solution**: Make bucket publicly readable:
```bash
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}
```

### Issue: GCS upload fails silently

**Check**:
1. `GCS_BUCKET_NAME` environment variable is set
2. Service account has correct permissions
3. Bucket exists and is accessible
4. Check Cloud Run logs for error messages

## Next Steps

1. Set up GCS bucket and configure environment variable
2. Deploy updated code
3. Test PDF generation and download
4. Monitor GCS usage and costs
5. Consider using signed URLs for private access (set `GCS_USE_SIGNED_URLS=true`)

## Support

For detailed setup instructions, see `GCS_SETUP_GUIDE.md`.

