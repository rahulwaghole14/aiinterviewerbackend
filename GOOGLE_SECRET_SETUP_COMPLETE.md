# 🔐 Complete Google Cloud Secret Setup Guide

## ✅ Code Updated

The code now supports **3 methods** to get Google Cloud credentials (in priority order):

1. **Environment Variable** (`GOOGLE_APPLICATION_CREDENTIALS`) - From Cloud Run secret mount
2. **Secret Manager API** - Fetches `my-service-key` secret at runtime
3. **Hardcoded File Path** - Fallback to `ringed-reach-471807-m3-cf0ec93e3257.json`

---

## Step 1: Grant Secret Manager Access to Cloud Run

The Cloud Run service account needs permission to access Secret Manager:

```bash
# Get the Cloud Run service account
PROJECT_NUMBER=$(gcloud projects describe eastern-team-480811-e6 --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant Secret Manager Secret Accessor role
gcloud projects add-iam-policy-binding eastern-team-480811-e6 \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project=eastern-team-480811-e6
```

---

## Step 2: Choose Your Method

### Method A: Mount Secret as File (Recommended)

**Try this command** (corrected syntax):

```bash
gcloud run services update talaroai \
  --region asia-southeast1 \
  --set-secrets=/etc/secrets/my-service-key.json=my-service-key:latest \
  --update-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/my-service-key.json" \
  --project=eastern-team-480811-e6
```

**If that doesn't work**, try without the leading slash:

```bash
gcloud run services update talaroai \
  --region asia-southeast1 \
  --set-secrets=etc/secrets/my-service-key.json=my-service-key:latest \
  --update-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/my-service-key.json" \
  --project=eastern-team-480811-e6
```

### Method B: Use Secret Manager API (No Mount Needed)

**No Cloud Run update needed!** The code will automatically fetch from Secret Manager.

Just ensure:
1. ✅ Secret exists: `my-service-key`
2. ✅ Service account has `roles/secretmanager.secretAccessor` role (Step 1)
3. ✅ Code is deployed (already done ✅)

---

## Step 3: Verify Setup

### Check Secret Exists:
```bash
gcloud secrets describe my-service-key --project=eastern-team-480811-e6
```

### Check Service Account Permissions:
```bash
PROJECT_NUMBER=$(gcloud projects describe eastern-team-480811-e6 --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects get-iam-policy eastern-team-480811-e6 \
  --flatten="bindings[].members" \
  --filter="bindings.members:${SERVICE_ACCOUNT}" \
  --format="table(bindings.role)"
```

### Test TTS After Deployment:
1. Start an interview
2. Check logs for:
   - `"✅ Loaded credentials from Secret Manager"` OR
   - `"✅ Google Cloud credentials set"`
3. Verify TTS works (questions are spoken)

---

## Troubleshooting

### Issue: "Permission denied" when accessing secret

**Solution**: Run Step 1 to grant Secret Manager access

### Issue: Secret mount path not found

**Solution**: Use Method B (Secret Manager API) - no mount needed!

### Issue: Code still uses hardcoded path

**Check logs** - the code will try Secret Manager first, then fallback to file.
If you see `"⚠️ Could not load from Secret Manager"`, check:
- Secret name is correct: `my-service-key`
- Service account has permissions
- Secret has a version (use `latest`)

---

## Recommended Approach

**Use Method B (Secret Manager API)** because:
- ✅ No Cloud Run configuration needed
- ✅ Works automatically
- ✅ More secure (no file paths)
- ✅ Code already updated ✅

Just ensure:
1. ✅ Secret exists: `my-service-key`
2. ✅ Service account has permissions (run Step 1)
3. ✅ Deploy updated code (already done ✅)

---

## Quick Setup Command

Run this to grant permissions (if not already done):

```bash
PROJECT_NUMBER=$(gcloud projects describe eastern-team-480811-e6 --format="value(projectNumber)")
gcloud projects add-iam-policy-binding eastern-team-480811-e6 \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Then deploy the updated code and test!

---

**Last Updated**: 2025-01-27

