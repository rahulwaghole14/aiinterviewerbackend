# How to Run Django Migrations on Google Cloud Run

## Overview
Since Cloud Run containers are stateless and ephemeral, you need to run migrations before deploying or as part of the startup process. Here are several methods:

---

## Method 1: Run Migrations via Cloud Run Jobs (Recommended)

Cloud Run Jobs allow you to run one-time tasks like migrations.

### Step 1: Create a Migration Job

```bash
# Set your project and region
PROJECT_ID="eastern-team-480811-e6"
REGION="asia-southeast1"
SERVICE_NAME="talaroai"
IMAGE_NAME="asia-southeast1-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/aiinterviewerbackend/talaroai:latest"

# Create a Cloud Run Job for migrations
gcloud run jobs create run-migrations \
  --image=${IMAGE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --set-env-vars="DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY},DATABASE_URL=${DATABASE_URL},USE_POSTGRESQL=True" \
  --add-cloudsql-instances=${CLOUD_SQL_CONNECTION_NAME} \
  --command="python" \
  --args="manage.py,migrate" \
  --max-retries=1 \
  --task-timeout=600
```

### Step 2: Execute the Migration Job

```bash
# Run the migration job
gcloud run jobs execute run-migrations \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --wait
```

### Step 3: Check Job Logs

```bash
# View job execution logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=run-migrations" \
  --limit=50 \
  --project=${PROJECT_ID} \
  --format=json
```

---

## Method 2: Run Migrations via Cloud Shell (Quick Method)

### Step 1: Connect to Cloud Shell

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the Cloud Shell icon (top right)
3. Or use: https://shell.cloud.google.com/

### Step 2: Clone Your Repository

```bash
# Clone your backend repository
git clone https://github.com/rahulwaghole14/aiinterviewerbackend.git
cd aiinterviewerbackend
```

### Step 3: Set Environment Variables

```bash
# Set your project
gcloud config set project eastern-team-480811-e6

# Set environment variables (get from Cloud Run service)
export DATABASE_URL="your-database-url"
export DJANGO_SECRET_KEY="your-secret-key"
export USE_POSTGRESQL="True"
export GCS_BUCKET_NAME="ai-interview-pdfs-eastern-team-480811-e6"
```

### Step 4: Install Dependencies and Run Migrations

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Run specific migration
python manage.py migrate evaluation 0007_clean_malformed_proctoring_pdf_urls_v2
```

**Note:** This method requires installing dependencies locally in Cloud Shell, which may take time.

---

## Method 3: Add Migrations to Startup Script (Automatic)

### Step 1: Create/Update `start.sh` Script

Create a `start.sh` file in your backend root:

```bash
#!/bin/bash
set -e

echo "Starting Django application..."

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (if needed)
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn your_project.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 2 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile -
```

### Step 2: Update Dockerfile

```dockerfile
# ... existing Dockerfile content ...

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Use startup script
CMD ["/app/start.sh"]
```

### Step 3: Deploy

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/${PROJECT_ID}/talaroai:latest
gcloud run deploy talaroai \
  --image gcr.io/${PROJECT_ID}/talaroai:latest \
  --region ${REGION} \
  --platform managed
```

**Pros:** Migrations run automatically on every deployment
**Cons:** Slows down startup time, migrations run even if not needed

---

## Method 4: Run Migrations via Cloud Build (CI/CD)

### Step 1: Create `cloudbuild-migrate.yaml`

```yaml
steps:
  # Step 1: Build the image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - '${_IMAGE_NAME}'
      - '.'
    id: 'build-image'

  # Step 2: Push the image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '${_IMAGE_NAME}'
    id: 'push-image'
    waitFor: ['build-image']

  # Step 3: Run migrations
  - name: '${_IMAGE_NAME}'
    entrypoint: 'python'
    args:
      - 'manage.py'
      - 'migrate'
      - '--noinput'
    env:
      - 'DATABASE_URL=${_DATABASE_URL}'
      - 'DJANGO_SECRET_KEY=${_DJANGO_SECRET_KEY}'
      - 'USE_POSTGRESQL=True'
    id: 'run-migrations'
    waitFor: ['push-image']

  # Step 4: Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
    entrypoint: 'gcloud'
    args:
      - 'run'
      - 'deploy'
      - '${_SERVICE_NAME}'
      - '--image'
      - '${_IMAGE_NAME}'
      - '--region'
      - '${_REGION}'
      - '--platform'
      - 'managed'
    id: 'deploy-cloud-run'
    waitFor: ['run-migrations']

substitutions:
  _SERVICE_NAME: 'talaroai'
  _REGION: 'asia-southeast1'
  _IMAGE_NAME: 'asia-southeast1-docker.pkg.dev/eastern-team-480811-e6/cloud-run-source-deploy/aiinterviewerbackend/talaroai:latest'
  _DATABASE_URL: 'your-database-url'
  _DJANGO_SECRET_KEY: 'your-secret-key'

options:
  machineType: 'E2_HIGHCPU_8'
  timeout: '1200s'
```

### Step 2: Run Cloud Build

```bash
gcloud builds submit --config cloudbuild-migrate.yaml
```

---

## Method 5: Run Migrations via Cloud Run Exec (Direct Container Access)

### Step 1: Get Cloud Run Service Details

```bash
# Get service name and region
SERVICE_NAME="talaroai"
REGION="asia-southeast1"
PROJECT_ID="eastern-team-480811-e6"
```

### Step 2: Execute Migration Command Directly

```bash
# Run migration command in Cloud Run container
gcloud run services update ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --command="python" \
  --args="manage.py,migrate" \
  --no-traffic
```

**Note:** This method may not work if your Cloud Run service doesn't support custom commands.

---

## Method 6: Use Cloud SQL Proxy (Local Development)

### Step 1: Install Cloud SQL Proxy

```bash
# Download Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.windows.amd64

# Make executable
chmod +x cloud-sql-proxy
```

### Step 2: Start Cloud SQL Proxy

```bash
# Start proxy (replace with your connection name)
./cloud-sql-proxy ${CLOUD_SQL_CONNECTION_NAME}
```

### Step 3: Run Migrations Locally

```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@127.0.0.1:5432/dbname"
export USE_POSTGRESQL="True"

# Run migrations
python manage.py migrate
```

---

## Recommended Approach for Your Project

Based on your setup, I recommend **Method 1 (Cloud Run Jobs)** for one-time migrations:

### Quick Migration Command

```bash
# Set variables
PROJECT_ID="eastern-team-480811-e6"
REGION="asia-southeast1"
SERVICE_NAME="talaroai"
IMAGE_NAME="asia-southeast1-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/aiinterviewerbackend/talaroai:latest"

# Get Cloud SQL connection name
CLOUD_SQL_CONNECTION_NAME=$(gcloud sql instances describe ai-interviewer-db1 \
  --project=${PROJECT_ID} \
  --format="value(connectionName)")

# Get environment variables from Cloud Run service
ENV_VARS=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format="value(spec.template.spec.containers[0].env)")

# Create and run migration job
gcloud run jobs create run-migrations \
  --image=${IMAGE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --set-env-vars="${ENV_VARS}" \
  --add-cloudsql-instances=${CLOUD_SQL_CONNECTION_NAME} \
  --command="python" \
  --args="manage.py,migrate" \
  --max-retries=1 \
  --task-timeout=600 \
  --wait
```

---

## Running Specific Migration

To run a specific migration (like cleaning proctoring PDF URLs):

```bash
# Create job for specific migration
gcloud run jobs create run-specific-migration \
  --image=${IMAGE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --set-env-vars="${ENV_VARS}" \
  --add-cloudsql-instances=${CLOUD_SQL_CONNECTION_NAME} \
  --command="python" \
  --args="manage.py,migrate,evaluation,0007_clean_malformed_proctoring_pdf_urls_v2" \
  --max-retries=1 \
  --task-timeout=600

# Execute the job
gcloud run jobs execute run-specific-migration \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --wait
```

---

## Troubleshooting

### Issue: Migration fails with "connection refused"
**Solution:** Ensure Cloud SQL connection name is correct and Cloud SQL Proxy is configured.

### Issue: Migration times out
**Solution:** Increase `--task-timeout` value (default is 3600 seconds).

### Issue: Environment variables not available
**Solution:** Get env vars from Cloud Run service:
```bash
gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --format="get(spec.template.spec.containers[0].env)"
```

### Issue: Migration already applied
**Solution:** Check migration status:
```bash
# In Cloud Shell or local environment
python manage.py showmigrations evaluation
```

---

## Best Practices

1. **Always backup database** before running migrations
2. **Test migrations locally** first using Cloud SQL Proxy
3. **Run migrations during low-traffic periods**
4. **Monitor migration logs** for errors
5. **Use Cloud Run Jobs** for one-time migrations
6. **Add migrations to startup script** only if needed for every deployment

---

## Quick Reference

```bash
# Run all migrations
python manage.py migrate

# Run specific app migrations
python manage.py migrate evaluation

# Run specific migration
python manage.py migrate evaluation 0007_clean_malformed_proctoring_pdf_urls_v2

# Check migration status
python manage.py showmigrations

# Rollback migration
python manage.py migrate evaluation 0006_clean_malformed_proctoring_pdf_urls
```

