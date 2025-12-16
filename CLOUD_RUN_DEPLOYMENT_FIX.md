# 🔧 Cloud Run Deployment Fix

## Problem
Container failed to start and listen on port 8080 within the allocated timeout.

## Solution
Updated Dockerfile to use a startup script that:
1. Properly handles PORT environment variable
2. Continues even if migrations fail
3. Provides better logging
4. Uses `exec` to properly forward signals

## Changes Made

### 1. Created `start.sh` startup script
- Reads PORT from environment variable
- Runs migrations (non-blocking)
- Starts Gunicorn with proper port binding
- Uses `exec` for signal handling

### 2. Updated `Dockerfile`
- Uses startup script instead of inline CMD
- Simplified healthcheck
- Better error handling

## Files Changed
- ✅ `Dockerfile` - Updated to use startup script
- ✅ `start.sh` - New startup script

## Next Steps

### 1. Commit and Push Changes

```bash
# In your backend repository
git add Dockerfile start.sh
git commit -m "Fix Cloud Run deployment: Use startup script for proper port handling"
git push origin main
```

### 2. Redeploy to Cloud Run

**Option A: Using Cloud Build Trigger (Recommended)**

If you have a Cloud Build trigger set up, just push to GitHub and it will automatically rebuild and redeploy.

**Option B: Manual Deployment**

```bash
# Set variables
export PROJECT_ID=eastern-team-480811-e6
export REGION=asia-south2
export SERVICE_NAME=ai-interviewer-backend
export IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
export CLOUD_SQL_CONNECTION="eastern-team-480811-e6:asia-south2:ai-interviewer-db1"
export DATABASE_URL="postgresql://db_user:Admin12345@/ai_interviewer_db1?host=/cloudsql/${CLOUD_SQL_CONNECTION}"

# Set API keys
export DJANGO_SECRET_KEY=your-secret-key
export GEMINI_API_KEY=your-gemini-key
export DEEPGRAM_API_KEY=your-deepgram-key

# Build and deploy
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True,DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY},GEMINI_API_KEY=${GEMINI_API_KEY},DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY},DJANGO_DEBUG=False" \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --port=8080 \
  --project=$PROJECT_ID
```

### 3. Check Logs

```bash
# View recent logs
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --limit=50

# Follow logs in real-time
gcloud run services logs tail $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID
```

### 4. Test Deployment

```bash
# Get service URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

# Test health endpoint
curl $BACKEND_URL/api/health/

# Or test root
curl $BACKEND_URL/
```

## Expected Logs

After deployment, you should see in the logs:

```
🚀 Starting Django Backend on port 8080
📋 Environment check:
   PORT=8080
   DATABASE_URL=postgresql://db_user:Admin12345@/ai_interviewer_db1?host=/cloudsql/...
📊 Running database migrations...
✅ Migrations completed successfully
🌐 Starting Gunicorn server on 0.0.0.0:8080
[INFO] Starting gunicorn 21.x.x
[INFO] Listening at: http://0.0.0.0:8080
[INFO] Using worker: sync
[INFO] Booting worker with pid: X
```

## Troubleshooting

### Issue: Still getting port timeout error

**Check:**
1. PORT environment variable is set in Cloud Run
2. Startup script is executable (`chmod +x start.sh`)
3. Gunicorn is binding to `0.0.0.0:$PORT` (not `127.0.0.1`)

**Solution:**
```bash
# Verify PORT is set
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format="value(spec.template.spec.containers[0].env)"

# Check if port 8080 is exposed
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format="value(spec.template.spec.containers[0].ports)"
```

### Issue: Migrations failing

**Check logs for migration errors:**
```bash
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --limit=100 | grep -i migration
```

**Solution:**
- Check database connection string
- Verify Cloud SQL instance is running
- Check Cloud Run service account has Cloud SQL Client role

### Issue: Database connection fails

**Verify Cloud SQL connection:**
```bash
# Check Cloud SQL instance status
gcloud sql instances describe ai-interviewer-db1 \
  --project=$PROJECT_ID

# Test connection from Cloud Run
gcloud run jobs create test-db-connection \
  --image $IMAGE_NAME \
  --region $REGION \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True" \
  --command="python" \
  --args="-c,import django; django.setup(); from django.db import connection; connection.ensure_connection(); print('✅ Database connection successful')" \
  --project=$PROJECT_ID

gcloud run jobs execute test-db-connection --region $REGION --project=$PROJECT_ID
```

## ✅ Success Indicators

- [ ] Container starts successfully
- [ ] Logs show "Starting Gunicorn server on 0.0.0.0:8080"
- [ ] Health check passes
- [ ] Service URL is accessible
- [ ] API endpoints respond correctly

---

**Last Updated**: 2025-01-27

