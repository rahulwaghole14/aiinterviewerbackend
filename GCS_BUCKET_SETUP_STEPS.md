# GCS Bucket Setup Steps

## Issue: Permission Denied

You're getting `storage.buckets.create` permission denied. Here are the solutions:

## Solution 1: Grant Yourself Permission (Recommended)

If you have project owner/admin access, grant yourself the Storage Admin role:

```bash
# Get your email
YOUR_EMAIL="rsl.jayshree1803@gmail.com"
PROJECT_ID="eastern-team-480811-e6"

# Grant Storage Admin role
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="user:${YOUR_EMAIL}" \
    --role="roles/storage.admin"
```

Then create the bucket:

```bash
export PROJECT_ID="eastern-team-480811-e6"
export BUCKET_NAME="ai-interview-pdfs-${PROJECT_ID}"

# Create bucket
gsutil mb -p ${PROJECT_ID} -l asia-southeast1 gs://${BUCKET_NAME}

# Make bucket publicly readable
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}
```

## Solution 2: Use gcloud Instead of gsutil

Sometimes `gcloud` works when `gsutil` doesn't:

```bash
export PROJECT_ID="eastern-team-480811-e6"
export BUCKET_NAME="ai-interview-pdfs-${PROJECT_ID}"

# Create bucket using gcloud
gcloud storage buckets create gs://${BUCKET_NAME} \
    --project=${PROJECT_ID} \
    --location=asia-southeast1

# Make bucket publicly readable
gcloud storage buckets add-iam-policy-binding gs://${BUCKET_NAME} \
    --member="allUsers" \
    --role="roles/storage.objectViewer"
```

## Solution 3: Ask Project Owner to Create Bucket

If you don't have admin access, ask someone with `roles/owner` or `roles/storage.admin` to:

1. Create the bucket using the commands above
2. Grant you access to use it

## After Bucket Creation

### Step 1: Grant Cloud Run Service Account Permissions

```bash
export PROJECT_ID="eastern-team-480811-e6"

# Get project number
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")

# Grant Storage Object Admin role
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

### Step 2: Set Cloud Run Environment Variable

```bash
export PROJECT_ID="eastern-team-480811-e6"
export BUCKET_NAME="ai-interview-pdfs-${PROJECT_ID}"

gcloud run services update talaroai \
  --region asia-southeast1 \
  --update-env-vars="GCS_BUCKET_NAME=${BUCKET_NAME}" \
  --project=${PROJECT_ID}
```

### Step 3: Verify Setup

```bash
# List bucket contents (should be empty initially)
gsutil ls gs://${BUCKET_NAME}

# Check bucket permissions
gsutil iam get gs://${BUCKET_NAME}
```

## Quick Test

After setup, complete an interview and check:

1. **Check Cloud Run logs** for "✅ PDF uploaded to GCS"
2. **List bucket contents**:
   ```bash
   gsutil ls -r gs://${BUCKET_NAME}/
   ```
3. **Download a PDF** from the frontend and verify it works

## Troubleshooting

### Still Getting Permission Errors?

1. **Check your current roles**:
   ```bash
   gcloud projects get-iam-policy ${PROJECT_ID} \
     --flatten="bindings[].members" \
     --filter="bindings.members:user:rsl.jayshree1803@gmail.com"
   ```

2. **Check if bucket already exists**:
   ```bash
   gsutil ls gs://ai-interview-pdfs-${PROJECT_ID}
   ```

3. **Try creating with a different name**:
   ```bash
   export BUCKET_NAME="ai-interview-pdfs-$(date +%s)"
   gsutil mb -p ${PROJECT_ID} -l asia-southeast1 gs://${BUCKET_NAME}
   ```

## Alternative: Use Existing Bucket

If you already have a GCS bucket, you can use it:

```bash
# List existing buckets
gsutil ls

# Use an existing bucket (replace with your bucket name)
export BUCKET_NAME="your-existing-bucket-name"

# Make it publicly readable (if not already)
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}
```

