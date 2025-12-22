#!/bin/bash
# Alternative method to get environment variables without jq

PROJECT_ID="eastern-team-480811-e6"
REGION="asia-southeast1"
SERVICE_NAME="talaroai"

# Get environment variables using Python (available in Cloud Shell)
ENV_VARS=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --format="json" | python3 -c "
import json
import sys
data = json.load(sys.stdin)
env_list = []
for env in data['spec']['template']['spec']['containers'][0]['env']:
    name = env['name']
    value = env['value']
    env_list.append(f\"{name}={value}\")
print(','.join(env_list))
")

echo "Environment variables:"
echo "${ENV_VARS}"

