# 🚀 Deploy Backend from GitHub to Cloud Run with Cloud SQL

Complete guide to deploy Django backend from GitHub repository to Google Cloud Run with Cloud SQL database connection.

**Repository**: https://github.com/rahulwaghole14/aiinterviewerbackend.git

---

## 📋 Prerequisites

- [ ] Google Cloud Project with billing enabled
- [ ] Cloud SQL API enabled
- [ ] Cloud Run API enabled
- [ ] Cloud Build API enabled
- [ ] GitHub repository: `rahulwaghole14/aiinterviewerbackend`

---

## Step 1: Create Cloud SQL PostgreSQL Instance

### 1.1 Create Instance

```bash
# Set variables
export PROJECT_ID=eastern-team-480811-e6
export INSTANCE_NAME=ai-interviewer-db
export REGION=asia-south2
export DB_PASSWORD=your-strong-password-here

# Create Cloud SQL instance
gcloud sql instances create $INSTANCE_NAME \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --root-password=$DB_PASSWORD \
  --project=$PROJECT_ID
```

### 1.2 Create Database

```bash
gcloud sql databases create ai_interviewer_db \
  --instance=$INSTANCE_NAME \
  --project=$PROJECT_ID
```

### 1.3 Create Database User

```bash
gcloud sql users create db_user \
  --instance=$INSTANCE_NAME \
  --password=$DB_PASSWORD \
  --project=$PROJECT_ID
```

### 1.4 Get Connection Name

```bash
CLOUD_SQL_CONNECTION=$(gcloud sql instances describe $INSTANCE_NAME \
  --project=$PROJECT_ID \
  --format="value(connectionName)")

echo "Cloud SQL Connection: $CLOUD_SQL_CONNECTION"
# Output: PROJECT_ID:REGION:INSTANCE_NAME
# Example: eastern-team-480811-e6:asia-south2:ai-interviewer-db
```

---

## Step 2: Connect GitHub Repository to Cloud Build

### 2.1 Install GitHub App

1. Go to [Cloud Build Console](https://console.cloud.google.com/cloud-build)
2. Click **"Triggers"** → **"Connect Repository"**
3. Select **"GitHub (Cloud Build GitHub App)"**
4. Click **"Install GitHub App"**
5. Select your GitHub account
6. Choose repository: **`rahulwaghole14/aiinterviewerbackend`**
7. Click **"Install"**

### 2.2 Authorize Connection

1. After installation, you'll be redirected back to GCP
2. Select your GitHub account
3. Select repository: **`aiinterviewerbackend`**
4. Click **"Connect"**

---

## Step 3: Create Cloud Build Trigger

### 3.1 Create Trigger

1. In Cloud Build Console, click **"Create Trigger"**
2. Fill in details:

   **Name**: `deploy-backend-cloudrun`
   
   **Event**: **Push to a branch**
   
   **Source**: Select `rahulwaghole14/aiinterviewerbackend`
   
   **Branch**: `^main$` (or your main branch)
   
   **Configuration**: **Cloud Build configuration file (yaml or json)**
   
   **Location**: `cloudbuild-backend.yaml`

### 3.2 Add Substitutions

Click **"Substitution variables"** → **"Add variable"** for each:

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `_SERVICE_NAME` | `ai-interviewer-backend` | Cloud Run service name |
| `_REGION` | `asia-south2` | Deployment region |
| `_CLOUD_SQL_CONNECTION_NAME` | `eastern-team-480811-e6:asia-south2:ai-interviewer-db` | Cloud SQL connection |
| `_DJANGO_SECRET_KEY` | `your-secret-key` | Django secret key |
| `_DATABASE_URL` | `postgresql://db_user:PASSWORD@/ai_interviewer_db?host=/cloudsql/eastern-team-480811-e6:asia-south2:ai-interviewer-db` | Database URL |
| `_GEMINI_API_KEY` | `your-gemini-key` | Gemini API key |
| `_DEEPGRAM_API_KEY` | `your-deepgram-key` | Deepgram API key |
| `_BACKEND_URL` | `https://ai-interviewer-backend-PROJECT_NUMBER.asia-south2.run.app` | Backend URL (auto-updated) |

**⚠️ Important**: Replace `PASSWORD` in `_DATABASE_URL` with your actual database password!

### 3.3 Advanced Settings

- **Service account**: Leave default
- **Timeout**: `1200s` (20 minutes)
- **Machine type**: `E2_HIGHCPU_8`

### 3.4 Create Trigger

Click **"Create"** button.

---

## Step 4: Grant Cloud Build Permissions

### 4.1 Get Project Number

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
echo "Project Number: $PROJECT_NUMBER"
```

### 4.2 Grant Required Roles

```bash
# Cloud Run Admin (to deploy services)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

# Service Account User (to use service accounts)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Cloud SQL Client (to connect to Cloud SQL)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

### 4.3 Grant Cloud Run Service Account Cloud SQL Access

```bash
# Grant Cloud Run service account access to Cloud SQL
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

---

## Step 5: Verify cloudbuild-backend.yaml Exists

Ensure `cloudbuild-backend.yaml` exists in your repository root:

```bash
# Check if file exists
ls cloudbuild-backend.yaml
```

The file should be at the root of the repository.

---

## Step 6: Test the Trigger

### 6.1 Make a Small Change

```bash
# Clone repository (if not already)
git clone https://github.com/rahulwaghole14/aiinterviewerbackend.git
cd aiinterviewerbackend

# Make a small change
echo "# Test deployment" >> README.md
git add README.md
git commit -m "Test Cloud Build trigger"
git push origin main
```

### 6.2 Monitor Build

1. Go to [Cloud Build Console](https://console.cloud.google.com/cloud-build)
2. Click **"History"**
3. You should see a new build running
4. Click on the build to see logs in real-time

### 6.3 Verify Deployment

After build completes (15-20 minutes):
- Check build logs for success
- Go to [Cloud Run Console](https://console.cloud.google.com/run)
- Verify service `ai-interviewer-backend` is running
- Get service URL and test: `curl https://SERVICE_URL/api/health/`

---

## Step 7: Run Database Migrations

### 7.1 Create Migration Job

```bash
# Set variables
export PROJECT_ID=eastern-team-480811-e6
export SERVICE_NAME=ai-interviewer-backend
export REGION=asia-south2
export INSTANCE_NAME=ai-interviewer-db
export CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
export IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
export DB_PASSWORD=your-password
export DATABASE_URL="postgresql://db_user:${DB_PASSWORD}@/ai_interviewer_db?host=/cloudsql/${CLOUD_SQL_CONNECTION}"

# Create migration job
gcloud run jobs create migrate-db \
  --image $IMAGE_NAME \
  --region $REGION \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True" \
  --command="python" \
  --args="manage.py,migrate" \
  --max-retries=3 \
  --project $PROJECT_ID
```

### 7.2 Execute Migration

```bash
gcloud run jobs execute migrate-db --region $REGION --project $PROJECT_ID
```

### 7.3 Verify Migrations

```bash
# Check job logs
gcloud run jobs executions list --job=migrate-db --region $REGION --project $PROJECT_ID
```

---

## Step 8: Using Secrets Manager (Recommended for Production)

### 8.1 Create Secrets

```bash
# Create secrets
echo -n "your-secret-key" | gcloud secrets create django-secret-key --data-file=- --project=$PROJECT_ID
echo -n "your-db-password" | gcloud secrets create db-password --data-file=- --project=$PROJECT_ID
echo -n "your-gemini-key" | gcloud secrets create gemini-api-key --data-file=- --project=$PROJECT_ID
echo -n "your-deepgram-key" | gcloud secrets create deepgram-api-key --data-file=- --project=$PROJECT_ID
```

### 8.2 Grant Access

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Grant Cloud Build access
gcloud secrets add-iam-policy-binding django-secret-key \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding django-secret-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID
```

### 8.3 Update cloudbuild-backend.yaml to Use Secrets

Update the deploy step in `cloudbuild-backend.yaml`:

```yaml
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
  entrypoint: 'gcloud'
  args:
    - 'run'
    - 'deploy'
    - '${_SERVICE_NAME}'
    - '--update-secrets'
    - 'DJANGO_SECRET_KEY=django-secret-key:latest,GEMINI_API_KEY=gemini-api-key:latest,DEEPGRAM_API_KEY=deepgram-api-key:latest'
    - '--set-env-vars'
    - 'DATABASE_URL=${_DATABASE_URL},USE_POSTGRESQL=True,DJANGO_DEBUG=False'
```

---

## 🔄 Automated Deployment Workflow

### How It Works

```
GitHub Push → Cloud Build Trigger → Build Docker Image → Push to Registry → Deploy to Cloud Run → Service Live
```

### Typical Workflow

1. **Developer pushes code**:
   ```bash
   git add .
   git commit -m "Update backend"
   git push origin main
   ```

2. **Cloud Build automatically**:
   - Detects push to `main` branch
   - Starts build using `cloudbuild-backend.yaml`
   - Builds Docker image
   - Pushes to Container Registry
   - Deploys to Cloud Run
   - Connects to Cloud SQL

3. **Service is live** at Cloud Run URL

---

## 📝 Configuration Files

### Required Files in Repository

```
aiinterviewerbackend/
├── Dockerfile                    ← Must exist
├── cloudbuild-backend.yaml       ← Must exist
├── requirements.txt              ← Must exist
├── manage.py                     ← Must exist
└── interview_app/
    └── settings.py               ← Database configuration
```

### Dockerfile Location

The `Dockerfile` should be in the **root** of the repository.

### cloudbuild-backend.yaml Location

The `cloudbuild-backend.yaml` should be in the **root** of the repository.

---

## 🔐 Environment Variables Setup

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Cloud SQL connection string | `postgresql://user:pass@/db?host=/cloudsql/...` |
| `USE_POSTGRESQL` | Enable PostgreSQL | `True` |
| `DJANGO_SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DJANGO_DEBUG` | Debug mode | `False` |

### DATABASE_URL Format for Cloud SQL

```
postgresql://USER:PASSWORD@/DATABASE_NAME?host=/cloudsql/CONNECTION_NAME
```

**Example**:
```
postgresql://db_user:password123@/ai_interviewer_db?host=/cloudsql/eastern-team-480811-e6:asia-south2:ai-interviewer-db
```

---

## 🐛 Troubleshooting

### Issue: Trigger Not Firing

**Solution**:
1. Check branch name matches trigger pattern
2. Verify repository is connected
3. Check Cloud Build API is enabled
4. Review trigger logs

### Issue: Build Fails - "Permission Denied"

**Solution**:
```bash
# Grant required permissions
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### Issue: Cloud SQL Connection Failed

**Solution**:
1. Verify Cloud SQL instance is running
2. Check connection name format: `PROJECT_ID:REGION:INSTANCE_NAME`
3. Ensure `--add-cloudsql-instances` is set correctly
4. Grant Cloud Run service account Cloud SQL access:
   ```bash
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
     --role="roles/cloudsql.client"
   ```

### Issue: Migration Failed

**Solution**:
1. Run migrations via Cloud Run job
2. Check database permissions
3. Verify DATABASE_URL format
4. Check Cloud Run job logs

---

## ✅ Verification Checklist

After setup:

- [ ] GitHub repository connected to Cloud Build
- [ ] Trigger created and active
- [ ] Substitutions configured correctly
- [ ] Cloud Build has required permissions
- [ ] Cloud SQL instance created and running
- [ ] Cloud Run service account has Cloud SQL access
- [ ] Test push triggers build successfully
- [ ] Build completes and deploys to Cloud Run
- [ ] Service URL is accessible
- [ ] Database migrations completed
- [ ] API endpoints respond correctly

---

## 📊 Monitoring

### View Build History

```bash
gcloud builds list --limit=10 --project=$PROJECT_ID
```

### View Build Logs

```bash
gcloud builds log BUILD_ID --project=$PROJECT_ID
```

### View Cloud Run Logs

```bash
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --limit=50
```

### View Service Status

```bash
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID
```

---

## 🔄 Update After Code Changes

### Automatic (Recommended)

Just push to `main` branch:
```bash
git add .
git commit -m "Update backend code"
git push origin main
```

Cloud Build will automatically:
- Build new Docker image
- Deploy to Cloud Run
- Update service

### Manual Deployment

```bash
# Build and deploy manually
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION
```

---

## 📚 Related Documentation

- **Complete Guide**: `BACKEND_CLOUD_RUN_DEPLOYMENT.md`
- **Quick Reference**: `QUICK_BACKEND_DEPLOY.md`
- **Deployment Script**: `deploy-backend-cloudrun.sh`

---

## 🆘 Support

For issues:
1. Check Cloud Build logs
2. Check Cloud Run logs
3. Verify permissions and configurations
4. Review `BACKEND_CLOUD_RUN_DEPLOYMENT.md` for detailed troubleshooting

---

**Last Updated**: 2025-01-27

