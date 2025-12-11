# ✅ GitHub Deployment Setup Checklist

Quick checklist for setting up automated frontend deployment from GitHub.

---

## 🎯 Method 1: Cloud Build Trigger (Recommended)

### Pre-Setup
- [ ] Google Cloud account with billing enabled
- [ ] GitHub account
- [ ] Frontend code in GitHub repository
- [ ] `cloudbuild-frontend.yaml` exists in `frontend/` directory

### Step-by-Step Checklist

#### 1. GitHub Repository Setup
- [ ] Repository created on GitHub
- [ ] Frontend code pushed to repository
- [ ] `frontend/cloudbuild-frontend.yaml` committed

#### 2. Connect GitHub to GCP
- [ ] Go to Cloud Build Console
- [ ] Click "Connect Repository"
- [ ] Install GitHub App
- [ ] Select repository
- [ ] Authorize connection

#### 3. Create Cloud Build Trigger
- [ ] Click "Create Trigger"
- [ ] Name: `deploy-frontend`
- [ ] Event: Push to branch `main`
- [ ] Config file: `frontend/cloudbuild-frontend.yaml`
- [ ] Add substitution: `_GCS_BUCKET_NAME` = `ai-interviewer-frontend`
- [ ] Add substitution: `_BACKEND_URL` = `https://your-backend.run.app`
- [ ] Create trigger

#### 4. Grant Permissions
- [ ] Get project number: `gcloud projects describe PROJECT_ID --format="value(projectNumber)"`
- [ ] Grant Storage Admin role to Cloud Build service account
- [ ] Verify permissions

#### 5. Create GCS Bucket
- [ ] Create bucket: `gsutil mb -p PROJECT_ID -c STANDARD -l us-central1 gs://BUCKET_NAME`
- [ ] Configure website hosting: `gsutil web set -m index.html -e index.html gs://BUCKET_NAME`
- [ ] Set public permissions: `gsutil iam ch allUsers:objectViewer gs://BUCKET_NAME`

#### 6. Test Deployment
- [ ] Make small change to frontend code
- [ ] Commit and push to `main` branch
- [ ] Check Cloud Build console for running build
- [ ] Wait for build to complete (5-10 minutes)
- [ ] Verify frontend at: `https://storage.googleapis.com/BUCKET_NAME/index.html`

---

## 🎯 Method 2: GitHub Actions

### Pre-Setup
- [ ] Google Cloud account with billing enabled
- [ ] GitHub account
- [ ] Frontend code in GitHub repository
- [ ] Service account created in GCP

### Step-by-Step Checklist

#### 1. Create Service Account
- [ ] Create service account: `gcloud iam service-accounts create github-actions-sa`
- [ ] Grant Storage Admin role
- [ ] Create and download JSON key

#### 2. Add GitHub Secrets
- [ ] Go to repository Settings → Secrets → Actions
- [ ] Add secret: `GCP_SA_KEY` (service account JSON)
- [ ] Add secret: `GCS_BUCKET_NAME` (bucket name)
- [ ] Add secret: `BACKEND_URL` (backend API URL)
- [ ] Add secret: `GCP_PROJECT_ID` (project ID)

#### 3. Create Workflow File
- [ ] Create `.github/workflows/deploy.yml` in frontend directory
- [ ] Copy workflow content from guide
- [ ] Commit and push to repository

#### 4. Create GCS Bucket
- [ ] Create bucket: `gsutil mb -p PROJECT_ID -c STANDARD -l us-central1 gs://BUCKET_NAME`
- [ ] Configure website hosting
- [ ] Set public permissions

#### 5. Test Deployment
- [ ] Make small change to frontend code
- [ ] Commit and push to `main` branch
- [ ] Check GitHub Actions tab
- [ ] Wait for workflow to complete
- [ ] Verify frontend deployment

---

## 🔧 Required Commands Summary

### Cloud Build Method

```bash
# 1. Connect repository (via UI)

# 2. Grant permissions
PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.admin"

# 3. Create bucket
gsutil mb -p PROJECT_ID -c STANDARD -l us-central1 gs://BUCKET_NAME
gsutil web set -m index.html -e index.html gs://BUCKET_NAME
gsutil iam ch allUsers:objectViewer gs://BUCKET_NAME
```

### GitHub Actions Method

```bash
# 1. Create service account
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions Service Account"

# 2. Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:github-actions-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# 3. Create key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-sa@PROJECT_ID.iam.gserviceaccount.com

# 4. Add key to GitHub Secrets (via UI)

# 5. Create bucket
gsutil mb -p PROJECT_ID -c STANDARD -l us-central1 gs://BUCKET_NAME
gsutil web set -m index.html -e index.html gs://BUCKET_NAME
gsutil iam ch allUsers:objectViewer gs://BUCKET_NAME
```

---

## 📝 Required Files

### For Cloud Build
```
frontend/
  └── cloudbuild-frontend.yaml  ← Must exist
```

### For GitHub Actions
```
frontend/
  └── .github/
      └── workflows/
          └── deploy.yml  ← Must exist
```

---

## 🐛 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Trigger not firing | Check branch name, verify repository connection |
| Permission denied | Grant Storage Admin role to Cloud Build service account |
| Bucket not found | Create bucket before first deployment |
| Build fails | Check build logs, verify substitutions are correct |
| GitHub Actions auth fails | Verify GCP_SA_KEY secret is valid JSON |

---

## ✅ Success Indicators

After setup, you should see:

- ✅ Push to `main` branch triggers build automatically
- ✅ Build completes successfully (green status)
- ✅ Frontend files uploaded to GCS bucket
- ✅ Frontend accessible at GCS URL
- ✅ No errors in build logs

---

## 📚 Documentation

- **Full Guide**: `FRONTEND_GITHUB_DEPLOYMENT.md`
- **Manual Deployment**: `FRONTEND_DEPLOYMENT_STEPS.md`
- **Complete Guide**: `DEPLOYMENT_GUIDE.md`

---

**Last Updated**: 2025-01-27

