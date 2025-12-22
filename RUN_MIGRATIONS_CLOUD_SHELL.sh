#!/bin/bash
# Script to run Django migrations on Google Cloud Run
# Run this in Cloud Shell: bash RUN_MIGRATIONS_CLOUD_SHELL.sh

set -e

# Set your project details
PROJECT_ID="eastern-team-480811-e6"
REGION="asia-southeast1"
SERVICE_NAME="talaroai"

echo "🚀 Starting migration process..."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"

# Set the gcloud project
gcloud config set project ${PROJECT_ID}

# Get Cloud Run image name
IMAGE_NAME="asia-southeast1-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/aiinterviewerbackend/talaroai:latest"
echo "📦 Image: ${IMAGE_NAME}"

# Get Cloud SQL connection name
echo "🔍 Getting Cloud SQL connection name..."
CLOUD_SQL_CONNECTION_NAME=$(gcloud sql instances describe ai-interviewer-db1 \
  --project=${PROJECT_ID} \
  --format="value(connectionName)")

if [ -z "$CLOUD_SQL_CONNECTION_NAME" ]; then
  echo "❌ Error: Could not get Cloud SQL connection name"
  exit 1
fi

echo "✅ Cloud SQL Connection: ${CLOUD_SQL_CONNECTION_NAME}"

# Get environment variables from Cloud Run service
echo "🔍 Getting environment variables from Cloud Run service..."
ENV_VARS_JSON=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format="json" | jq -r '.spec.template.spec.containers[0].env[] | "\(.name)=\(.value)"' | tr '\n' ',' | sed 's/,$//')

if [ -z "$ENV_VARS_JSON" ]; then
  echo "⚠️  Warning: Could not get environment variables from service"
  echo "   Using manual environment variables..."
  ENV_VARS="DJANGO_SECRET_KEY=your-secret-key,DATABASE_URL=your-database-url,USE_POSTGRESQL=True"
else
  ENV_VARS="${ENV_VARS_JSON}"
fi

echo "✅ Environment variables configured"

# Check if migration job already exists
echo "🔍 Checking if migration job exists..."
if gcloud run jobs describe run-migrations --region=${REGION} --project=${PROJECT_ID} &>/dev/null; then
  echo "⚠️  Migration job already exists. Updating..."
  gcloud run jobs update run-migrations \
    --image=${IMAGE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --set-env-vars="${ENV_VARS}" \
    --add-cloudsql-instances=${CLOUD_SQL_CONNECTION_NAME} \
    --command="python" \
    --args="manage.py,migrate" \
    --max-retries=1 \
    --task-timeout=600
else
  echo "📝 Creating new migration job..."
  gcloud run jobs create run-migrations \
    --image=${IMAGE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --set-env-vars="${ENV_VARS}" \
    --add-cloudsql-instances=${CLOUD_SQL_CONNECTION_NAME} \
    --command="python" \
    --args="manage.py,migrate" \
    --max-retries=1 \
    --task-timeout=600
fi

echo "✅ Migration job created/updated"

# Execute the migration job
echo "🚀 Executing migration job..."
gcloud run jobs execute run-migrations \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --wait

echo "✅ Migration completed!"

# Show recent logs
echo ""
echo "📋 Recent migration logs:"
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=run-migrations" \
  --limit=50 \
  --project=${PROJECT_ID} \
  --format="table(timestamp,textPayload)"

echo ""
echo "✅ Done! Check the logs above for migration results."

