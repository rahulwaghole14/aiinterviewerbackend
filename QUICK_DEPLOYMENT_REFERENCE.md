# ⚡ Quick Deployment Reference

## 🚀 One-Command Deployment

### Frontend (GCS)
```bash
export GCP_PROJECT_ID=your-project-id
export GCS_BUCKET_NAME=ai-interviewer-frontend
export BACKEND_URL=https://your-backend-service.run.app
./deploy-frontend.sh
```

### Backend (Cloud Run)
```bash
export GCP_PROJECT_ID=your-project-id
export SERVICE_NAME=ai-interviewer-backend
export GCP_REGION=us-central1
./deploy-backend.sh
```

---

## 📋 Prerequisites Checklist

- [ ] GCP account with billing enabled
- [ ] `gcloud` CLI installed and authenticated
- [ ] Docker installed (for Cloud Run)
- [ ] Node.js 18+ installed (for frontend build)
- [ ] Python 3.11+ installed (for local testing)

---

## 🔧 Initial Setup (One-Time)

```bash
# 1. Authenticate
gcloud auth login
gcloud auth application-default login

# 2. Set project
export GCP_PROJECT_ID=your-project-id
gcloud config set project $GCP_PROJECT_ID

# 3. Enable APIs
./setup-gcp-project.sh

# 4. Create Cloud SQL database (if needed)
gcloud sql instances create ai-interviewer-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

gcloud sql databases create ai_interviewer_db \
  --instance=ai-interviewer-db
```

---

## 🌐 Frontend Deployment Commands

### Build Only
```bash
cd frontend
npm install
export VITE_API_URL=https://your-backend.run.app
npm run build
```

### Deploy to GCS
```bash
# Set variables
export GCS_BUCKET_NAME=ai-interviewer-frontend
export GCP_PROJECT_ID=your-project-id

# Create bucket (first time only)
gsutil mb -p $GCP_PROJECT_ID -c STANDARD -l us-central1 gs://$GCS_BUCKET_NAME
gsutil web set -m index.html -e index.html gs://$GCS_BUCKET_NAME
gsutil iam ch allUsers:objectViewer gs://$GCS_BUCKET_NAME

# Upload files
gsutil -m cp -r frontend/dist/* gs://$GCS_BUCKET_NAME/
```

### Access Frontend
```
https://storage.googleapis.com/YOUR_BUCKET_NAME/index.html
```

---

## 🔧 Backend Deployment Commands

### Build Docker Image
```bash
export PROJECT_ID=your-project-id
export SERVICE_NAME=ai-interviewer-backend
export IMAGE_NAME=gcr.io/$PROJECT_ID/$SERVICE_NAME

gcloud builds submit --tag $IMAGE_NAME
```

### Deploy to Cloud Run
```bash
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --set-env-vars="DJANGO_SECRET_KEY=your-secret-key" \
  --set-env-vars="DATABASE_URL=postgresql://user:pass@host/db" \
  --set-env-vars="GEMINI_API_KEY=your-key" \
  --set-env-vars="DEEPGRAM_API_KEY=your-key"
```

### Get Service URL
```bash
gcloud run services describe $SERVICE_NAME \
  --region us-central1 \
  --format 'value(status.url)'
```

---

## 🔗 Connect Frontend to Backend

### 1. Get Backend URL
```bash
BACKEND_URL=$(gcloud run services describe ai-interviewer-backend \
  --region us-central1 \
  --format 'value(status.url)')
echo $BACKEND_URL
```

### 2. Update Frontend Config
Edit `frontend/src/config/constants.js`:
```javascript
const getApiBaseUrl = () => {
  if (import.meta.env.PROD) {
    return 'https://your-backend-service.run.app'; // Replace with actual URL
  }
  return 'http://127.0.0.1:8000';
};
```

### 3. Rebuild and Redeploy Frontend
```bash
cd frontend
export VITE_API_URL=$BACKEND_URL
npm run build
cd ..
gsutil -m cp -r frontend/dist/* gs://$GCS_BUCKET_NAME/
```

---

## 🔐 Environment Variables

### Required Backend Variables
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

### Set via gcloud
```bash
gcloud run services update $SERVICE_NAME \
  --region us-central1 \
  --update-env-vars="KEY1=value1,KEY2=value2"
```

---

## 📊 Useful Commands

### View Logs
```bash
# Backend logs
gcloud run services logs read $SERVICE_NAME --region us-central1 --limit=50

# Real-time logs
gcloud run services logs tail $SERVICE_NAME --region us-central1
```

### Check Service Status
```bash
gcloud run services describe $SERVICE_NAME --region us-central1
```

### Test API
```bash
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
  --region us-central1 --format 'value(status.url)')
curl $BACKEND_URL/api/health/
```

### Run Migrations
```bash
# Via Cloud Run job
gcloud run jobs create migrate-db \
  --image $IMAGE_NAME \
  --region us-central1 \
  --set-env-vars="DATABASE_URL=..." \
  --command="python" \
  --args="manage.py,migrate"

gcloud run jobs execute migrate-db --region us-central1
```

---

## 🐛 Troubleshooting

### CORS Errors
```bash
# Check CORS settings in Django
gcloud run services logs read $SERVICE_NAME --region us-central1 | grep CORS
```

### Database Connection Issues
```bash
# Test database connection
gcloud sql connect ai-interviewer-db --user=db_user
```

### Build Failures
```bash
# Check Cloud Build logs
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

### Service Not Starting
```bash
# Check service logs
gcloud run services logs read $SERVICE_NAME --region us-central1 --limit=100
```

---

## 📝 File Structure

```
.
├── Dockerfile                 # Backend Docker image
├── deploy-frontend.sh        # Frontend deployment script
├── deploy-backend.sh         # Backend deployment script
├── setup-gcp-project.sh      # GCP setup script
├── requirements.txt          # Python dependencies
├── frontend/
│   ├── package.json          # Node dependencies
│   ├── vite.config.js        # Vite config
│   └── src/
│       └── config/
│           └── constants.js  # API URL config
└── interview_app/
    └── settings.py           # Django settings
```

---

## 🔄 Update Workflow

### After Code Changes

**Backend:**
```bash
# 1. Build new image
gcloud builds submit --tag $IMAGE_NAME

# 2. Deploy
gcloud run deploy $SERVICE_NAME --image $IMAGE_NAME --region us-central1
```

**Frontend:**
```bash
# 1. Build
cd frontend && npm run build && cd ..

# 2. Deploy
gsutil -m cp -r frontend/dist/* gs://$GCS_BUCKET_NAME/
```

---

## 📞 Support

For detailed instructions, see `DEPLOYMENT_GUIDE.md`

For issues:
1. Check Cloud Run logs
2. Check Cloud Build logs
3. Verify environment variables
4. Test API endpoints manually

