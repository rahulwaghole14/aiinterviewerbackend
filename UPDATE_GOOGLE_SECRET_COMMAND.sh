#!/bin/bash
# Command to mount Google Cloud Secret as file in Cloud Run

gcloud run services update talaroai \
  --region asia-southeast1 \
  --set-secrets=/etc/secrets/my-service-key.json=my-service-key:latest \
  --update-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/my-service-key.json" \
  --project=eastern-team-480811-e6

