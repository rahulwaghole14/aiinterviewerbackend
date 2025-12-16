# 🚀 Complete Deployment Guide: Frontend (GCS) + Backend (Vertex AI)

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Frontend Deployment (Google Cloud Storage)](#frontend-deployment-google-cloud-storage)
5. [Backend Deployment (Vertex AI)](#backend-deployment-vertex-ai)
6. [Connecting Frontend and Backend](#connecting-frontend-and-backend)
7. [Environment Variables Setup](#environment-variables-setup)
8. [Post-Deployment Verification](#post-deployment-verification)
9. [Functionality Overview](#functionality-overview)

---

## 📖 Overview

This guide covers deploying:
- **Frontend**: React application deployed to **Google Cloud Storage (GCS)** with Cloud CDN
- **Backend**: Django REST API deployed to **Google Cloud Run** (Vertex AI compatible)

**Note**: Vertex AI is primarily for ML model serving. For Django backend, we'll use **Cloud Run** which is compatible with Vertex AI and provides better Django support.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser                              │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         Google Cloud CDN (Frontend)                         │
│         Serves static files from GCS                        │
└────────────────────┬────────────────────────────────────────┘
                     │ API Calls
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         Cloud Run (Django Backend)                          │
│         - REST API                                           │
│         - WebSocket (Channels)                               │
│         - AI Interview Logic                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │PostgreSQL│ │ Vertex │ │  GCS    │
    │Database │ │   AI   │ │ Storage │
    └────────┘  └────────┘  └────────┘
```

---

## ✅ Prerequisites

### Required Accounts & Tools
1. **Google Cloud Platform (GCP) Account**
   - Enable billing
   - Create a new project or use existing

2. **Required GCP APIs** (Enable via Cloud Console or gcloud CLI):
   ```bash
   gcloud services enable \
     cloudbuild.googleapis.com \
     run.googleapis.com \
     storage-api.googleapis.com \
     storage-component.googleapis.com \
     sql-component.googleapis.com \
     sqladmin.googleapis.com \
     aiplatform.googleapis.com \
     compute.googleapis.com
   ```

3. **Local Tools**:
   - `gcloud CLI` installed and authenticated
   - `docker` installed (for Cloud Run)
   - `node.js` (v18+) and `npm`
   - `python` (3.11+)
   - `git`

### Authentication Setup
```bash
# Login to GCP
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable Application Default Credentials
gcloud auth application-default login
```

---

## 🌐 Frontend Deployment (Google Cloud Storage)

### Step 1: Build Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set backend API URL (replace with your Cloud Run URL after backend deployment)
export VITE_API_URL=https://your-backend-service.run.app

# Build for production
npm run build

# Verify build output
ls -la dist/
```

**Expected Output**: `dist/` folder with `index.html`, `assets/`, etc.

### Step 2: Create GCS Bucket

```bash
# Set variables
export PROJECT_ID=your-project-id
export BUCKET_NAME=ai-interviewer-frontend
export REGION=us-central1

# Create bucket
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME

# Enable static website hosting
gsutil web set -m index.html -e index.html gs://$BUCKET_NAME

# Set bucket permissions (public read for static files)
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
```

### Step 3: Upload Frontend Build to GCS

```bash
# Upload all files from dist/ to bucket root
gsutil -m cp -r dist/* gs://$BUCKET_NAME/

# Set correct content types
gsutil -m setmeta -h "Content-Type:text/html" gs://$BUCKET_NAME/*.html
gsutil -m setmeta -h "Content-Type:application/javascript" gs://$BUCKET_NAME/**/*.js
gsutil -m setmeta -h "Content-Type:text/css" gs://$BUCKET_NAME/**/*.css
```

### Step 4: Setup Cloud CDN (Optional but Recommended)

```bash
# Create backend bucket
gcloud compute backend-buckets create frontend-backend-bucket \
  --gcs-bucket-name=$BUCKET_NAME

# Create URL map
gcloud compute url-maps create frontend-url-map \
  --default-backend-bucket=frontend-backend-bucket

# Create HTTP(S) proxy
gcloud compute target-https-proxies create frontend-https-proxy \
  --url-map=frontend-url-map \
  --ssl-certificates=YOUR_SSL_CERT_NAME

# Create forwarding rule
gcloud compute forwarding-rules create frontend-forwarding-rule \
  --global \
  --target-https-proxy=frontend-https-proxy \
  --ports=443
```

### Step 5: Configure CORS for API Calls

Create `cors.json`:
```json
[
  {
    "origin": ["https://your-frontend-domain.com", "http://localhost:5173"],
    "method": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "responseHeader": ["Content-Type", "Authorization"],
    "maxAgeSeconds": 3600
  }
]
```

Apply CORS:
```bash
gsutil cors set cors.json gs://$BUCKET_NAME
```

### Step 6: Update Frontend API Configuration

Edit `frontend/src/config/constants.js`:
```javascript
const getApiBaseUrl = () => {
  // Production: Use Cloud Run backend URL
  if (import.meta.env.PROD) {
    return 'https://your-backend-service.run.app';
  }
  // Development
  return 'http://127.0.0.1:8000';
};
```

Rebuild and redeploy:
```bash
npm run build
gsutil -m cp -r dist/* gs://$BUCKET_NAME/
```

---

## 🔧 Backend Deployment (Cloud Run / Vertex AI Compatible)

### Step 1: Prepare Backend for Cloud Run

Create `Dockerfile` in project root:
```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port (Cloud Run uses PORT env variable)
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run migrations and start server
CMD python manage.py migrate --noinput && \
    gunicorn interview_app.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --worker-class sync
```

Create `.dockerignore`:
```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
*.db
*.sqlite3
.git
.gitignore
.env
*.md
node_modules/
frontend/
```

### Step 2: Build and Push Docker Image

```bash
# Set variables
export PROJECT_ID=your-project-id
export SERVICE_NAME=ai-interviewer-backend
export REGION=us-central1
export IMAGE_NAME=gcr.io/$PROJECT_ID/$SERVICE_NAME

# Build Docker image
docker build -t $IMAGE_NAME .

# Push to Google Container Registry
docker push $IMAGE_NAME

# Alternative: Use Cloud Build
gcloud builds submit --tag $IMAGE_NAME
```

### Step 3: Create Cloud SQL PostgreSQL Database

```bash
# Create Cloud SQL instance
gcloud sql instances create ai-interviewer-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --root-password=YOUR_ROOT_PASSWORD

# Create database
gcloud sql databases create ai_interviewer_db \
  --instance=ai-interviewer-db

# Create database user
gcloud sql users create db_user \
  --instance=ai-interviewer-db \
  --password=YOUR_DB_PASSWORD
```

### Step 4: Deploy to Cloud Run

```bash
# Deploy service
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances=$PROJECT_ID:$REGION:ai-interviewer-db \
  --set-env-vars="DJANGO_SECRET_KEY=your-secret-key" \
  --set-env-vars="DATABASE_URL=postgresql://db_user:YOUR_DB_PASSWORD@/ai_interviewer_db?host=/cloudsql/$PROJECT_ID:$REGION:ai-interviewer-db" \
  --set-env-vars="GEMINI_API_KEY=your-gemini-key" \
  --set-env-vars="DEEPGRAM_API_KEY=your-deepgram-key" \
  --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/app/ringed-reach-471807-m3-cf0ec93e3257.json" \
  --set-env-vars="BACKEND_URL=https://$SERVICE_NAME-$REGION-$PROJECT_ID.a.run.app" \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --max-instances=10 \
  --min-instances=0

# Get service URL
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
```

### Step 5: Upload Google Cloud Credentials File

```bash
# Copy credentials file to Cloud Run (via Cloud Storage)
gsutil cp ringed-reach-471807-m3-cf0ec93e3257.json gs://$BUCKET_NAME-credentials/

# Or mount as secret (recommended)
gcloud secrets create google-credentials --data-file=ringed-reach-471807-m3-cf0ec93e3257.json

# Update Cloud Run to use secret
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --update-secrets=GOOGLE_APPLICATION_CREDENTIALS=google-credentials:latest
```

### Step 6: Run Database Migrations

```bash
# Connect to Cloud Run service and run migrations
gcloud run jobs create migrate-db \
  --image $IMAGE_NAME \
  --region $REGION \
  --set-env-vars="DATABASE_URL=..." \
  --command="python" \
  --args="manage.py,migrate"

# Execute migration job
gcloud run jobs execute migrate-db --region $REGION

# Or run migrations via Cloud Run service
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --command="sh" \
  --args="-c,python manage.py migrate && gunicorn interview_app.wsgi:application --bind 0.0.0.0:\$PORT --workers 2"
```

---

## 🔗 Connecting Frontend and Backend

### Step 1: Update Frontend API URL

After backend deployment, update frontend:

```bash
cd frontend

# Set backend URL
export BACKEND_URL=https://ai-interviewer-backend-us-central1-xxxxx.a.run.app

# Update vite.config.js or use environment variable
export VITE_API_URL=$BACKEND_URL

# Rebuild
npm run build

# Redeploy to GCS
gsutil -m cp -r dist/* gs://$BUCKET_NAME/
```

### Step 2: Configure CORS in Backend

Ensure `interview_app/settings.py` has:
```python
CORS_ALLOWED_ORIGINS = [
    "https://storage.googleapis.com",
    "https://your-frontend-bucket.storage.googleapis.com",
    "https://your-cdn-domain.com",
]

CORS_ALLOW_CREDENTIALS = True
```

### Step 3: Test Connection

```bash
# Test backend health
curl https://your-backend-service.run.app/api/health/

# Test frontend can reach backend
curl -H "Origin: https://your-frontend-domain.com" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     https://your-backend-service.run.app/api/auth/login/
```

---

## 🔐 Environment Variables Setup

### Backend Environment Variables (Cloud Run)

Set via `gcloud`:
```bash
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --update-env-vars="DJANGO_SECRET_KEY=your-secret-key" \
  --update-env-vars="DJANGO_DEBUG=False" \
  --update-env-vars="DATABASE_URL=postgresql://..." \
  --update-env-vars="GEMINI_API_KEY=your-key" \
  --update-env-vars="DEEPGRAM_API_KEY=your-key" \
  --update-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json" \
  --update-env-vars="BACKEND_URL=https://your-backend.run.app" \
  --update-env-vars="EMAIL_HOST=smtp.gmail.com" \
  --update-env-vars="EMAIL_PORT=587" \
  --update-env-vars="EMAIL_USE_TLS=True" \
  --update-env-vars="EMAIL_HOST_USER=your-email@gmail.com" \
  --update-env-vars="EMAIL_HOST_PASSWORD=your-app-password" \
  --update-env-vars="DEFAULT_FROM_EMAIL=your-email@gmail.com"
```

Or use secrets:
```bash
# Create secrets
gcloud secrets create django-secret-key --data-file=- <<< "your-secret-key"
gcloud secrets create gemini-api-key --data-file=- <<< "your-gemini-key"
gcloud secrets create deepgram-api-key --data-file=- <<< "your-deepgram-key"

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding django-secret-key \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Update service to use secrets
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --update-secrets=DJANGO_SECRET_KEY=django-secret-key:latest
```

### Frontend Environment Variables

Build-time variables (set before `npm run build`):
```bash
export VITE_API_URL=https://your-backend-service.run.app
export VITE_ENVIRONMENT=production
```

---

## ✅ Post-Deployment Verification

### 1. Backend Health Check

```bash
# Check service status
gcloud run services describe $SERVICE_NAME --region $REGION

# Test API endpoint
curl https://your-backend-service.run.app/api/health/

# Check logs
gcloud run services logs read $SERVICE_NAME --region $REGION --limit=50
```

### 2. Frontend Access

```bash
# Get public URL
echo "Frontend URL: https://storage.googleapis.com/$BUCKET_NAME/index.html"

# Or if using CDN
echo "Frontend CDN URL: https://your-cdn-domain.com"

# Test in browser
open https://storage.googleapis.com/$BUCKET_NAME/index.html
```

### 3. Database Connection

```bash
# Connect to Cloud SQL
gcloud sql connect ai-interviewer-db --user=db_user

# Run migrations manually if needed
gcloud run jobs execute migrate-db --region $REGION
```

### 4. API Integration Test

```bash
# Test login endpoint
curl -X POST https://your-backend-service.run.app/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Test CORS
curl -H "Origin: https://your-frontend-domain.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     https://your-backend-service.run.app/api/auth/login/
```

---

## 🎯 Functionality Overview

### Core Features

#### 1. **Authentication & Authorization**
- User registration and login (JWT tokens)
- Role-based access control (Admin, Company, Hiring Agency, Candidate)
- Session management

#### 2. **Candidate Management**
- Candidate profile creation and management
- Resume upload and parsing (PDF, DOCX)
- Candidate search and filtering
- Resume-job matching using AI

#### 3. **Job Management**
- Job posting creation and management
- Job description parsing
- Job search and filtering
- Application tracking

#### 4. **Interview Scheduling**
- Time slot management
- Calendar integration
- Email notifications (SendGrid/Gmail SMTP)
- Interview link generation

#### 5. **AI-Powered Interview System**
- **Spoken Interview Phase**:
  - Real-time speech-to-text (Deepgram)
  - AI question generation (Google Gemini)
  - Text-to-speech (Google Cloud TTS)
  - Answer evaluation and scoring
  
- **Coding Interview Phase**:
  - Coding question generation
  - Code submission and evaluation
  - Real-time feedback

#### 6. **Proctoring & Monitoring**
- Live camera feed (browser-based or backend)
- Face detection (YOLOv8 ONNX + Haar Cascade fallback)
- Proctoring warnings:
  - No person detected
  - Multiple people detected
  - Phone detection
  - Low concentration
  - Tab switching detection
  - Excessive noise
  - Multiple speakers

#### 7. **ID Verification**
- ID card image upload
- OCR text extraction (Google Gemini Vision)
- Name matching with candidate database
- Face count verification (2 faces: candidate + ID photo)

#### 8. **Evaluation & Analytics**
- Comprehensive interview evaluation
- Score calculation (technical, communication, problem-solving)
- PDF report generation
- Dashboard analytics
- Performance metrics

#### 9. **File Management**
- Resume storage (local or GCS)
- Interview recording storage
- Video/audio merge
- Static file serving

#### 10. **Notifications**
- Email notifications (interview scheduled, completed)
- In-app notifications
- Real-time updates via WebSocket

### Technical Stack

**Frontend:**
- React 19
- Redux Toolkit
- React Router
- Vite
- Axios
- Chart.js

**Backend:**
- Django 5.1
- Django REST Framework
- Django Channels (WebSocket)
- PostgreSQL
- Gunicorn

**AI/ML:**
- Google Gemini (text generation, OCR)
- Google Cloud TTS (text-to-speech)
- Deepgram (speech-to-text)
- YOLOv8 ONNX (face detection)
- OpenCV (image processing)

**Infrastructure:**
- Google Cloud Storage (frontend)
- Cloud Run (backend)
- Cloud SQL (PostgreSQL)
- Cloud CDN (optional)

---

## 📝 Deployment Commands Summary

### Frontend Deployment
```bash
# Build
cd frontend && npm install && npm run build

# Deploy to GCS
gsutil -m cp -r dist/* gs://$BUCKET_NAME/
```

### Backend Deployment
```bash
# Build and push
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed
```

### Update After Code Changes
```bash
# Frontend
cd frontend && npm run build && gsutil -m cp -r dist/* gs://$BUCKET_NAME/

# Backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME && \
gcloud run deploy $SERVICE_NAME --image gcr.io/$PROJECT_ID/$SERVICE_NAME --region $REGION
```

---

## 🆘 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check `CORS_ALLOWED_ORIGINS` in Django settings
   - Verify frontend URL is in allowed origins

2. **Database Connection Issues**
   - Verify Cloud SQL instance is running
   - Check connection string format
   - Ensure Cloud Run has Cloud SQL connection

3. **Static Files 404**
   - Run `python manage.py collectstatic`
   - Check `STATIC_URL` and `STATIC_ROOT` settings
   - Verify WhiteNoise is configured

4. **API Key Errors**
   - Verify environment variables are set
   - Check secret access permissions
   - Review Cloud Run logs

5. **Build Failures**
   - Check Dockerfile syntax
   - Verify all dependencies in requirements.txt
   - Review Cloud Build logs

---

## 📚 Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Django Deployment Guide](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [React Production Build](https://react.dev/learn/start-a-new-react-project#building-for-production)

---

**Last Updated**: 2025-01-27
**Version**: 1.0

