# 🔧 Fix Interview URL to Use Cloud Run Instead of Localhost

## Problem
Interview links are being generated with `localhost:8000` instead of the Cloud Run URL `https://talaroai-310576915040.asia-southeast1.run.app`.

## Root Cause
The code was using `BACKEND_URL` from settings, which defaults to `localhost:8000` when not set in Cloud Run environment variables.

## Solution
Updated the code to automatically detect Cloud Run URL from environment variables when `BACKEND_URL` is not set.

## Changes Made

### 1. Updated `interviews/models.py` - `get_interview_url()` method
- Now detects Cloud Run URL from `K_SERVICE`, `GOOGLE_CLOUD_REGION`, and `GOOGLE_CLOUD_PROJECT_NUMBER` environment variables
- Falls back to `BACKEND_URL` environment variable if set
- Only uses `localhost:8000` as final fallback

### 2. Updated `notifications/services.py` - Interview URL generation
- Uses the same Cloud Run detection logic
- Generates URLs in format: `https://service-name-project-number.region.run.app/?session_key=xxx`

## How It Works

The code now detects Cloud Run URL automatically:

```python
# 1. Check BACKEND_URL from settings
base_url = getattr(settings, "BACKEND_URL", None)

# 2. If not set or localhost, check environment variable
if not base_url or "localhost" in base_url.lower():
    base_url = os.environ.get("BACKEND_URL", None)

# 3. If still not set, detect from Cloud Run environment
if not base_url or "localhost" in base_url.lower():
    service_name = os.environ.get("K_SERVICE")  # e.g., "talaroai"
    region = os.environ.get("GOOGLE_CLOUD_REGION", "asia-southeast1")
    project_number = os.environ.get("GOOGLE_CLOUD_PROJECT_NUMBER", "310576915040")
    
    if service_name:
        base_url = f"https://{service_name}-{project_number}.{region}.run.app"
```

## Expected Result

After deployment, interview links will be:
- ✅ `https://talaroai-310576915040.asia-southeast1.run.app/?session_key=xxx`
- ❌ NOT `http://localhost:8000/?session_key=xxx`

## Optional: Set BACKEND_URL Explicitly

For more control, you can set `BACKEND_URL` environment variable in Cloud Run:

```bash
gcloud run services update talaroai \
  --region asia-southeast1 \
  --set-env-vars="BACKEND_URL=https://talaroai-310576915040.asia-southeast1.run.app" \
  --project=eastern-team-480811-e6
```

But this is **not required** - the code will auto-detect it now.

## Testing

After deploying the updated code:

1. **Create an interview** via the API or admin panel
2. **Check the interview URL** - it should use Cloud Run URL
3. **Send email notification** - the link in the email should use Cloud Run URL
4. **Access the link** - it should work from anywhere (not just localhost)

## Files Changed
- ✅ `interviews/models.py` - Updated `get_interview_url()` method
- ✅ `notifications/services.py` - Updated URL generation logic

## Next Steps

1. **Commit and push** these changes:
```bash
git add interviews/models.py notifications/services.py
git commit -m "Fix interview URL to use Cloud Run URL instead of localhost"
git push origin main
```

2. **Deploy to Cloud Run** (if using Cloud Build trigger, it will auto-deploy)

3. **Test** by creating a new interview and checking the generated URL

---

**Last Updated**: 2025-01-27

