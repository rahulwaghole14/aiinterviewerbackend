#!/bin/bash
# Frontend Deployment Script for Google Cloud Storage
# Usage: ./deploy-frontend.sh

set -e  # Exit on error

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
BUCKET_NAME="${GCS_BUCKET_NAME:-ai-interviewer-frontend}"
REGION="${GCP_REGION:-us-central1}"
BACKEND_URL="${BACKEND_URL:-https://your-backend-service.run.app}"

echo "🚀 Starting Frontend Deployment to GCS"
echo "========================================"
echo "Project ID: $PROJECT_ID"
echo "Bucket: $BUCKET_NAME"
echo "Region: $REGION"
echo "Backend URL: $BACKEND_URL"
echo ""

# Step 1: Build Frontend
echo "📦 Step 1: Building frontend..."
cd frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Set backend URL for build
export VITE_API_URL=$BACKEND_URL

# Build for production
echo "Building production bundle..."
npm run build

if [ ! -d "dist" ]; then
    echo "❌ Build failed: dist/ directory not found"
    exit 1
fi

echo "✅ Build completed successfully"
cd ..

# Step 2: Create bucket if it doesn't exist
echo ""
echo "🪣 Step 2: Checking/Creating GCS bucket..."
if ! gsutil ls -b gs://$BUCKET_NAME &>/dev/null; then
    echo "Creating bucket: gs://$BUCKET_NAME"
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME
    echo "✅ Bucket created"
else
    echo "✅ Bucket already exists"
fi

# Step 3: Configure bucket for static website hosting
echo ""
echo "⚙️  Step 3: Configuring bucket for static hosting..."
gsutil web set -m index.html -e index.html gs://$BUCKET_NAME
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
echo "✅ Bucket configured"

# Step 4: Upload files
echo ""
echo "📤 Step 4: Uploading files to GCS..."
gsutil -m cp -r frontend/dist/* gs://$BUCKET_NAME/

# Set correct content types
echo "Setting content types..."
gsutil -m setmeta -h "Content-Type:text/html" gs://$BUCKET_NAME/*.html 2>/dev/null || true
gsutil -m setmeta -h "Content-Type:application/javascript" gs://$BUCKET_NAME/**/*.js 2>/dev/null || true
gsutil -m setmeta -h "Content-Type:text/css" gs://$BUCKET_NAME/**/*.css 2>/dev/null || true

echo "✅ Files uploaded"

# Step 5: Display URLs
echo ""
echo "✅ Deployment Complete!"
echo "========================================"
echo "Frontend URL: https://storage.googleapis.com/$BUCKET_NAME/index.html"
echo ""
echo "To access via custom domain, set up Cloud CDN or Cloud Load Balancer"
echo "See DEPLOYMENT_GUIDE.md for CDN setup instructions"

