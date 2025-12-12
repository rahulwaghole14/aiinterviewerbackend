# ⚡ Quick Backend Deployment to Cloud Run

## 🚀 One-Command Deployment

### Prerequisites Setup (One-Time)

```bash
# Set variables
export PROJECT_ID=eastern-team-480811-e6
export REGION=asia-south2
export INSTANCE_NAME=ai-interviewer-db

# Create Cloud SQL instance (if not exists)
gcloud sql instances create $INSTANCE_NAME \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --root-password=YOUR_DB_PASSWORD

# Create database
gcloud sql databases create ai_interviewer_db --instance=$INSTANCE_NAME

# Create user
gcloud sql users create db_user --instance=$INSTANCE_NAME --password=YOUR_DB_PASSWORD
```

### Quick Deploy

```bash
# Set all variables
export PROJECT_ID=eastern-team-480811-e6
export SERVICE_NAME=ai-interviewer-backend
export REGION=asia-south2
export INSTANCE_NAME=ai-interviewer-db
export CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
export DB_PASSWORD=your-db-password
export DJANGO_SECRET_KEY=your-secret-key
export GEMINI_API_KEY=your-gemini-key
export DEEPGRAM_API_KEY=your-deepgram-key

# Build DATABASE_URL for Cloud SQL
export DATABASE_URL="postgresql://db_user:${DB_PASSWORD}@/ai_interviewer_db?host=/cloudsql/${CLOUD_SQL_CONNECTION}"

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME && \
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY},DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True,GEMINI_API_KEY=${GEMINI_API_KEY},DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY},DJANGO_DEBUG=False" \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --port=8080

# Run migrations
gcloud run jobs create migrate-db \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True" \
  --command="python" \
  --args="manage.py,migrate" && \
gcloud run jobs execute migrate-db --region $REGION
```

## 📝 Files Created

1. **Dockerfile** - Updated for Cloud Run
2. **cloudbuild-backend.yaml** - Cloud Build configuration
3. **deploy-backend-cloudrun.sh** - Deployment script
4. **BACKEND_CLOUD_RUN_DEPLOYMENT.md** - Complete guide

---

**See BACKEND_CLOUD_RUN_DEPLOYMENT.md for detailed instructions**

