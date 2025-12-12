# ✅ Backend GitHub to Cloud Run Setup Checklist

Quick checklist for setting up automated backend deployment from GitHub to Cloud Run with Cloud SQL.

**Repository**: https://github.com/rahulwaghole14/aiinterviewerbackend.git

---

## 📋 Pre-Setup Checklist

- [ ] Google Cloud Project created
- [ ] Billing enabled
- [ ] gcloud CLI installed (or use Cloud Console)
- [ ] GitHub repository exists: `rahulwaghole14/aiinterviewerbackend`

---

## Step 1: Enable Required APIs

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  sql-component.googleapis.com \
  --project=eastern-team-480811-e6
```

Or enable via [Cloud Console](https://console.cloud.google.com/apis/library)

---

## Step 2: Create Cloud SQL Instance

### Via Console:
1. Go to [Cloud SQL](https://console.cloud.google.com/sql)
2. Create Instance → PostgreSQL
3. Instance ID: `ai-interviewer-db`
4. Region: `asia-south2`
5. Set root password
6. Create

### Via CLI:
```bash
gcloud sql instances create ai-interviewer-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-south2 \
  --root-password=YOUR_PASSWORD \
  --project=eastern-team-480811-e6
```

### Create Database:
```bash
gcloud sql databases create ai_interviewer_db \
  --instance=ai-interviewer-db \
  --project=eastern-team-480811-e6
```

### Create User:
```bash
gcloud sql users create db_user \
  --instance=ai-interviewer-db \
  --password=YOUR_PASSWORD \
  --project=eastern-team-480811-e6
```

### Get Connection Name:
```bash
gcloud sql instances describe ai-interviewer-db \
  --format="value(connectionName)" \
  --project=eastern-team-480811-e6
```

**Save this connection name!** Format: `PROJECT_ID:REGION:INSTANCE_NAME`

---

## Step 3: Connect GitHub to Cloud Build

### 3.1 Install GitHub App
- [ ] Go to [Cloud Build Console](https://console.cloud.google.com/cloud-build)
- [ ] Click **"Triggers"** → **"Connect Repository"**
- [ ] Select **"GitHub (Cloud Build GitHub App)"**
- [ ] Install GitHub App
- [ ] Select repository: `rahulwaghole14/aiinterviewerbackend`
- [ ] Authorize connection

### 3.2 Verify Connection
- [ ] Repository appears in Cloud Build
- [ ] Can see repository files

---

## Step 4: Create Cloud Build Trigger

### 4.1 Basic Configuration
- [ ] Name: `deploy-backend-cloudrun`
- [ ] Event: **Push to a branch**
- [ ] Branch: `^main$`
- [ ] Source: `rahulwaghole14/aiinterviewerbackend`
- [ ] Config: **Cloud Build configuration file**
- [ ] Location: `cloudbuild-backend.yaml`

### 4.2 Substitutions (Add These)
- [ ] `_SERVICE_NAME` = `ai-interviewer-backend`
- [ ] `_REGION` = `asia-south2`
- [ ] `_CLOUD_SQL_CONNECTION_NAME` = `eastern-team-480811-e6:asia-south2:ai-interviewer-db`
- [ ] `_DJANGO_SECRET_KEY` = `your-secret-key`
- [ ] `_DATABASE_URL` = `postgresql://db_user:PASSWORD@/ai_interviewer_db?host=/cloudsql/eastern-team-480811-e6:asia-south2:ai-interviewer-db`
- [ ] `_GEMINI_API_KEY` = `your-gemini-key`
- [ ] `_DEEPGRAM_API_KEY` = `your-deepgram-key`
- [ ] `_BACKEND_URL` = `https://ai-interviewer-backend-PROJECT_NUMBER.asia-south2.run.app`

**⚠️ Replace PASSWORD in _DATABASE_URL with actual password!**

### 4.3 Create Trigger
- [ ] Click **"Create"**
- [ ] Trigger appears in list

---

## Step 5: Grant Permissions

### 5.1 Get Project Number
```bash
gcloud projects describe eastern-team-480811-e6 --format="value(projectNumber)"
```

### 5.2 Grant Cloud Build Permissions
```bash
PROJECT_ID=eastern-team-480811-e6
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Cloud Run Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

# Service Account User
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Cloud SQL Client
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

### 5.3 Grant Cloud Run Cloud SQL Access
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

---

## Step 6: Verify Files in Repository

Check that these files exist in the repository:

- [ ] `Dockerfile` (root directory)
- [ ] `cloudbuild-backend.yaml` (root directory)
- [ ] `requirements.txt` (root directory)
- [ ] `manage.py` (root directory)
- [ ] `interview_app/settings.py` (with Cloud SQL support)

---

## Step 7: Test Deployment

### 7.1 Trigger Build
```bash
# Make a small change and push
echo "# Test" >> README.md
git add README.md
git commit -m "Test Cloud Build deployment"
git push origin main
```

### 7.2 Monitor Build
- [ ] Go to Cloud Build Console → History
- [ ] See build running
- [ ] Build completes successfully (15-20 minutes)
- [ ] No errors in logs

### 7.3 Verify Service
- [ ] Go to Cloud Run Console
- [ ] Service `ai-interviewer-backend` exists
- [ ] Service is running
- [ ] Get service URL
- [ ] Test: `curl https://SERVICE_URL/api/health/`

---

## Step 8: Run Database Migrations

### 8.1 Create Migration Job
```bash
PROJECT_ID=eastern-team-480811-e6
SERVICE_NAME=ai-interviewer-backend
REGION=asia-south2
INSTANCE_NAME=ai-interviewer-db
CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
DB_PASSWORD=your-password
DATABASE_URL="postgresql://db_user:${DB_PASSWORD}@/ai_interviewer_db?host=/cloudsql/${CLOUD_SQL_CONNECTION}"

gcloud run jobs create migrate-db \
  --image $IMAGE_NAME \
  --region $REGION \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True" \
  --command="python" \
  --args="manage.py,migrate" \
  --project $PROJECT_ID
```

### 8.2 Execute Migration
```bash
gcloud run jobs execute migrate-db --region $REGION --project $PROJECT_ID
```

### 8.3 Verify
- [ ] Migration job completes successfully
- [ ] Check job logs for errors
- [ ] Database tables created

---

## Step 9: Allow Unauthenticated Access

### Via Console:
1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click service: `ai-interviewer-backend`
3. Click **"Permissions"** tab
4. Click **"Add Principal"**
5. Principal: `allUsers`
6. Role: **"Cloud Run Invoker"**
7. Save

### Via CLI:
```bash
gcloud run services add-iam-policy-binding ai-interviewer-backend \
  --region=asia-south2 \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --project=eastern-team-480811-e6
```

---

## ✅ Final Verification

- [ ] Service URL is accessible
- [ ] API endpoints respond
- [ ] Database connection works
- [ ] Migrations completed
- [ ] No errors in logs
- [ ] Frontend can connect to backend

---

## 🔄 Future Updates

After initial setup, just push to GitHub:

```bash
git add .
git commit -m "Update backend"
git push origin main
```

Cloud Build will automatically:
1. Build new Docker image
2. Deploy to Cloud Run
3. Update service

---

## 📚 Documentation

- **Complete Guide**: `BACKEND_GITHUB_CLOUD_RUN_DEPLOYMENT.md`
- **Quick Deploy**: `QUICK_BACKEND_DEPLOY.md`
- **Full Guide**: `BACKEND_CLOUD_RUN_DEPLOYMENT.md`

---

**Last Updated**: 2025-01-27

