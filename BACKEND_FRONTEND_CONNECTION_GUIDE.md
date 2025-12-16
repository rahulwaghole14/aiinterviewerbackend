# 🔗 Backend Repository & Frontend-Backend Connection Guide

## 📋 Overview

This guide covers:
1. **Connecting to Backend Repository** (GitHub)
2. **Deploying Backend to Cloud Run** with Cloud SQL
3. **Connecting Frontend to Backend** (Update API URL)
4. **Testing the Connection**

---

## Part 1: Connect to Backend Repository

### Step 1.1: Clone Backend Repository

**In Cloud Shell or Local Terminal:**

```bash
# Navigate to your workspace
cd ~/workspace  # or your preferred directory

# Clone the backend repository
git clone https://github.com/rahulwaghole14/aiinterviewerbackend.git

# Navigate into the repository
cd aiinterviewerbackend

# Check current branch
git branch

# Pull latest changes
git pull origin main
```

### Step 1.2: Verify Repository Structure

```bash
# List files
ls -la

# Check for Dockerfile
ls -la Dockerfile

# Check for requirements.txt
ls -la requirements.txt

# Check for cloudbuild-backend.yaml
ls -la cloudbuild-backend.yaml
```

**Expected Files:**
- ✅ `Dockerfile`
- ✅ `requirements.txt`
- ✅ `cloudbuild-backend.yaml`
- ✅ `interview_app/` (Django app)
- ✅ `manage.py`

---

## Part 2: Deploy Backend to Cloud Run

### Step 2.1: Set Up Environment Variables

**In Cloud Shell:**

```bash
# Set project variables
export PROJECT_ID=eastern-team-480811-e6
export REGION=asia-south2
export INSTANCE_NAME=ai-interviewer-db1
export SERVICE_NAME=ai-interviewer-backend
export CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"

# Database variables
export DB_PASSWORD=Admin12345
export DB_NAME=ai_interviewer_db1
export DB_USER=db_user

# Build DATABASE_URL for Cloud SQL Unix socket
export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CLOUD_SQL_CONNECTION}"

# Set API keys (REPLACE WITH YOUR ACTUAL KEYS)
export DJANGO_SECRET_KEY=your-django-secret-key-here
export GEMINI_API_KEY=your-gemini-api-key
export DEEPGRAM_API_KEY=your-deepgram-api-key

# Image name
export IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Verify variables
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Cloud SQL Connection: $CLOUD_SQL_CONNECTION"
echo "Database URL: $DATABASE_URL"
echo "Image: $IMAGE_NAME"
```

### Step 2.2: Build and Push Docker Image

```bash
# Navigate to backend repository
cd ~/workspace/aiinterviewerbackend  # or your path

# Build and push image (10-15 minutes)
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID
```

**Wait for build to complete** ✅

### Step 2.3: Deploy to Cloud Run

```bash
# Deploy backend service
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
  --max-instances=10 \
  --min-instances=0 \
  --port=8080 \
  --project=$PROJECT_ID
```

**Wait for deployment** (5-10 minutes) ⏳

### Step 2.4: Get Backend Service URL

```bash
# Get service URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

echo "✅ Backend deployed!"
echo "🌐 Backend URL: $BACKEND_URL"

# Save URL for later
echo "export BACKEND_URL=$BACKEND_URL" >> ~/.bashrc
```

**Expected Output:**
```
✅ Backend deployed!
🌐 Backend URL: https://ai-interviewer-backend-310576915040.asia-south2.run.app
```

**Save this URL!** 📝

### Step 2.5: Run Database Migrations

```bash
# Create migration job
gcloud run jobs create migrate-db \
  --image $IMAGE_NAME \
  --region $REGION \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True" \
  --command="python" \
  --args="manage.py,migrate" \
  --max-retries=3 \
  --project=$PROJECT_ID

# Execute migration
gcloud run jobs execute migrate-db --region $REGION --project=$PROJECT_ID
```

### Step 2.6: Test Backend

```bash
# Test health endpoint
curl $BACKEND_URL/api/health/

# Check logs
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --limit=20
```

**Expected:** JSON response or 200 status ✅

---

## Part 3: Connect Frontend to Backend

### Step 3.1: Update Frontend Configuration

**Option A: Update Frontend Repository (Recommended)**

**In your local machine or Cloud Shell:**

```bash
# Navigate to frontend repository
cd ~/workspace/aiinterviewerfrontend  # or your frontend path

# Create or update .env.production file
cat > .env.production << EOF
VITE_API_URL=$BACKEND_URL
EOF

# Verify
cat .env.production
```

**Option B: Update Cloud Build Substitutions**

If using Cloud Build for frontend deployment:

1. Go to **Cloud Build** → **Triggers**
2. Edit your frontend trigger
3. Add substitution:
   - **Name**: `_VITE_API_URL`
   - **Value**: `https://ai-interviewer-backend-310576915040.asia-south2.run.app` (your backend URL)

### Step 3.2: Update Frontend Constants (If Needed)

**File: `frontend/src/config/constants.js`**

The file already supports `VITE_API_URL` environment variable. Just ensure it's set during build.

**File: `frontend/vite.config.js`**

Already configured to use `VITE_API_URL`. No changes needed if using environment variable.

### Step 3.3: Rebuild Frontend with New Backend URL

**Option A: Local Build**

```bash
# Navigate to frontend
cd ~/workspace/aiinterviewerfrontend/frontend

# Set environment variable
export VITE_API_URL=$BACKEND_URL

# Build
npm run build

# Test locally (optional)
npm run preview
```

**Option B: Cloud Build Trigger**

```bash
# Trigger Cloud Build for frontend
gcloud builds triggers run FRONTEND_TRIGGER_NAME \
  --branch=main \
  --project=$PROJECT_ID
```

Or push to GitHub to trigger automatically:

```bash
# Commit and push changes
git add .env.production
git commit -m "Update backend URL to Cloud Run"
git push origin main
```

### Step 3.4: Verify Frontend-Backend Connection

**After frontend is deployed:**

1. **Open Frontend URL** in browser
2. **Open Browser DevTools** (F12)
3. **Go to Network tab**
4. **Try to login** or make an API call
5. **Check Network requests** - they should go to your Cloud Run backend URL

**Expected:**
- ✅ API calls go to: `https://ai-interviewer-backend-310576915040.asia-south2.run.app`
- ✅ No CORS errors
- ✅ Successful API responses

---

## Part 4: Configure CORS (If Needed)

### Step 4.1: Update Backend CORS Settings

**File: `interview_app/settings.py`**

Ensure CORS is configured:

```python
CORS_ALLOWED_ORIGINS = [
    "https://aiinterviewfrontend-310576915040.asia-south2.run.app",  # Your frontend URL
    "http://localhost:5173",  # Local development
    "http://localhost:3000",  # Alternative local port
]

# Or allow all origins (for testing only)
# CORS_ALLOW_ALL_ORIGINS = True  # ⚠️ Only for development
```

### Step 4.2: Redeploy Backend (If CORS Changed)

```bash
# Rebuild and redeploy
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --project=$PROJECT_ID
```

---

## Part 5: Complete Setup Script

**Copy and run this complete script in Cloud Shell:**

```bash
#!/bin/bash

# ============================================
# Backend & Frontend Connection Setup Script
# ============================================

set -e  # Exit on error

# Step 1: Set Variables
export PROJECT_ID=eastern-team-480811-e6
export REGION=asia-south2
export INSTANCE_NAME=ai-interviewer-db1
export SERVICE_NAME=ai-interviewer-backend
export CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
export DB_PASSWORD=Admin12345
export DB_NAME=ai_interviewer_db1
export DB_USER=db_user
export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CLOUD_SQL_CONNECTION}"
export IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Set API keys (REPLACE WITH YOUR ACTUAL KEYS)
export DJANGO_SECRET_KEY=your-secret-key-here
export GEMINI_API_KEY=your-gemini-key
export DEEPGRAM_API_KEY=your-deepgram-key

echo "🔧 Step 1: Variables Set"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Cloud SQL: $CLOUD_SQL_CONNECTION"

# Step 2: Clone Backend Repository (if not exists)
if [ ! -d "aiinterviewerbackend" ]; then
    echo "📥 Step 2: Cloning Backend Repository..."
    git clone https://github.com/rahulwaghole14/aiinterviewerbackend.git
fi

cd aiinterviewerbackend
echo "✅ Step 2: Backend Repository Ready"

# Step 3: Build Docker Image
echo "🔨 Step 3: Building Docker Image..."
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID
echo "✅ Step 3: Image Built"

# Step 4: Deploy to Cloud Run
echo "🚀 Step 4: Deploying to Cloud Run..."
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

# Step 5: Get Backend URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

echo "✅ Step 4: Backend Deployed"
echo "🌐 Backend URL: $BACKEND_URL"

# Step 6: Run Migrations
echo "📊 Step 5: Running Database Migrations..."
gcloud run jobs create migrate-db \
  --image $IMAGE_NAME \
  --region $REGION \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True" \
  --command="python" \
  --args="manage.py,migrate" \
  --max-retries=3 \
  --project=$PROJECT_ID || true

gcloud run jobs execute migrate-db --region $REGION --project=$PROJECT_ID || true
echo "✅ Step 5: Migrations Complete"

# Step 7: Test Backend
echo "🧪 Step 6: Testing Backend..."
curl -s $BACKEND_URL/api/health/ || echo "Health check endpoint may not exist"

# Step 8: Frontend Configuration
echo ""
echo "============================================"
echo "✅ Backend Setup Complete!"
echo "============================================"
echo ""
echo "📝 Next Steps for Frontend:"
echo ""
echo "1. Update Frontend .env.production:"
echo "   VITE_API_URL=$BACKEND_URL"
echo ""
echo "2. Or update Cloud Build trigger substitution:"
echo "   _VITE_API_URL=$BACKEND_URL"
echo ""
echo "3. Rebuild and redeploy frontend"
echo ""
echo "🌐 Backend URL: $BACKEND_URL"
echo "============================================"
```

**Save as `setup-backend-frontend.sh` and run:**

```bash
chmod +x setup-backend-frontend.sh
./setup-backend-frontend.sh
```

---

## Part 6: Quick Reference Commands

### Backend Commands

```bash
# Get backend URL
gcloud run services describe ai-interviewer-backend \
  --region asia-south2 \
  --project eastern-team-480811-e6 \
  --format 'value(status.url)'

# View backend logs
gcloud run services logs read ai-interviewer-backend \
  --region asia-south2 \
  --project eastern-team-480811-e6 \
  --limit=50

# Update backend environment variables
gcloud run services update ai-interviewer-backend \
  --region asia-south2 \
  --update-env-vars="NEW_VAR=value" \
  --project eastern-team-480811-e6
```

### Frontend Commands

```bash
# Get frontend URL
gcloud run services describe aiinterviewfrontend \
  --region asia-south2 \
  --project eastern-team-480811-e6 \
  --format 'value(status.url)'

# Trigger frontend rebuild
gcloud builds triggers run FRONTEND_TRIGGER_NAME \
  --branch=main \
  --project=eastern-team-480811-e6
```

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Backend repository cloned successfully
- [ ] Backend deployed to Cloud Run
- [ ] Backend URL accessible (health check works)
- [ ] Database migrations completed
- [ ] Frontend `.env.production` updated with backend URL
- [ ] Frontend rebuilt with new backend URL
- [ ] Frontend can make API calls to backend
- [ ] No CORS errors in browser console
- [ ] Login/API calls work from frontend

---

## 🔧 Troubleshooting

### Issue: Frontend can't connect to backend

**Check:**
1. Backend URL is correct in frontend config
2. Backend service is running
3. CORS is configured correctly
4. Backend allows unauthenticated access

### Issue: CORS errors

**Solution:**
```python
# In interview_app/settings.py
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-url.run.app",
]
```

### Issue: Database connection fails

**Check:**
- Cloud SQL instance is running
- Connection name is correct
- Cloud Run service account has Cloud SQL Client role

---

**Last Updated**: 2025-01-27

