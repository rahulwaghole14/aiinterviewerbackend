#!/bin/bash
# Create GCS bucket for PDF storage
# Replace with your actual project ID

export PROJECT_ID="eastern-team-480811-e6"
export BUCKET_NAME="ai-interview-pdfs-${PROJECT_ID}"

echo "📦 Creating GCS bucket: ${BUCKET_NAME}"

# Create bucket
gsutil mb -p ${PROJECT_ID} -l asia-southeast1 gs://${BUCKET_NAME}

# Make bucket publicly readable (for PDF downloads)
echo "🔓 Making bucket publicly readable..."
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}

# Verify bucket was created
echo "✅ Verifying bucket creation..."
gsutil ls gs://${BUCKET_NAME}

echo ""
echo "✅ Bucket created successfully!"
echo "📝 Add this to your Cloud Run environment variables:"
echo "   GCS_BUCKET_NAME=${BUCKET_NAME}"

