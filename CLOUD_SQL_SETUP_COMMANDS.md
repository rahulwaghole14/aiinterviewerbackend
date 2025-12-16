# 🔧 Cloud SQL Setup Commands

## ✅ Instance Created Successfully

Your Cloud SQL instance `ai-interviewer-db1` has been created!

**Instance Details**:
- Name: `ai-interviewer-db1`
- Version: PostgreSQL 15
- Region: `asia-south2-b`
- Status: RUNNABLE
- Primary IP: `34.131.5.139`

---

## Step 1: Set Project (If Not Set)

```bash
gcloud config set project eastern-team-480811-e6
```

---

## Step 2: Create Database

```bash
gcloud sql databases create ai_interviewer_db1 \
  --instance=ai-interviewer-db1 \
  --project=eastern-team-480811-e6
```

**Note**: Using `ai_interviewer_db1` to match instance name `ai-interviewer-db1`

---

## Step 3: Create Database User

```bash
gcloud sql users create db_user \
  --instance=ai-interviewer-db1 \
  --password=Admin12345 \
  --project=eastern-team-480811-e6
```

**Note**: Using instance name `ai-interviewer-db1` (not `ai-interviewer-db`)

---

## Step 4: Get Connection Name

```bash
gcloud sql instances describe ai-interviewer-db1 \
  --project=eastern-team-480811-e6 \
  --format="value(connectionName)"
```

**Expected Output**: `eastern-team-480811-e6:asia-south2:ai-interviewer-db1`

---

## Step 5: Build DATABASE_URL for Cloud Run

```bash
# Set variables
export PROJECT_ID=eastern-team-480811-e6
export REGION=asia-south2
export INSTANCE_NAME=ai-interviewer-db1
export CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
export DB_PASSWORD=Admin12345
export DB_NAME=ai_interviewer_db1

# Build DATABASE_URL
export DATABASE_URL="postgresql://db_user:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CLOUD_SQL_CONNECTION}"

echo "DATABASE_URL: $DATABASE_URL"
```

**Expected Output**:
```
postgresql://db_user:Admin12345@/ai_interviewer_db1?host=/cloudsql/eastern-team-480811-e6:asia-south2:ai-interviewer-db1
```

---

## Step 6: Deploy Backend to Cloud Run

```bash
# Set variables
export SERVICE_NAME=ai-interviewer-backend
export IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
export DJANGO_SECRET_KEY=your-secret-key-here
export GEMINI_API_KEY=your-gemini-key
export DEEPGRAM_API_KEY=your-deepgram-key

# Build and push image
gcloud builds submit --tag $IMAGE_NAME

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

---

## Step 7: Run Database Migrations

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

---

## 📝 Quick Copy-Paste Commands

```bash
# 1. Set project
gcloud config set project eastern-team-480811-e6

# 2. Create database
gcloud sql databases create ai_interviewer_db1 \
  --instance=ai-interviewer-db1 \
  --project=eastern-team-480811-e6

# 3. Create user
gcloud sql users create db_user \
  --instance=ai-interviewer-db1 \
  --password=Admin12345 \
  --project=eastern-team-480811-e6

# 4. Get connection name
CLOUD_SQL_CONNECTION=$(gcloud sql instances describe ai-interviewer-db1 \
  --project=eastern-team-480811-e6 \
  --format="value(connectionName)")

echo "Cloud SQL Connection: $CLOUD_SQL_CONNECTION"
```

---

## ⚠️ Important Notes

1. **Instance Name**: `ai-interviewer-db1` (not `ai-interviewer-db`)
2. **Database Name**: `ai_interviewer_db1` (to match instance naming)
3. **Connection Name**: Will be `eastern-team-480811-e6:asia-south2:ai-interviewer-db1`
4. **Password**: `Admin12345` (consider changing for production)

---

## 🔄 Update Cloud Build Trigger Substitutions

If using Cloud Build trigger, update these substitutions:

- `_CLOUD_SQL_CONNECTION_NAME` = `eastern-team-480811-e6:asia-south2:ai-interviewer-db1`
- `_DATABASE_URL` = `postgresql://db_user:Admin12345@/ai_interviewer_db1?host=/cloudsql/eastern-team-480811-e6:asia-south2:ai-interviewer-db1`

---

**Last Updated**: 2025-01-27

