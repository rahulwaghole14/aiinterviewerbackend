#!/bin/bash
# Grant Secret Manager access to Cloud Run service account

PROJECT_ID="eastern-team-480811-e6"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "🔐 Granting Secret Manager access..."
echo "Project: $PROJECT_ID"
echo "Project Number: $PROJECT_NUMBER"
echo "Service Account: $SERVICE_ACCOUNT"

# Grant Secret Manager Secret Accessor role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None

echo ""
echo "✅ Permission granted!"
echo ""
echo "Now you can mount the secret:"
echo "gcloud run services update talaroai \\"
echo "  --region asia-southeast1 \\"
echo "  --set-secrets=/etc/secrets/my-service-key.json=my-service-key:latest \\"
echo "  --update-env-vars=\"GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/my-service-key.json\" \\"
echo "  --project=$PROJECT_ID"

