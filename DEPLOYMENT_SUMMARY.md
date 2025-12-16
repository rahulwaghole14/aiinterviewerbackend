# 📦 Deployment Summary: AI Interview Portal

## 🎯 Overview

This project consists of two main components:
1. **Frontend**: React application deployed to **Google Cloud Storage (GCS)**
2. **Backend**: Django REST API deployed to **Google Cloud Run** (Vertex AI compatible)

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `DEPLOYMENT_GUIDE.md` | Complete step-by-step deployment guide |
| `QUICK_DEPLOYMENT_REFERENCE.md` | Quick command reference |
| `deploy-frontend.sh` | Automated frontend deployment script |
| `deploy-backend.sh` | Automated backend deployment script |
| `setup-gcp-project.sh` | GCP project initialization script |
| `Dockerfile` | Backend Docker image configuration |

---

## 🚀 Quick Start

### 1. Initial Setup (One-Time)
```bash
# Authenticate with GCP
gcloud auth login
gcloud auth application-default login

# Set project
export GCP_PROJECT_ID=your-project-id
gcloud config set project $GCP_PROJECT_ID

# Setup GCP project
./setup-gcp-project.sh
```

### 2. Deploy Backend
```bash
export GCP_PROJECT_ID=your-project-id
export SERVICE_NAME=ai-interviewer-backend
export GCP_REGION=us-central1
./deploy-backend.sh
```

### 3. Deploy Frontend
```bash
export GCP_PROJECT_ID=your-project-id
export GCS_BUCKET_NAME=ai-interviewer-frontend
export BACKEND_URL=https://your-backend-service.run.app  # From step 2
./deploy-frontend.sh
```

---

## 🏗️ Architecture

```
┌─────────────────┐
│   User Browser  │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────────────────────┐
│  Google Cloud Storage (GCS)     │
│  Frontend Static Files          │
│  + Cloud CDN (optional)         │
└────────┬────────────────────────┘
         │ API Calls
         ▼
┌─────────────────────────────────┐
│  Cloud Run (Django Backend)     │
│  - REST API                     │
│  - WebSocket                    │
│  - AI Processing                │
└────────┬────────────────────────┘
         │
    ┌────┼────┐
    ▼    ▼    ▼
┌────┐ ┌────┐ ┌────┐
│PostgreSQL│ │Vertex│ │  GCS  │
│Database │ │  AI  │ │Storage│
└────┘ └────┘ └────┘
```

---

## 🔑 Key Components

### Frontend (React)
- **Location**: `frontend/` directory
- **Build Tool**: Vite
- **Deployment**: Google Cloud Storage
- **Access**: `https://storage.googleapis.com/BUCKET_NAME/index.html`

### Backend (Django)
- **Location**: Root directory
- **Framework**: Django 5.1 + Django REST Framework
- **Deployment**: Google Cloud Run
- **Access**: `https://SERVICE_NAME-REGION-PROJECT_ID.a.run.app`

### Database
- **Type**: PostgreSQL (Cloud SQL)
- **Connection**: Via Cloud SQL Proxy in Cloud Run

### AI Services
- **Google Gemini**: Text generation, OCR
- **Google Cloud TTS**: Text-to-speech
- **Deepgram**: Speech-to-text
- **YOLOv8 ONNX**: Face detection

---

## 📋 Required Environment Variables

### Backend (Cloud Run)
```bash
DJANGO_SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host/db
GEMINI_API_KEY=your-gemini-key
DEEPGRAM_API_KEY=your-deepgram-key
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
BACKEND_URL=https://your-backend.run.app
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Frontend (Build-Time)
```bash
VITE_API_URL=https://your-backend-service.run.app
```

---

## 🔄 Deployment Workflow

### Backend Updates
```bash
# 1. Make code changes
# 2. Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
gcloud run deploy $SERVICE_NAME --image gcr.io/$PROJECT_ID/$SERVICE_NAME --region us-central1
```

### Frontend Updates
```bash
# 1. Make code changes
# 2. Build
cd frontend && npm run build && cd ..
# 3. Deploy
gsutil -m cp -r frontend/dist/* gs://$GCS_BUCKET_NAME/
```

---

## 🎯 Functionality Overview

### Core Features
1. **Authentication & Authorization**
   - User registration/login
   - JWT token-based auth
   - Role-based access control

2. **Candidate Management**
   - Profile management
   - Resume upload/parsing
   - AI-powered resume-job matching

3. **Job Management**
   - Job posting
   - Job search/filtering
   - Application tracking

4. **Interview Scheduling**
   - Time slot management
   - Calendar integration
   - Email notifications

5. **AI Interview System**
   - **Spoken Interview**: Real-time Q&A with AI
   - **Coding Interview**: Code challenges and evaluation
   - **Proctoring**: Live monitoring with face detection
   - **ID Verification**: OCR-based verification

6. **Evaluation & Analytics**
   - Comprehensive scoring
   - PDF report generation
   - Dashboard analytics

---

## 📊 Service URLs

After deployment, you'll have:

- **Frontend**: `https://storage.googleapis.com/YOUR_BUCKET_NAME/index.html`
- **Backend API**: `https://SERVICE_NAME-REGION-PROJECT_ID.a.run.app`
- **API Health**: `https://SERVICE_NAME-REGION-PROJECT_ID.a.run.app/api/health/`

---

## 🛠️ Useful Commands

### View Logs
```bash
# Backend
gcloud run services logs read $SERVICE_NAME --region us-central1

# Real-time
gcloud run services logs tail $SERVICE_NAME --region us-central1
```

### Check Status
```bash
gcloud run services describe $SERVICE_NAME --region us-central1
```

### Test API
```bash
curl https://your-backend.run.app/api/health/
```

### Run Migrations
```bash
gcloud run jobs create migrate-db \
  --image $IMAGE_NAME \
  --region us-central1 \
  --command="python" \
  --args="manage.py,migrate"
```

---

## 🐛 Common Issues & Solutions

### Issue: CORS Errors
**Solution**: Check `CORS_ALLOWED_ORIGINS` in Django settings includes frontend URL

### Issue: Database Connection Failed
**Solution**: Verify Cloud SQL instance is running and Cloud Run has Cloud SQL connection

### Issue: Static Files 404
**Solution**: Run `python manage.py collectstatic` before deployment

### Issue: API Key Errors
**Solution**: Verify environment variables are set correctly in Cloud Run

---

## 📖 Detailed Documentation

For complete step-by-step instructions, see:
- **Full Guide**: `DEPLOYMENT_GUIDE.md`
- **Quick Reference**: `QUICK_DEPLOYMENT_REFERENCE.md`

---

## 🔐 Security Notes

1. **Never commit** `.env` files or credentials
2. Use **GCP Secrets Manager** for sensitive values
3. Enable **HTTPS only** for Cloud Run
4. Set **CORS** properly to restrict origins
5. Use **strong Django SECRET_KEY** in production

---

## 📞 Support

For deployment issues:
1. Check Cloud Run logs
2. Check Cloud Build logs
3. Verify environment variables
4. Test API endpoints manually
5. Review `DEPLOYMENT_GUIDE.md` for detailed troubleshooting

---

**Last Updated**: 2025-01-27
**Version**: 1.0

