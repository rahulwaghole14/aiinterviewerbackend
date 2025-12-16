#!/bin/bash
# Backend Deployment Script for Google Cloud Run
# Usage: ./deploy-backend.sh

set -e  # Exit on error

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
SERVICE_NAME="${SERVICE_NAME:-ai-interviewer-backend}"
REGION="${GCP_REGION:-us-central1}"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Starting Backend Deployment to Cloud Run"
echo "============================================="
echo "Project ID: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo "Image: $IMAGE_NAME"
echo ""

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found. Creating default Dockerfile..."
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput || true

EXPOSE 8080

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD python manage.py migrate --noinput && \
    gunicorn interview_app.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --worker-class sync
EOF
    echo "✅ Dockerfile created"
fi

# Step 1: Build and push Docker image
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
            ENV_VARS="$ENV_VARS --update-env-vars=\"$key=$value\""
        else
            ENV_VARS="--set-env-vars=\"$key=$value\""
        fi
    done < .env
fi

# Deploy with basic configuration
eval "$DEPLOY_CMD \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=0 \
    --project $PROJECT_ID \
    $ENV_VARS"

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
echo "1. Update frontend BACKEND_URL to: $SERVICE_URL"
echo "2. Run database migrations if needed"
echo "3. Test API endpoints"
echo ""
echo "To view logs:"
echo "gcloud run services logs read $SERVICE_NAME --region $REGION --project $PROJECT_ID"

