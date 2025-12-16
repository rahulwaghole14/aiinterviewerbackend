# ✅ Verify Deployment Status

## Current Status

From your Cloud Build history:
- ✅ **Build `22f18c8e`**: SUCCESS (commit `619a283`) - This is your latest fix!
- ❌ **Build `8aeed566`**: FAILURE (latest attempt)

The successful build should have deployed your interview URL fix.

---

## Step 1: Check Cloud Run Service Status

Run these commands in Cloud Shell:

```bash
# Set project
gcloud config set project eastern-team-480811-e6

# Check service status
gcloud run services describe talaroai \
  --region asia-southeast1 \
  --format="value(status.url,status.conditions[0].status)"

# Get service URL
BACKEND_URL=$(gcloud run services describe talaroai \
  --region asia-southeast1 \
  --format='value(status.url)')

echo "Backend URL: $BACKEND_URL"
```

---

## Step 2: Check Latest Revision

```bash
# Check latest revision
gcloud run revisions list \
  --service=talaroai \
  --region=asia-southeast1 \
  --limit=1 \
  --format="table(metadata.name,status.conditions[0].status,metadata.creationTimestamp)"
```

---

## Step 3: Test Service Health

```bash
# Test health endpoint
curl -s "$BACKEND_URL/api/health/" | head -20

# Or test root
curl -s "$BACKEND_URL/" | head -20
```

---

## Step 4: Check Logs for URL Generation

```bash
# Check recent logs
gcloud run services logs read talaroai \
  --region asia-southeast1 \
  --limit=30 \
  --format="value(textPayload,jsonPayload.message)"

# Look for URL generation
gcloud run services logs read talaroai \
  --region asia-southeast1 \
  --limit=50 \
  | grep -i "interview.*url\|session_key\|get_backend_url"
```

---

## Step 5: Test Interview URL Generation

### Option A: Check Environment Variables

```bash
# Check if K_SERVICE is set (Cloud Run detection)
gcloud run services describe talaroai \
  --region asia-southeast1 \
  --format="value(spec.template.spec.containers[0].env)" \
  | grep -i "K_SERVICE\|BACKEND_URL"
```

### Option B: Create Test Interview via API

```bash
# Set backend URL
export BACKEND_URL="https://talaroai-310576915040.asia-southeast1.run.app"

# Login (replace with your credentials)
TOKEN=$(curl -s -X POST "$BACKEND_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}' \
  | jq -r '.token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
  echo "✅ Login successful"
  
  # Get interviews list
  curl -s "$BACKEND_URL/api/interviews/" \
    -H "Authorization: Token $TOKEN" \
    | jq '.[0] | {id, session_key, interview_url}'
else
  echo "❌ Login failed - check credentials"
fi
```

---

## Step 6: Verify Code is Deployed

Check if the utility function exists:

```bash
# Check if utils.py was deployed (by checking logs or testing)
# The code should auto-detect Cloud Run URL from K_SERVICE

# Test by creating an interview and checking the URL
```

---

## Troubleshooting Failed Build

If the latest build failed, check why:

```bash
# Get build details
gcloud builds describe 8aeed566-f052-4112-a401-3bf4ec6cab25 \
  --format="value(status,statusDetail,failureInfo)"

# Get build logs
gcloud builds log 8aeed566-f052-4112-a401-3bf4ec6cab25
```

---

## Quick Verification Script

Run this in Cloud Shell:

```bash
#!/bin/bash

export PROJECT_ID=eastern-team-480811-e6
export REGION=asia-southeast1
export SERVICE_NAME=talaroai

echo "🔍 Verifying Deployment"
echo "======================"

# 1. Check service status
echo "1. Checking service status..."
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format='value(status.url)' 2>/dev/null)

if [ -n "$BACKEND_URL" ]; then
  echo "   ✅ Service is running"
  echo "   🌐 URL: $BACKEND_URL"
else
  echo "   ❌ Service not found"
  exit 1
fi

# 2. Test health
echo ""
echo "2. Testing health endpoint..."
if curl -s "$BACKEND_URL/api/health/" > /dev/null 2>&1; then
  echo "   ✅ Health check passed"
else
  echo "   ⚠️  Health check failed (may be normal if endpoint doesn't exist)"
fi

# 3. Check latest revision
echo ""
echo "3. Checking latest revision..."
LATEST_REVISION=$(gcloud run revisions list \
  --service=$SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --limit=1 \
  --format='value(metadata.name)' 2>/dev/null)

if [ -n "$LATEST_REVISION" ]; then
  echo "   ✅ Latest revision: $LATEST_REVISION"
  
  # Check revision creation time
  REVISION_TIME=$(gcloud run revisions describe $LATEST_REVISION \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(metadata.creationTimestamp)' 2>/dev/null)
  echo "   📅 Created: $REVISION_TIME"
else
  echo "   ❌ Could not get revision info"
fi

# 4. Check environment variables
echo ""
echo "4. Checking environment variables..."
ENV_VARS=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format="value(spec.template.spec.containers[0].env)" 2>/dev/null)

if echo "$ENV_VARS" | grep -q "K_SERVICE"; then
  K_SERVICE=$(echo "$ENV_VARS" | grep "K_SERVICE" | cut -d'=' -f2)
  echo "   ✅ K_SERVICE detected: $K_SERVICE"
  echo "   ✅ Code will auto-detect Cloud Run URL"
else
  echo "   ⚠️  K_SERVICE not found in env vars"
  echo "   💡 Will use BACKEND_URL if set"
fi

# 5. Check recent logs
echo ""
echo "5. Checking recent logs for URL generation..."
RECENT_LOGS=$(gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --limit=20 2>/dev/null)

if echo "$RECENT_LOGS" | grep -qi "talaroai.*run\.app"; then
  echo "   ✅ Found Cloud Run URLs in logs"
elif echo "$RECENT_LOGS" | grep -qi "localhost"; then
  echo "   ⚠️  Found localhost URLs in logs (may be from old requests)"
else
  echo "   ℹ️  No URL generation found in recent logs"
fi

echo ""
echo "✅ Verification complete!"
echo ""
echo "Next steps:"
echo "1. Create an interview via admin panel or API"
echo "2. Check the generated interview URL"
echo "3. Verify it uses: $BACKEND_URL/?session_key=xxx"
echo "4. Test the link in a browser"
```

Save and run:
```bash
# Save script
cat > verify_deployment.sh << 'EOF'
[paste script above]
EOF

chmod +x verify_deployment.sh
./verify_deployment.sh
```

---

## Expected Results

After verification, you should see:

- ✅ Service is running at: `https://talaroai-310576915040.asia-southeast1.run.app`
- ✅ Latest revision is from commit `619a283` (your fix)
- ✅ K_SERVICE environment variable is set
- ✅ When creating interviews, URLs use Cloud Run domain

---

**Last Updated**: 2025-01-27

