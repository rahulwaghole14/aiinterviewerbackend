# 🚀 Deploy Frontend Using GitHub Repository - Step-by-Step Guide

Complete guide to set up automated frontend deployment from GitHub to Google Cloud Storage.

---

## 📋 Overview

This guide covers two methods:
1. **Google Cloud Build Triggers** (Recommended) - Automated builds on push
2. **GitHub Actions** (Alternative) - CI/CD directly from GitHub

---

## 🎯 Method 1: Google Cloud Build Triggers (Recommended)

### Step 1: Prepare GitHub Repository

#### 1.1 Create GitHub Repository (If Not Exists)

1. Go to https://github.com/new
2. Repository name: `ai-interviewer-frontend` (or your choice)
3. Choose **Public** or **Private**
4. ✅ Check "Add a README file"
5. Click **Create repository**

#### 1.2 Push Your Frontend Code

**If repository is new**:
```bash
cd frontend
git init
git add .
git commit -m "Initial commit: Frontend code"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-interviewer-frontend.git
git push -u origin main
```

**If repository already exists**:
```bash
cd frontend
git add .
git commit -m "Add frontend code"
git push origin main
```

---

### Step 2: Connect GitHub to Google Cloud

#### 2.1 Install GitHub App (First Time Only)

1. Go to [Cloud Build Console](https://console.cloud.google.com/cloud-build)
2. Click **Triggers** → **Connect Repository**
3. Select **GitHub (Cloud Build GitHub App)**
4. Click **Install GitHub App**
5. Select your GitHub account
6. Choose repositories:
   - **Only select repositories** → Choose `ai-interviewer-frontend`
   - Or **All repositories** (if you trust GCP)
7. Click **Install**

#### 2.2 Authorize Cloud Build

1. After installation, you'll be redirected back to GCP
2. Select your GitHub account
3. Select repository: `ai-interviewer-frontend`
4. Click **Connect**

---

### Step 3: Create Cloud Build Trigger

#### 3.1 Create New Trigger

1. In Cloud Build Console, click **Create Trigger**
2. Fill in details:

   **Name**: `deploy-frontend`
   
   **Event**: **Push to a branch**
   
   **Source**: Select your connected repository
   
   **Branch**: `^main$` (or your main branch name)
   
   **Configuration**: **Cloud Build configuration file (yaml or json)**
   
   **Location**: `frontend/cloudbuild-frontend.yaml`

#### 3.2 Add Substitutions

Click **Substitution variables** → **Add variable**:

**Variable 1**:
- **Name**: `_GCS_BUCKET_NAME`
- **Value**: `ai-interviewer-frontend`

**Variable 2**:
- **Name**: `_BACKEND_URL`
- **Value**: `https://your-backend-service.run.app`

**Replace `your-backend-service.run.app` with your actual backend URL!**

#### 3.3 Advanced Settings (Optional)

- **Service account**: Leave default
- **Timeout**: `600s` (10 minutes)
- **Machine type**: `E2_HIGHCPU_8` (for faster builds)

#### 3.4 Create Trigger

Click **Create** button.

---

### Step 4: Grant Cloud Build Permissions

#### 4.1 Get Project Number

```bash
gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)"
```

Copy the project number (e.g., `123456789012`).

#### 4.2 Grant Storage Admin Role

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.admin"
```

**Replace**:
- `YOUR_PROJECT_ID` with your project ID
- `PROJECT_NUMBER` with the number from Step 4.1

**Example**:
```bash
gcloud projects add-iam-policy-binding my-project-123 \
  --member="serviceAccount:123456789012@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.admin"
```

---

### Step 5: Create GCS Bucket (If Not Exists)

```bash
# Set variables
export PROJECT_ID=your-project-id
export BUCKET_NAME=ai-interviewer-frontend
export REGION=us-central1

# Create bucket
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME

# Configure for static website hosting
gsutil web set -m index.html -e index.html gs://$BUCKET_NAME

# Set public permissions
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
```

**For Windows Command Prompt**:
```cmd
set PROJECT_ID=your-project-id
set BUCKET_NAME=ai-interviewer-frontend
set REGION=us-central1

gsutil mb -p %PROJECT_ID% -c STANDARD -l %REGION% gs://%BUCKET_NAME%
gsutil web set -m index.html -e index.html gs://%BUCKET_NAME%
gsutil iam ch allUsers:objectViewer gs://%BUCKET_NAME%
```

---

### Step 6: Verify cloudbuild-frontend.yaml Exists

Ensure `frontend/cloudbuild-frontend.yaml` exists in your repository:

```bash
# Check if file exists
ls frontend/cloudbuild-frontend.yaml

# If not, create it (see below)
```

The file should be at: `frontend/cloudbuild-frontend.yaml`

---

### Step 7: Test the Trigger

#### 7.1 Make a Small Change

```bash
cd frontend
# Make any small change (e.g., update a comment)
echo "# Updated" >> README.md
git add .
git commit -m "Test deployment trigger"
git push origin main
```

#### 7.2 Monitor Build

1. Go to [Cloud Build Console](https://console.cloud.google.com/cloud-build)
2. Click **History**
3. You should see a new build running
4. Click on the build to see logs in real-time

#### 7.3 Verify Deployment

After build completes (5-10 minutes):
- Check build logs for success
- Visit: `https://storage.googleapis.com/ai-interviewer-frontend/index.html`
- Verify frontend loads correctly

---

## 🎯 Method 2: GitHub Actions (Alternative)

### Step 1: Create GitHub Actions Workflow

#### 1.1 Create Workflow Directory

```bash
mkdir -p frontend/.github/workflows
```

#### 1.2 Create Workflow File

Create `frontend/.github/workflows/deploy.yml`:

```yaml
name: Deploy Frontend to GCS

on:
  push:
    branches:
      - main
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci
      
      - name: Build frontend
        working-directory: ./frontend
        env:
          VITE_API_URL: ${{ secrets.BACKEND_URL }}
        run: npm run build
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2
      
      - name: Upload to GCS
        run: |
          gsutil -m cp -r frontend/dist/* gs://${{ secrets.GCS_BUCKET_NAME }}/
          gsutil -m setmeta -h "Content-Type:text/html" gs://${{ secrets.GCS_BUCKET_NAME }}/*.html
          gsutil -m setmeta -h "Content-Type:application/javascript" gs://${{ secrets.GCS_BUCKET_NAME }}/assets/*.js
          gsutil -m setmeta -h "Content-Type:text/css" gs://${{ secrets.GCS_BUCKET_NAME }}/assets/*.css
```

---

### Step 2: Create Service Account for GitHub Actions

#### 2.1 Create Service Account

```bash
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions Service Account" \
  --project=YOUR_PROJECT_ID
```

#### 2.2 Grant Storage Admin Role

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

#### 2.3 Create and Download Key

```bash
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

**⚠️ Keep this key secure!**

---

### Step 3: Add GitHub Secrets

#### 3.1 Go to Repository Settings

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**

#### 3.2 Add Secrets

Click **New repository secret** for each:

**Secret 1: GCP_SA_KEY**
- **Name**: `GCP_SA_KEY`
- **Value**: Contents of `github-actions-key.json` (entire JSON file)

**Secret 2: GCS_BUCKET_NAME**
- **Name**: `GCS_BUCKET_NAME`
- **Value**: `ai-interviewer-frontend`

**Secret 3: BACKEND_URL**
- **Name**: `BACKEND_URL`
- **Value**: `https://your-backend-service.run.app`

**Secret 4: GCP_PROJECT_ID** (Optional)
- **Name**: `GCP_PROJECT_ID`
- **Value**: Your GCP project ID

---

### Step 4: Commit and Push Workflow

```bash
cd frontend
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions deployment workflow"
git push origin main
```

---

### Step 5: Monitor GitHub Actions

1. Go to your GitHub repository
2. Click **Actions** tab
3. You should see workflow running
4. Click on the workflow run to see logs

---

## 🔄 Automated Deployment Workflow

### How It Works

**Cloud Build Trigger**:
```
GitHub Push → Cloud Build Trigger → Build Frontend → Deploy to GCS → Frontend Live
```

**GitHub Actions**:
```
GitHub Push → GitHub Actions → Build Frontend → Deploy to GCS → Frontend Live
```

### Typical Workflow

1. **Developer makes changes**:
   ```bash
   cd frontend
   # Make code changes
   git add .
   git commit -m "Update frontend"
   git push origin main
   ```

2. **Automated build starts** (within seconds)

3. **Build completes** (5-10 minutes)

4. **Frontend is live** at GCS URL

---

## 📝 Configuration Files

### cloudbuild-frontend.yaml Location

Ensure this file exists in your repository:
```
frontend/
  ├── cloudbuild-frontend.yaml  ← Must be here
  ├── package.json
  ├── vite.config.js
  └── ...
```

### Required Substitutions

For Cloud Build Trigger, ensure these substitutions are set:

| Variable | Description | Example |
|----------|-------------|---------|
| `_GCS_BUCKET_NAME` | GCS bucket name | `ai-interviewer-frontend` |
| `_BACKEND_URL` | Backend API URL | `https://backend.run.app` |

---

## 🐛 Troubleshooting

### Issue: Trigger Not Firing

**Solution**:
1. Check branch name matches trigger pattern
2. Verify repository is connected
3. Check Cloud Build API is enabled
4. Review trigger logs

### Issue: Build Fails - "Permission Denied"

**Solution**:
```bash
# Grant Storage Admin role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.admin"
```

### Issue: Build Fails - "Bucket Not Found"

**Solution**: Create bucket first (see Step 5)

### Issue: GitHub Actions - "Invalid credentials"

**Solution**:
- Verify `GCP_SA_KEY` secret is correct JSON
- Check service account has correct permissions
- Regenerate key if needed

### Issue: Files Not Uploading

**Solution**:
- Check build logs for errors
- Verify bucket name is correct
- Check gsutil commands in build logs

---

## ✅ Verification Checklist

After setup:

- [ ] GitHub repository connected to Cloud Build
- [ ] Trigger created and active
- [ ] Substitutions configured correctly
- [ ] Cloud Build has Storage Admin permissions
- [ ] GCS bucket exists and configured
- [ ] Test push triggers build successfully
- [ ] Frontend deploys to GCS
- [ ] Frontend URL loads correctly

---

## 🔐 Security Best Practices

1. **Use Secrets**: Never hardcode API keys or credentials
2. **Limit Permissions**: Grant only necessary roles
3. **Private Repos**: Use private repositories for sensitive code
4. **Review Builds**: Monitor build logs regularly
5. **Rotate Keys**: Periodically rotate service account keys

---

## 📊 Monitoring

### View Build History

**Cloud Build**:
- Go to: https://console.cloud.google.com/cloud-build
- Click **History** to see all builds

**GitHub Actions**:
- Go to repository → **Actions** tab
- View workflow runs and logs

### Set Up Notifications

**Cloud Build**:
1. Go to Cloud Build Settings
2. Configure email notifications
3. Set up Pub/Sub for programmatic notifications

**GitHub Actions**:
- Configure email notifications in GitHub Settings
- Use GitHub Actions status badges

---

## 🎯 Quick Reference Commands

### Create Trigger via CLI

```bash
gcloud builds triggers create github \
  --repo-name=ai-interviewer-frontend \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern="^main$" \
  --build-config=frontend/cloudbuild-frontend.yaml \
  --substitutions=_GCS_BUCKET_NAME=ai-interviewer-frontend,_BACKEND_URL=https://your-backend.run.app \
  --name=deploy-frontend
```

### List Triggers

```bash
gcloud builds triggers list
```

### Test Trigger Manually

```bash
gcloud builds triggers run deploy-frontend --branch=main
```

### View Build Logs

```bash
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

---

## 📚 Related Documentation

- [Cloud Build Triggers](https://cloud.google.com/build/docs/triggers)
- [GitHub Actions](https://docs.github.com/en/actions)
- [GCS Static Website Hosting](https://cloud.google.com/storage/docs/hosting-static-website)

---

## 🆘 Need Help?

1. Check Cloud Build logs
2. Review GitHub Actions logs
3. Verify permissions and configurations
4. See `FRONTEND_DEPLOYMENT_STEPS.md` for manual deployment
5. See `DEPLOYMENT_GUIDE.md` for complete deployment guide

---

**Last Updated**: 2025-01-27

