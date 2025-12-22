#!/bin/bash
# Script to run Django migrations on Google Cloud Run
# Run this in Cloud Shell: bash RUN_MIGRATIONS_FIXED.sh

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

# Get the actual image name from Cloud Run service
echo "🔍 Getting image name from Cloud Run service..."
IMAGE_NAME=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format="value(spec.template.spec.containers[0].image)")

if [ -z "$IMAGE_NAME" ]; then
  echo "❌ Error: Could not get image name from Cloud Run service"
  exit 1
fi

echo "✅ Image: ${IMAGE_NAME}"

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

# Get environment variables from Cloud Run service and format them properly
echo "🔍 Getting environment variables from Cloud Run service..."
ENV_VARS=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format="json" | jq -r '.spec.template.spec.containers[0].env[] | "\(.name)=\(.value)"' | tr '\n' ',' | sed 's/,$//')

if [ -z "$ENV_VARS" ]; then
  echo "❌ Error: Could not get environment variables from Cloud Run service"
  echo ""
  echo "Please run this command manually to get environment variables:"
  echo "gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='get(spec.template.spec.containers[0].env)'"
  echo ""
  echo "Then format them as: KEY1=value1,KEY2=value2,KEY3=value3"
  echo "And set ENV_VARS variable before running the job creation command."
  exit 1
fi

echo "✅ Environment variables configured"

# Check if migration job already exists
echo "🔍 Checking if migration job exists..."
if gcloud run jobs describe run-migrations --region=${REGION} --project=${PROJECT_ID} &>/dev/null; then
  echo "⚠️  Migration job already exists. Deleting and recreating..."
  gcloud run jobs delete run-migrations \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --quiet
fi

echo "📝 Creating new migration job..."
gcloud run jobs create run-migrations \
  --image=${IMAGE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --set-env-vars="${ENV_VARS}" \
  --set-cloudsql-instances=${CLOUD_SQL_CONNECTION_NAME} \
  --command="python" \
  --args="manage.py,migrate" \
  --max-retries=1 \
  --task-timeout=600

echo "✅ Migration job created"

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

