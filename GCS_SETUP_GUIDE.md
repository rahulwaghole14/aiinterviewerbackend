# Google Cloud Storage Setup Guide for PDF Storage

This guide explains how to set up Google Cloud Storage (GCS) to store and serve PDFs (proctoring reports and Q&A evaluation PDFs) for your AI Interview Portal.

## Benefits of Using GCS

1. **Scalability**: No storage limits on Cloud Run instances
2. **Reliability**: Persistent storage that survives container restarts
3. **Performance**: Fast CDN-like access to PDFs
4. **Cost-effective**: Pay only for storage and bandwidth used
5. **Accessibility**: PDFs accessible via public URLs

## Prerequisites

1. Google Cloud Project with billing enabled
2. `gcloud` CLI installed and authenticated
3. Appropriate IAM permissions

## Step 1: Create GCS Bucket

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
export BUCKET_NAME="ai-interview-pdfs-${PROJECT_ID}"

# Create bucket
gsutil mb -p ${PROJECT_ID} -l asia-southeast1 gs://${BUCKET_NAME}

# Make bucket publicly readable (for PDF downloads)
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}

# Or use fine-grained access control (recommended for production)
# Create a service account for Cloud Run
gcloud iam service-accounts create pdf-storage-sa \
    --display-name="PDF Storage Service Account" \
    --project=${PROJECT_ID}

# Grant storage admin role
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:pdf-storage-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
```

## Step 2: Configure Environment Variables

Add to your Cloud Run service environment variables:

```bash
# Set GCS bucket name
gcloud run services update talaroai \
  --region asia-southeast1 \
  --update-env-vars="GCS_BUCKET_NAME=${BUCKET_NAME}" \
  --project=${PROJECT_ID}

# If using service account (recommended)
gcloud run services update talaroai \
  --region asia-southeast1 \
  --service-account="pdf-storage-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project=${PROJECT_ID}
```

Or add to your `.env` file for local development:

```env
GCS_BUCKET_NAME=ai-interview-pdfs-your-project-id
GCS_USE_SIGNED_URLS=false  # Set to true for private access
```

## Step 3: Grant Cloud Run Service Account Permissions

If using the default Cloud Run service account:

```bash
# Get your Cloud Run service account email
export CLOUD_RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant Storage Object Admin role
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${CLOUD_RUN_SA}" \
    --role="roles/storage.objectAdmin"
```

## Step 4: Verify Setup

1. **Check bucket exists:**
   ```bash
   gsutil ls gs://${BUCKET_NAME}
   ```

2. **Test upload (optional):**
   ```bash
   echo "test" > test.txt
   gsutil cp test.txt gs://${BUCKET_NAME}/test/
   gsutil rm gs://${BUCKET_NAME}/test/test.txt
   ```

## Step 5: Deploy Updated Code

The code changes include:
- `interview_app/gcs_storage.py` - GCS utility functions
- Updated PDF generation to upload to GCS
- Updated download endpoints to serve from GCS

Deploy using Cloud Build or manually:

```bash
# If using Cloud Build trigger, push to GitHub
git push origin main

# Or manually deploy
gcloud builds submit --config cloudbuild-backend.yaml
```

## How It Works

### PDF Generation Flow

1. **Proctoring PDF:**
   - Generated when interview completes
   - Uploaded to `gs://bucket/proctoring_pdfs/proctoring_report_{interview_id}_{timestamp}.pdf`
   - GCS URL stored in `evaluation.details['proctoring_pdf_gcs_url']`
   - Local copy also saved as fallback

2. **Q&A Evaluation PDF:**
   - Generated on-demand when user clicks download
   - Uploaded to `gs://bucket/evaluation_pdfs/qna_evaluation_{session_key}_{timestamp}.pdf`
   - GCS URL stored in `evaluation.details['qna_pdf_gcs_url']`

### PDF Access Flow

1. **Frontend requests PDF:**
   - Calls `/api/proctoring/pdf/<session_id>/` or `/ai/transcript_pdf?session_key=...`

2. **Backend checks:**
   - First: Check for GCS URL in evaluation details
   - If GCS URL exists: Redirect to GCS public URL
   - If not: Try to download from GCS using file path
   - Fallback: Serve from local file system

3. **User downloads:**
   - PDF served directly from GCS (fast, scalable)
   - Or served from backend (fallback)

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

**Solution:** Grant Storage Object Admin role to Cloud Run service account:
```bash
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${CLOUD_RUN_SA}" \
    --role="roles/storage.objectAdmin"
```

### Issue: PDFs not accessible publicly

**Solution:** Make bucket or objects publicly readable:
```bash
# Option 1: Make entire bucket public (not recommended for production)
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}

# Option 2: Make individual objects public (done automatically in code)
# The code calls blob.make_public() after upload
```

### Issue: GCS upload fails silently

**Check:**
1. `GCS_BUCKET_NAME` environment variable is set
2. Service account has correct permissions
3. Bucket exists and is accessible
4. Check Cloud Run logs for error messages

### Issue: PDFs still served from local storage

**Solution:** 
- Verify GCS upload is successful (check logs)
- Check `evaluation.details['proctoring_pdf_gcs_url']` exists
- Ensure bucket is publicly readable or using signed URLs

## Cost Considerations

- **Storage:** ~$0.020 per GB/month
- **Operations:** ~$0.05 per 10,000 operations
- **Bandwidth:** First 1GB/month free, then ~$0.12/GB

For typical usage (1000 interviews/month, 2MB PDF each):
- Storage: ~2GB = $0.04/month
- Operations: ~2000 uploads = $0.01/month
- **Total: ~$0.05/month**

## Security Best Practices

1. **Use signed URLs for private access:**
   ```python
   # In settings.py
   GCS_USE_SIGNED_URLS = True
   ```

2. **Restrict bucket access:**
   - Don't make entire bucket public
   - Use IAM policies to control access
   - Use signed URLs with expiration

3. **Monitor access:**
   - Enable Cloud Storage audit logs
   - Set up alerts for unusual access patterns

## Migration from Local Storage

If you have existing PDFs in local storage:

1. **Upload existing PDFs to GCS:**
   ```bash
   gsutil -m cp -r media/proctoring_pdfs/* gs://${BUCKET_NAME}/proctoring_pdfs/
   gsutil -m cp -r media/evaluation_pdfs/* gs://${BUCKET_NAME}/evaluation_pdfs/
   ```

2. **Update evaluation records:**
   - Run a migration script to update `evaluation.details` with GCS URLs
   - Or let the system regenerate PDFs on next access

## Testing

1. **Test PDF generation:**
   - Complete an interview
   - Check Cloud Run logs for "✅ PDF uploaded to GCS"
   - Verify PDF appears in GCS bucket

2. **Test PDF download:**
   - Click "Download Proctoring Warnings Report" in frontend
   - Should redirect to GCS URL or serve from GCS
   - Verify PDF downloads correctly

3. **Test fallback:**
   - Temporarily disable GCS (remove `GCS_BUCKET_NAME`)
   - Verify PDFs still work from local storage

## Support

For issues or questions:
1. Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision"`
2. Check GCS bucket: `gsutil ls -l gs://${BUCKET_NAME}/proctoring_pdfs/`
3. Verify environment variables: `gcloud run services describe talaroai --region asia-southeast1`

