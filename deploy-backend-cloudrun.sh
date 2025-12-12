#!/bin/bash
# Backend Deployment Script for Google Cloud Run with Cloud SQL
# Usage: ./deploy-backend-cloudrun.sh

set -e  # Exit on error

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-eastern-team-480811-e6}"
SERVICE_NAME="${SERVICE_NAME:-ai-interviewer-backend}"
REGION="${GCP_REGION:-asia-south2}"
INSTANCE_NAME="${CLOUD_SQL_INSTANCE:-ai-interviewer-db}"
CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Starting Backend Deployment to Cloud Run"
echo "============================================="
echo "Project ID: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo "Cloud SQL: $CLOUD_SQL_CONNECTION"
echo ""

# Step 1: Build Docker image
echo "🐳 Step 1: Building Docker image..."
gcloud builds submit --tag $IMAGE_NAME --project $PROJECT_ID

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Image built and pushed: $IMAGE_NAME"

# Step 2: Check if service exists
echo ""
echo "🔍 Step 2: Checking if service exists..."
if gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID &>/dev/null; then
    echo "✅ Service exists, updating..."
    DEPLOY_CMD="gcloud run services update $SERVICE_NAME"
else
    echo "✅ Service doesn't exist, creating..."
    DEPLOY_CMD="gcloud run deploy $SERVICE_NAME"
fi

# Step 3: Deploy to Cloud Run
echo ""
echo "🚀 Step 3: Deploying to Cloud Run..."

# Read environment variables from .env if exists
ENV_VARS=""
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        
        # Remove quotes from value
        value=$(echo "$value" | sed 's/^"//;s/"$//')
        
        if [ -n "$ENV_VARS" ]; then
            ENV_VARS="$ENV_VARS,$key=$value"
        else
            ENV_VARS="$key=$value"
        fi
    done < .env
fi

# Add required variables
ENV_VARS="${ENV_VARS},USE_POSTGRESQL=True,DJANGO_DEBUG=False"

# Build DATABASE_URL if not set
if [[ ! "$ENV_VARS" =~ DATABASE_URL ]]; then
    DB_USER="${DB_USER:-db_user}"
    DB_PASSWORD="${DB_PASSWORD:-your-password}"
    DB_NAME="${DB_NAME:-ai_interviewer_db}"
    DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CLOUD_SQL_CONNECTION}"
    ENV_VARS="${ENV_VARS},DATABASE_URL=${DATABASE_URL}"
fi

# Deploy with Cloud SQL connection
eval "$DEPLOY_CMD \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
    --set-env-vars=\"$ENV_VARS\" \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=0 \
    --port=8080 \
    --project $PROJECT_ID"

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed"
    exit 1
fi

# Step 4: Get service URL
echo ""
echo "🔗 Step 4: Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --project $PROJECT_ID \
    --format 'value(status.url)')

echo "✅ Deployment Complete!"
echo "============================================="
echo "Backend URL: $SERVICE_URL"
echo ""
echo "Next steps:"
echo "1. Run database migrations:"
echo "   gcloud run jobs create migrate-db \\"
echo "     --image $IMAGE_NAME \\"
echo "     --region $REGION \\"
echo "     --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \\"
echo "     --set-env-vars=\"DATABASE_URL=...\" \\"
echo "     --command=\"python\" \\"
echo "     --args=\"manage.py,migrate\""
echo ""
echo "   gcloud run jobs execute migrate-db --region $REGION"
echo ""
echo "2. Test API:"
echo "   curl $SERVICE_URL/api/health/"
echo ""
echo "3. View logs:"
echo "   gcloud run services logs read $SERVICE_NAME --region $REGION --project $PROJECT_ID"

