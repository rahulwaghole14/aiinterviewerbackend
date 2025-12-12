# 🚀 Backend Deployment to Cloud Run with Cloud SQL

Complete guide to deploy Django backend to Google Cloud Run with Cloud SQL PostgreSQL database.

---

## 📋 Prerequisites

- [ ] Google Cloud Project with billing enabled
- [ ] Cloud SQL API enabled
- [ ] Cloud Run API enabled
- [ ] Cloud Build API enabled
- [ ] gcloud CLI installed and authenticated

---

## Step 1: Create Cloud SQL PostgreSQL Instance

### 1.1 Create Instance via Console

1. Go to [Cloud SQL Console](https://console.cloud.google.com/sql)
2. Click **"Create Instance"**
3. Choose **PostgreSQL**
4. Fill in details:
   - **Instance ID**: `ai-interviewer-db`
   - **Password**: Set a strong password (save it!)
   - **Region**: `asia-south2` (or your preferred region)
   - **Database version**: PostgreSQL 15
   - **Machine type**: `db-f1-micro` (for testing) or `db-n1-standard-1` (production)
5. Click **"Create"**

### 1.2 Create Instance via CLI

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

### 1.3 Create Database

```bash
# Create database
gcloud sql databases create ai_interviewer_db \
  --instance=$INSTANCE_NAME \
  --project=$PROJECT_ID
```

### 1.4 Create Database User

```bash
# Create user
gcloud sql users create db_user \
  --instance=$INSTANCE_NAME \
  --password=$DB_PASSWORD \
  --project=$PROJECT_ID
```

---

## Step 2: Get Cloud SQL Connection Name

```bash
# Get connection name
gcloud sql instances describe $INSTANCE_NAME \
  --project=$PROJECT_ID \
  --format="value(connectionName)"
```

**Format**: `PROJECT_ID:REGION:INSTANCE_NAME`

**Example**: `eastern-team-480811-e6:asia-south2:ai-interviewer-db`

---

## Step 3: Update Django Settings for Cloud SQL

The settings.py already supports Cloud SQL via Unix socket. The DATABASE_URL format for Cloud SQL is:

```
postgresql://USER:PASSWORD@/DATABASE_NAME?host=/cloudsql/CONNECTION_NAME
```

**Example**:
```
postgresql://db_user:password@/ai_interviewer_db?host=/cloudsql/eastern-team-480811-e6:asia-south2:ai-interviewer-db
```

---

## Step 4: Build and Push Docker Image

### 4.1 Build Image

```bash
# Set variables
export PROJECT_ID=eastern-team-480811-e6
export SERVICE_NAME=ai-interviewer-backend
export IMAGE_NAME=gcr.io/$PROJECT_ID/$SERVICE_NAME

# Build image
gcloud builds submit --tag $IMAGE_NAME
```

### 4.2 Deploy to Cloud Run

```bash
# Set variables
export REGION=asia-south2
export CLOUD_SQL_CONNECTION=eastern-team-480811-e6:asia-south2:ai-interviewer-db
export DB_PASSWORD=your-db-password
export DJANGO_SECRET_KEY=your-secret-key
export GEMINI_API_KEY=your-gemini-key
export DEEPGRAM_API_KEY=your-deepgram-key

# Build DATABASE_URL for Cloud SQL
export DATABASE_URL="postgresql://db_user:${DB_PASSWORD}@/ai_interviewer_db?host=/cloudsql/${CLOUD_SQL_CONNECTION}"

# Deploy
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY},DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True,GEMINI_API_KEY=${GEMINI_API_KEY},DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY},DJANGO_DEBUG=False" \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --max-instances=10 \
  --min-instances=0 \
  --port=8080
```

---

## Step 5: Run Database Migrations

### 5.1 Via Cloud Run Job

```bash
# Create migration job
gcloud run jobs create migrate-db \
  --image $IMAGE_NAME \
  --region $REGION \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True" \
  --command="python" \
  --args="manage.py,migrate" \
  --max-retries=3

# Execute migration
gcloud run jobs execute migrate-db --region $REGION
```

### 5.2 Via Cloud Run Service (One-time)

```bash
# Temporarily update service to run migrations
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --command="sh" \
  --args="-c,python manage.py migrate && gunicorn interview_app.wsgi:application --bind 0.0.0.0:\$PORT --workers 2"
```

---

## Step 6: Automated Deployment with Cloud Build

### 6.1 Create Cloud Build Trigger

1. Go to [Cloud Build Console](https://console.cloud.google.com/cloud-build)
2. Click **"Triggers"** → **"Create Trigger"**
3. Connect your GitHub repository
4. Configure trigger:
   - **Name**: `deploy-backend`
   - **Event**: Push to branch `main`
   - **Configuration**: Cloud Build configuration file
   - **Location**: `cloudbuild-backend.yaml`

### 6.2 Add Substitutions

In trigger settings, add these substitutions:

| Variable | Value | Description |
|----------|-------|-------------|
| `_SERVICE_NAME` | `ai-interviewer-backend` | Cloud Run service name |
| `_REGION` | `asia-south2` | Deployment region |
| `_CLOUD_SQL_CONNECTION_NAME` | `eastern-team-480811-e6:asia-south2:ai-interviewer-db` | Cloud SQL connection |
| `_DJANGO_SECRET_KEY` | `your-secret-key` | Django secret key |
| `_DATABASE_URL` | `postgresql://db_user:password@/ai_interviewer_db?host=/cloudsql/eastern-team-480811-e6:asia-south2:ai-interviewer-db` | Database URL |
| `_GEMINI_API_KEY` | `your-key` | Gemini API key |
| `_DEEPGRAM_API_KEY` | `your-key` | Deepgram API key |
| `_BACKEND_URL` | `https://ai-interviewer-backend-PROJECT_NUMBER.asia-south2.run.app` | Backend URL |

**⚠️ Use Secrets Manager for sensitive values!**

### 6.3 Grant Permissions

```bash
# Grant Cloud Build service account permissions
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Cloud Run Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

# Service Account User (to deploy)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

---

## Step 7: Using Secrets Manager (Recommended)

### 7.1 Create Secrets

```bash
# Create secrets
echo -n "your-secret-key" | gcloud secrets create django-secret-key --data-file=-
echo -n "your-db-password" | gcloud secrets create db-password --data-file=-
echo -n "your-gemini-key" | gcloud secrets create gemini-api-key --data-file=-
echo -n "your-deepgram-key" | gcloud secrets create deepgram-api-key --data-file=-
```

### 7.2 Grant Access

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Grant Cloud Build access
gcloud secrets add-iam-policy-binding django-secret-key \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding django-secret-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 7.3 Update cloudbuild.yaml to Use Secrets

Update the deploy step to use secrets:

```yaml
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
  entrypoint: 'gcloud'
  args:
    - 'run'
    - 'deploy'
    - '${_SERVICE_NAME}'
    - '--update-secrets'
    - 'DJANGO_SECRET_KEY=django-secret-key:latest,DATABASE_URL=db-url-secret:latest'
```

---

## Step 8: Verify Deployment

### 8.1 Check Service Status

```bash
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)'
```

### 8.2 Test API

```bash
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)')

curl $BACKEND_URL/api/health/
```

### 8.3 Check Logs

```bash
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --limit=50
```

---

## 🔧 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@/db?host=/cloudsql/...` |
| `USE_POSTGRESQL` | Enable PostgreSQL | `True` |
| `DJANGO_DEBUG` | Debug mode | `False` |

### Optional Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `DEEPGRAM_API_KEY` | Deepgram API key |
| `BACKEND_URL` | Backend service URL |
| `EMAIL_HOST` | SMTP host |
| `EMAIL_PORT` | SMTP port |
| `EMAIL_HOST_USER` | SMTP user |
| `EMAIL_HOST_PASSWORD` | SMTP password |

---

## 🐛 Troubleshooting

### Issue: "Cloud SQL connection failed"

**Solution**:
1. Verify Cloud SQL instance is running
2. Check connection name format: `PROJECT_ID:REGION:INSTANCE_NAME`
3. Ensure `--add-cloudsql-instances` is set correctly
4. Verify database user and password

### Issue: "Migration failed"

**Solution**:
1. Run migrations via Cloud Run job
2. Check database permissions
3. Verify DATABASE_URL format

### Issue: "Container failed to start"

**Solution**:
1. Check Cloud Run logs
2. Verify environment variables
3. Check database connection
4. Increase startup timeout if needed

### Issue: "Permission denied"

**Solution**:
1. Grant Cloud Build service account permissions
2. Grant Cloud Run service account Cloud SQL access
3. Check IAM roles

---

## 📝 Quick Deployment Commands

### Full Deployment Script

```bash
#!/bin/bash
set -e

# Set variables
export PROJECT_ID=eastern-team-480811-e6
export SERVICE_NAME=ai-interviewer-backend
export REGION=asia-south2
export INSTANCE_NAME=ai-interviewer-db
export CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
export IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Build and push
gcloud builds submit --tag $IMAGE_NAME

# Deploy
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="USE_POSTGRESQL=True,DJANGO_DEBUG=False" \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --port=8080

# Run migrations
gcloud run jobs create migrate-db \
  --image $IMAGE_NAME \
  --region $REGION \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=...,USE_POSTGRESQL=True" \
  --command="python" \
  --args="manage.py,migrate"

gcloud run jobs execute migrate-db --region $REGION
```

---

## ✅ Success Checklist

After deployment:

- [ ] Cloud Run service is running
- [ ] Service URL is accessible
- [ ] Database connection works
- [ ] Migrations completed successfully
- [ ] API endpoints respond correctly
- [ ] Logs show no errors

---

**Last Updated**: 2025-01-27

