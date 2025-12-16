# 🚀 Next Steps: Deploy Backend to Cloud Run

## ✅ Completed Steps
- [x] Cloud SQL instance created: `ai-interviewer-db1`
- [x] Database created: `ai_interviewer_db1`
- [x] User created: `db_user`

---

## Step 1: Get Cloud SQL Connection Name

Run this in Cloud Shell:

```bash
gcloud config set project eastern-team-480811-e6

CLOUD_SQL_CONNECTION=$(gcloud sql instances describe ai-interviewer-db1 \
  --project=eastern-team-480811-e6 \
  --format="value(connectionName)")

echo "Cloud SQL Connection: $CLOUD_SQL_CONNECTION"
```

**Expected Output**: `eastern-team-480811-e6:asia-south2:ai-interviewer-db1`

**Save this value!**

---

## Step 2: Build DATABASE_URL

```bash
# Set variables
export PROJECT_ID=eastern-team-480811-e6
export REGION=asia-south2
export INSTANCE_NAME=ai-interviewer-db1
export CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
export DB_PASSWORD=Admin12345
export DB_NAME=ai_interviewer_db1

# Build DATABASE_URL for Cloud SQL Unix socket
export DATABASE_URL="postgresql://db_user:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CLOUD_SQL_CONNECTION}"

echo "DATABASE_URL: $DATABASE_URL"
```

**Expected Output**:
```
postgresql://db_user:Admin12345@/ai_interviewer_db1?host=/cloudsql/eastern-team-480811-e6:asia-south2:ai-interviewer-db1
```

---

## Step 3: Build and Push Docker Image

```bash
# Set service name
export SERVICE_NAME=ai-interviewer-backend
export IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Build and push image (this will take 10-15 minutes)
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID
```

**This will**:
- Build Docker image from your repository
- Push to Google Container Registry
- Take 10-15 minutes

---

## Step 4: Deploy to Cloud Run

```bash
# Set API keys (replace with your actual keys)
export DJANGO_SECRET_KEY=your-django-secret-key-here
export GEMINI_API_KEY=your-gemini-api-key
export DEEPGRAM_API_KEY=your-deepgram-api-key

# Deploy to Cloud Run
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

**This will**:
- Deploy your backend to Cloud Run
- Connect to Cloud SQL
- Set environment variables
- Make service publicly accessible

**Wait for deployment to complete** (5-10 minutes)

---

## Step 5: Get Service URL

```bash
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

echo "Backend URL: $SERVICE_URL"
```

**Save this URL!** You'll need it for the frontend.

---

## Step 6: Run Database Migrations

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

**This will**:
- Create all database tables
- Run Django migrations
- Set up the database schema

---

## Step 7: Verify Deployment

### 7.1 Test Health Endpoint

```bash
curl $SERVICE_URL/api/health/
```

**Expected**: JSON response or 200 status

### 7.2 Check Service Logs

```bash
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --limit=50
```

### 7.3 Verify Database Connection

Check logs for:
- `[OK] Using Cloud SQL via Unix socket`
- No database connection errors

---

## Step 8: Create Admin User (Optional)

```bash
# Create admin user via Cloud Run job
gcloud run jobs create create-admin \
  --image $IMAGE_NAME \
  --region $REGION \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True" \
  --command="python" \
  --args="manage.py,createsuperuser" \
  --project=$PROJECT_ID

# Execute (will prompt for credentials)
gcloud run jobs execute create-admin --region $REGION --project=$PROJECT_ID
```

Or use the management command if available:
```bash
gcloud run jobs create create-admin \
  --image $IMAGE_NAME \
  --region $REGION \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True" \
  --command="python" \
  --args="manage.py,shell,-c,from django.contrib.auth import get_user_model; User=get_user_model(); User.objects.create_superuser('admin','admin@example.com','password')" \
  --project=$PROJECT_ID
```

---

## 📝 Complete Command Sequence

Copy and paste this entire block into Cloud Shell:

```bash
# Set all variables
export PROJECT_ID=eastern-team-480811-e6
export REGION=asia-south2
export INSTANCE_NAME=ai-interviewer-db1
export SERVICE_NAME=ai-interviewer-backend
export CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
export DB_PASSWORD=Admin12345
export DB_NAME=ai_interviewer_db1
export DATABASE_URL="postgresql://db_user:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CLOUD_SQL_CONNECTION}"
export IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Set your API keys (REPLACE WITH YOUR ACTUAL KEYS)
export DJANGO_SECRET_KEY=your-secret-key-here
export GEMINI_API_KEY=your-gemini-key
export DEEPGRAM_API_KEY=your-deepgram-key

# Step 1: Build and push image
echo "🔨 Building Docker image..."
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID

# Step 2: Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
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

# Step 3: Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

echo "✅ Backend deployed!"
echo "🌐 Backend URL: $SERVICE_URL"

# Step 4: Run migrations
echo "📊 Running database migrations..."
gcloud run jobs create migrate-db \
  --image $IMAGE_NAME \
  --region $REGION \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True" \
  --command="python" \
  --args="manage.py,migrate" \
  --max-retries=3 \
  --project=$PROJECT_ID

gcloud run jobs execute migrate-db --region $REGION --project=$PROJECT_ID

echo "✅ Setup complete!"
echo "Backend URL: $SERVICE_URL"
```

---

## 🔍 Troubleshooting

### Issue: Build fails

**Check**:
- Dockerfile exists in repository root
- requirements.txt is valid
- No syntax errors in code

### Issue: Deployment fails - "Permission denied"

**Solution**:
```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Issue: Database connection fails

**Check**:
- Cloud SQL instance is running
- Connection name is correct
- Cloud Run service account has Cloud SQL access:
```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

---

## ✅ Success Indicators

After deployment, you should see:

- [ ] Service URL is accessible
- [ ] `curl $SERVICE_URL/api/health/` returns 200
- [ ] Logs show "Using Cloud SQL via Unix socket"
- [ ] No database connection errors
- [ ] Migrations completed successfully

---

## 📚 Next Steps After Deployment

1. **Update Frontend**: Set `BACKEND_URL` to your Cloud Run service URL
2. **Test API Endpoints**: Verify all endpoints work
3. **Set Up Monitoring**: Configure Cloud Monitoring
4. **Set Up Automated Deployments**: Use Cloud Build triggers

---

**Last Updated**: 2025-01-27

