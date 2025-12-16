#!/bin/bash
# GCP Project Setup Script
# This script enables required APIs and sets up basic infrastructure
# Usage: ./setup-gcp-project.sh

set -e

PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"

echo "🔧 Setting up GCP Project: $PROJECT_ID"
echo "========================================"

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo ""
echo "📡 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    storage-api.googleapis.com \
    storage-component.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    aiplatform.googleapis.com \
    compute.googleapis.com \
    secretmanager.googleapis.com \
    --project $PROJECT_ID

echo "✅ APIs enabled"

# Create Cloud SQL instance (optional - uncomment if needed)
# echo ""
# echo "🗄️  Creating Cloud SQL instance..."
# gcloud sql instances create ai-interviewer-db \
#     --database-version=POSTGRES_15 \
#     --tier=db-f1-micro \
#     --region=$REGION \
#     --root-password=$(openssl rand -base64 32) \
#     --project $PROJECT_ID

# echo "✅ Cloud SQL instance created"
# echo "Note: Remember to create database and user manually"

# Create secrets (optional - uncomment and fill values)
# echo ""
# echo "🔐 Creating secrets..."
# echo "Enter Django Secret Key:"
# read -s DJANGO_SECRET_KEY
# echo -n "$DJANGO_SECRET_KEY" | gcloud secrets create django-secret-key \
#     --data-file=- \
#     --project $PROJECT_ID

# echo "Enter Gemini API Key:"
# read -s GEMINI_API_KEY
# echo -n "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
#     --data-file=- \
#     --project $PROJECT_ID

# echo "Enter Deepgram API Key:"
# read -s DEEPGRAM_API_KEY
# echo -n "$DEEPGRAM_API_KEY" | gcloud secrets create deepgram-api-key \
#     --data-file=- \
#     --project $PROJECT_ID

# echo "✅ Secrets created"

echo ""
echo "✅ GCP Project Setup Complete!"
echo "========================================"
echo "Next steps:"
echo "1. Create Cloud SQL database (if not done)"
echo "2. Create secrets for API keys (if not done)"
echo "3. Run: ./deploy-backend.sh"
echo "4. Run: ./deploy-frontend.sh"

