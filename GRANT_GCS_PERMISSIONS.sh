#!/bin/bash
# Grant GCS permissions to Cloud Run service account

export PROJECT_ID="eastern-team-480811-e6"

echo "🔑 Getting project number..."
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")

if [ -z "$PROJECT_NUMBER" ]; then
    echo "❌ Could not get project number. Please check your project ID."
    exit 1
fi

echo "📊 Project Number: ${PROJECT_NUMBER}"

# Cloud Run service account email
CLOUD_RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "🔐 Granting Storage Object Admin role to Cloud Run service account..."
echo "   Service Account: ${CLOUD_RUN_SA}"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${CLOUD_RUN_SA}" \
    --role="roles/storage.objectAdmin"

echo ""
echo "✅ Permissions granted!"
echo "📝 The Cloud Run service account can now upload/download files from GCS."

