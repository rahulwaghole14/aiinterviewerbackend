# ⚡ Quick Steps: Connect Backend Repo & Link Frontend-Backend

## 🎯 Goal
1. Connect to backend repository
2. Deploy backend to Cloud Run
3. Connect frontend to backend

---

## Step 1: Clone Backend Repository (Cloud Shell)

```bash
cd ~
git clone https://github.com/rahulwaghole14/aiinterviewerbackend.git
cd aiinterviewerbackend
```

---

## Step 2: Set Variables

```bash
export PROJECT_ID=eastern-team-480811-e6
export REGION=asia-south2
export INSTANCE_NAME=ai-interviewer-db1
export SERVICE_NAME=ai-interviewer-backend
export CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
export DATABASE_URL="postgresql://db_user:Admin12345@/ai_interviewer_db1?host=/cloudsql/${CLOUD_SQL_CONNECTION}"
export IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Set your API keys
export DJANGO_SECRET_KEY=your-secret-key
export GEMINI_API_KEY=your-gemini-key
export DEEPGRAM_API_KEY=your-deepgram-key
```

---

## Step 3: Build & Deploy Backend

```bash
# Build image
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID

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
  --port=8080 \
  --project=$PROJECT_ID
```

---

## Step 4: Get Backend URL

```bash
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

echo "Backend URL: $BACKEND_URL"
```

**Save this URL!** 📝

---

## Step 5: Run Migrations

```bash
gcloud run jobs create migrate-db \
  --image $IMAGE_NAME \
  --region $REGION \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
  --set-env-vars="DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True" \
  --command="python" \
  --args="manage.py,migrate" \
  --project=$PROJECT_ID

gcloud run jobs execute migrate-db --region $REGION --project=$PROJECT_ID
```

---

## Step 6: Connect Frontend to Backend

### Option A: Update Frontend Repository

```bash
# Navigate to frontend repo
cd ~/aiinterviewerfrontend  # or your frontend path

# Create .env.production
echo "VITE_API_URL=$BACKEND_URL" > .env.production

# Commit and push
git add .env.production
git commit -m "Update backend URL to Cloud Run"
git push origin main
```

### Option B: Update Cloud Build Trigger

1. Go to **Cloud Build** → **Triggers**
2. Edit frontend trigger
3. Add substitution:
   - **Name**: `_VITE_API_URL`
   - **Value**: `$BACKEND_URL` (from Step 4)

---

## Step 7: Test Connection

```bash
# Test backend
curl $BACKEND_URL/api/health/

# Check logs
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --limit=10
```

---

## ✅ Done!

Your frontend should now connect to your Cloud Run backend! 🎉

---

**Need help?** See `BACKEND_FRONTEND_CONNECTION_GUIDE.md` for detailed instructions.

