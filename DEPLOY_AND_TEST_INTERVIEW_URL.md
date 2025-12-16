# 🚀 Deploy and Test Interview URL Fix

## Step 1: Deploy Updated Code to Cloud Run

### Option A: Using Cloud Build Trigger (Automatic)

If you have a Cloud Build trigger connected to your GitHub repository:

1. **Check if trigger exists:**
   ```bash
   gcloud builds triggers list --project=eastern-team-480811-e6
   ```

2. **If trigger exists**, it will automatically deploy when you push to GitHub (already done ✅)

3. **Manually trigger build** (if needed):
   ```bash
   # Find your trigger name
   TRIGGER_NAME=$(gcloud builds triggers list --project=eastern-team-480811-e6 --format="value(name)" | grep -i backend | head -1)
   
   # Trigger the build
   gcloud builds triggers run $TRIGGER_NAME \
     --branch=main \
     --project=eastern-team-480811-e6
   ```

### Option B: Manual Deployment

If you don't have a Cloud Build trigger, deploy manually:

```bash
# Set variables
export PROJECT_ID=eastern-team-480811-e6
export REGION=asia-southeast1
export SERVICE_NAME=talaroai
export IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
export CLOUD_SQL_CONNECTION="eastern-team-480811-e6:asia-south2:ai-interviewer-db1"
export DATABASE_URL="postgresql://db_user:Admin12345@/ai_interviewer_db1?host=/cloudsql/${CLOUD_SQL_CONNECTION}"

# Set your API keys
export DJANGO_SECRET_KEY=your-secret-key
export GEMINI_API_KEY=your-gemini-key
export DEEPGRAM_API_KEY=your-deepgram-key

# Build Docker image
echo "🔨 Building Docker image..."
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID

# Deploy to Cloud Run
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
  --port=8080 \
  --project=$PROJECT_ID
```

**Wait for deployment to complete** (5-10 minutes) ⏳

---

## Step 2: Verify Deployment

### 2.1 Check Service Status

```bash
# Get service URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

echo "✅ Backend deployed!"
echo "🌐 Backend URL: $BACKEND_URL"
```

### 2.2 Check Logs

```bash
# View recent logs
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --limit=50

# Follow logs in real-time
gcloud run services logs tail $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID
```

**Look for:**
- ✅ No errors
- ✅ "Starting Gunicorn server on 0.0.0.0:8080"
- ✅ Database connection successful

### 2.3 Test Health Endpoint

```bash
# Test health endpoint
curl $BACKEND_URL/api/health/

# Or test root
curl $BACKEND_URL/
```

**Expected:** JSON response or 200 status ✅

---

## Step 3: Test Interview URL Generation

### 3.1 Create a Test Interview via API

**Option A: Using curl**

```bash
# Set your backend URL
export BACKEND_URL="https://talaroai-310576915040.asia-southeast1.run.app"

# Login and get token (replace with your credentials)
TOKEN=$(curl -X POST "$BACKEND_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}' \
  | jq -r '.token')

# Create a candidate (if needed)
CANDIDATE_ID=$(curl -X POST "$BACKEND_URL/api/candidates/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test Candidate",
    "email": "test@example.com",
    "phone": "+1234567890"
  }' | jq -r '.id')

# Create a job (if needed)
JOB_ID=$(curl -X POST "$BACKEND_URL/api/jobs/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Software Engineer",
    "company_name": "Test Company",
    "job_description": "Test job description"
  }' | jq -r '.id')

# Create an interview
INTERVIEW_RESPONSE=$(curl -X POST "$BACKEND_URL/api/interviews/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"candidate\": $CANDIDATE_ID,
    \"job\": $JOB_ID,
    \"status\": \"scheduled\",
    \"started_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
    \"ended_at\": \"$(date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%SZ)\"
  }")

# Extract interview URL
INTERVIEW_URL=$(echo $INTERVIEW_RESPONSE | jq -r '.interview_url // .session_key // empty')
echo "Interview URL: $INTERVIEW_URL"
```

**Option B: Using Python Script**

Create `test_interview_url.py`:

```python
import requests
import json
from datetime import datetime, timedelta

BACKEND_URL = "https://talaroai-310576915040.asia-southeast1.run.app"

# Login
login_response = requests.post(
    f"{BACKEND_URL}/api/auth/login/",
    json={"email": "your-email@example.com", "password": "your-password"}
)
token = login_response.json()["token"]
headers = {"Authorization": f"Token {token}"}

# Create candidate
candidate_response = requests.post(
    f"{BACKEND_URL}/api/candidates/",
    headers=headers,
    json={
        "full_name": "Test Candidate",
        "email": "test@example.com",
        "phone": "+1234567890"
    }
)
candidate_id = candidate_response.json()["id"]

# Create job
job_response = requests.post(
    f"{BACKEND_URL}/api/jobs/",
    headers=headers,
    json={
        "job_title": "Software Engineer",
        "company_name": "Test Company",
        "job_description": "Test job description"
    }
)
job_id = job_response.json()["id"]

# Create interview
now = datetime.utcnow()
interview_response = requests.post(
    f"{BACKEND_URL}/api/interviews/",
    headers=headers,
    json={
        "candidate": candidate_id,
        "job": job_id,
        "status": "scheduled",
        "started_at": now.isoformat() + "Z",
        "ended_at": (now + timedelta(hours=1)).isoformat() + "Z"
    }
)

interview_data = interview_response.json()
print(f"\n✅ Interview created!")
print(f"Interview ID: {interview_data.get('id')}")
print(f"Session Key: {interview_data.get('session_key')}")

# Get interview URL
if interview_data.get('session_key'):
    interview_url = f"{BACKEND_URL}/?session_key={interview_data['session_key']}"
    print(f"\n🌐 Interview URL: {interview_url}")
    
    # Verify URL doesn't contain localhost
    if 'localhost' in interview_url or '127.0.0.1' in interview_url:
        print("❌ ERROR: URL contains localhost!")
    else:
        print("✅ SUCCESS: URL uses Cloud Run domain!")
```

Run it:
```bash
python test_interview_url.py
```

### 3.2 Create Interview via Admin Panel

1. **Open your backend URL:**
   ```
   https://talaroai-310576915040.asia-southeast1.run.app/admin/
   ```

2. **Login** with your admin credentials

3. **Navigate to:** Interviews → Add Interview

4. **Fill in the form:**
   - Select candidate
   - Select job
   - Set start time and end time
   - Save

5. **Check the interview URL:**
   - Look at the interview details page
   - Check the "Interview URL" field
   - **Verify it shows:** `https://talaroai-310576915040.asia-southeast1.run.app/?session_key=xxx`
   - **NOT:** `http://localhost:8000/?session_key=xxx`

### 3.3 Check Logs for URL Generation

```bash
# Watch logs for URL generation
gcloud run services logs tail $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  | grep -i "interview.*url\|session_key"
```

**Look for:**
- `📧 Generated interview URL: https://talaroai-310576915040.asia-southeast1.run.app/?session_key=xxx`
- `[EMAIL DEBUG] Generated interview URL: https://talaroai-310576915040.asia-southeast1.run.app/?session_key=xxx`

---

## Step 4: Verify Interview Link Works

### 4.1 Test from Browser

1. **Copy the interview URL** (should be: `https://talaroai-310576915040.asia-southeast1.run.app/?session_key=xxx`)

2. **Open in a new browser window** (or incognito mode)

3. **Verify:**
   - ✅ Page loads successfully
   - ✅ No "localhost" errors
   - ✅ Interview portal appears
   - ✅ Can start the interview

### 4.2 Test from Different Device/Network

1. **Share the interview URL** with someone else
2. **Or test from your phone** (different network)
3. **Verify it works** from anywhere

### 4.3 Test API Response

```bash
# Get interview details via API
curl "$BACKEND_URL/api/interviews/$INTERVIEW_ID/" \
  -H "Authorization: Token $TOKEN" \
  | jq '.interview_url, .session_key'
```

**Expected:**
- `interview_url`: `https://talaroai-310576915040.asia-southeast1.run.app/?session_key=xxx`
- `session_key`: `xxx...`

---

## Step 5: Troubleshooting

### Issue: Still Getting localhost URLs

**Check 1: Verify Environment Variables**

```bash
# Check Cloud Run environment variables
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format="value(spec.template.spec.containers[0].env)"
```

**Check 2: Verify Code is Deployed**

```bash
# Check latest revision
gcloud run revisions list \
  --service=$SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --limit=1
```

**Check 3: Check Logs for URL Generation**

```bash
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --limit=100 \
  | grep -i "interview.*url\|get_backend_url\|K_SERVICE"
```

**Solution: Set BACKEND_URL Explicitly**

```bash
# Set BACKEND_URL environment variable
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-env-vars="BACKEND_URL=https://talaroai-310576915040.asia-southeast1.run.app" \
  --project=$PROJECT_ID
```

### Issue: Interview Link Doesn't Work

**Check:**
1. Session key is valid
2. Interview hasn't expired
3. CORS is configured correctly
4. Service is accessible

**Test:**
```bash
# Test interview portal directly
curl "https://talaroai-310576915040.asia-southeast1.run.app/?session_key=YOUR_SESSION_KEY"
```

---

## ✅ Success Checklist

After deployment and testing, verify:

- [ ] Code deployed successfully to Cloud Run
- [ ] Service is running and accessible
- [ ] Created a new interview
- [ ] Interview URL uses Cloud Run domain (not localhost)
- [ ] Interview link works from browser
- [ ] Interview link works from different device/network
- [ ] Logs show correct URL generation
- [ ] No errors in Cloud Run logs

---

## Quick Test Script

Save this as `quick_test.sh`:

```bash
#!/bin/bash

export PROJECT_ID=eastern-team-480811-e6
export REGION=asia-southeast1
export SERVICE_NAME=talaroai
export BACKEND_URL="https://talaroai-310576915040.asia-southeast1.run.app"

echo "🧪 Testing Interview URL Generation"
echo "===================================="

# Test 1: Service is running
echo "1. Testing service health..."
if curl -s "$BACKEND_URL/api/health/" > /dev/null; then
    echo "   ✅ Service is running"
else
    echo "   ❌ Service is not responding"
    exit 1
fi

# Test 2: Check environment variables
echo "2. Checking Cloud Run environment..."
ENV_VARS=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format="value(spec.template.spec.containers[0].env)" 2>/dev/null)

if echo "$ENV_VARS" | grep -q "K_SERVICE"; then
    echo "   ✅ K_SERVICE environment variable detected"
else
    echo "   ⚠️  K_SERVICE not found (will use BACKEND_URL)"
fi

# Test 3: Check logs for URL generation
echo "3. Checking recent logs..."
LOGS=$(gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --limit=20 2>/dev/null)

if echo "$LOGS" | grep -qi "talaroai.*run\.app"; then
    echo "   ✅ Found Cloud Run URLs in logs"
else
    echo "   ⚠️  No Cloud Run URLs found in recent logs"
fi

echo ""
echo "✅ Basic tests completed!"
echo "Next: Create an interview and verify the URL"
```

Run it:
```bash
chmod +x quick_test.sh
./quick_test.sh
```

---

**Last Updated**: 2025-01-27

