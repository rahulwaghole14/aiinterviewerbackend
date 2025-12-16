# 🚀 Step-by-Step Frontend Deployment Guide

Complete guide to deploy your React frontend to Google Cloud Storage.

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Google Cloud Platform account (with billing enabled)
- [ ] Google Cloud SDK (gcloud) installed
- [ ] Node.js 18+ installed
- [ ] npm installed
- [ ] Git installed (for Git Bash on Windows)

---

## Step 1: Install Google Cloud SDK (If Not Installed)

### Windows:

1. **Download Installer**:
   - Visit: https://cloud.google.com/sdk/docs/install
   - Click "Download for Windows"
   - Or direct: https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe

2. **Run Installer**:
   - Double-click `GoogleCloudSDKInstaller.exe`
   - ✅ Check "Add to PATH"
   - ✅ Check "Run gcloud init"
   - Complete installation

3. **Restart Terminal**:
   - Close all terminal windows
   - Open new Command Prompt or PowerShell

4. **Verify Installation**:
   ```cmd
   gcloud --version
   ```
   Should show version numbers (e.g., `Google Cloud SDK 450.0.0`)

**If you see "gcloud is not recognized"**: See `INSTALL_GCLOUD_WINDOWS.md` for troubleshooting.

---

## Step 2: Authenticate with Google Cloud

### 2.1 Login to Google Cloud

**In Command Prompt/PowerShell/Git Bash**:
```cmd
gcloud auth login
```

This will:
- Open your default browser
- Ask you to sign in with your Google account
- Request permissions
- Return to terminal when done

### 2.2 Set Application Default Credentials

```cmd
gcloud auth application-default login
```

This allows applications to use your credentials automatically.

---

## Step 3: Create or Select GCP Project

### 3.1 List Existing Projects

```cmd
gcloud projects list
```

### 3.2 Create New Project (If Needed)

```cmd
gcloud projects create YOUR_PROJECT_ID --name="AI Interview Portal"
```

Replace `YOUR_PROJECT_ID` with your desired project ID (must be globally unique).

### 3.3 Set Active Project

```cmd
gcloud config set project YOUR_PROJECT_ID
```

Replace `YOUR_PROJECT_ID` with your actual project ID.

### 3.4 Verify Project

```cmd
gcloud config get-value project
```

Should display your project ID.

---

## Step 4: Enable Required APIs

Enable the necessary Google Cloud APIs:

```cmd
gcloud services enable cloudbuild.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable storage-component.googleapis.com
```

Wait for each to complete (may take 1-2 minutes).

---

## Step 5: Create Google Cloud Storage Bucket

### 5.1 Set Variables

**In Command Prompt**:
```cmd
set PROJECT_ID=your-project-id
set BUCKET_NAME=ai-interviewer-frontend
set REGION=us-central1
```

**In PowerShell**:
```powershell
$env:PROJECT_ID = "your-project-id"
$env:BUCKET_NAME = "ai-interviewer-frontend"
$env:REGION = "us-central1"
```

**In Git Bash**:
```bash
export PROJECT_ID=your-project-id
export BUCKET_NAME=ai-interviewer-frontend
export REGION=us-central1
```

**Replace `your-project-id` with your actual GCP project ID!**

### 5.2 Create Bucket

```cmd
gsutil mb -p %PROJECT_ID% -c STANDARD -l %REGION% gs://%BUCKET_NAME%
```

**PowerShell**:
```powershell
gsutil mb -p $env:PROJECT_ID -c STANDARD -l $env:REGION "gs://$env:BUCKET_NAME"
```

**Git Bash**:
```bash
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME
```

**Expected Output**: `Creating gs://ai-interviewer-frontend/...`

### 5.3 Configure Bucket for Static Website Hosting

```cmd
gsutil web set -m index.html -e index.html gs://%BUCKET_NAME%
```

**PowerShell**:
```powershell
gsutil web set -m index.html -e index.html "gs://$env:BUCKET_NAME"
```

**Git Bash**:
```bash
gsutil web set -m index.html -e index.html gs://$BUCKET_NAME
```

### 5.4 Set Public Read Permissions

```cmd
gsutil iam ch allUsers:objectViewer gs://%BUCKET_NAME%
```

**PowerShell**:
```powershell
gsutil iam ch allUsers:objectViewer "gs://$env:BUCKET_NAME"
```

**Git Bash**:
```bash
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
```

---

## Step 6: Get Backend URL

You need your backend API URL to configure the frontend.

### Option A: If Backend is Already Deployed

```cmd
# Get backend URL (replace with your backend service name)
gcloud run services describe YOUR_BACKEND_SERVICE_NAME --region us-central1 --format 'value(status.url)'
```

### Option B: If Using Existing Backend

Use your existing backend URL, e.g.:
- `https://aiinterviewerbackend-2.onrender.com`
- `https://your-backend-service.run.app`

**Set Backend URL Variable**:

**Command Prompt**:
```cmd
set BACKEND_URL=https://your-backend-service.run.app
```

**PowerShell**:
```powershell
$env:BACKEND_URL = "https://your-backend-service.run.app"
```

**Git Bash**:
```bash
export BACKEND_URL=https://your-backend-service.run.app
```

---

## Step 7: Build Frontend

### 7.1 Navigate to Frontend Directory

```cmd
cd frontend
```

### 7.2 Install Dependencies (First Time Only)

```cmd
npm install
```

This may take 2-5 minutes. Wait for completion.

### 7.3 Build Frontend

**Command Prompt**:
```cmd
set VITE_API_URL=%BACKEND_URL%
npm run build
```

**PowerShell**:
```powershell
$env:VITE_API_URL = $env:BACKEND_URL
npm run build
```

**Git Bash**:
```bash
export VITE_API_URL=$BACKEND_URL
npm run build
```

**Expected Output**:
```
vite v7.x.x building for production...
✓ built in X.XXs
```

### 7.4 Verify Build Output

```cmd
dir dist
```

You should see:
- `index.html`
- `assets/` folder
- Other static files (favicon, etc.)

---

## Step 8: Deploy to Google Cloud Storage

### 8.1 Navigate Back to Project Root

```cmd
cd ..
```

### 8.2 Upload Files to GCS

**Command Prompt**:
```cmd
gsutil -m cp -r frontend\dist\* gs://%BUCKET_NAME%\
```

**PowerShell**:
```powershell
gsutil -m cp -r frontend/dist/* "gs://$env:BUCKET_NAME/"
```

**Git Bash**:
```bash
gsutil -m cp -r frontend/dist/* gs://$BUCKET_NAME/
```

**Expected Output**: Shows upload progress for each file.

### 8.3 Set Correct Content Types

**Command Prompt**:
```cmd
gsutil -m setmeta -h "Content-Type:text/html" gs://%BUCKET_NAME%\*.html
gsutil -m setmeta -h "Content-Type:application/javascript" gs://%BUCKET_NAME%\assets\*.js
gsutil -m setmeta -h "Content-Type:text/css" gs://%BUCKET_NAME%\assets\*.css
```

**PowerShell**:
```powershell
gsutil -m setmeta -h "Content-Type:text/html" "gs://$env:BUCKET_NAME/*.html"
gsutil -m setmeta -h "Content-Type:application/javascript" "gs://$env:BUCKET_NAME/assets/*.js"
gsutil -m setmeta -h "Content-Type:text/css" "gs://$env:BUCKET_NAME/assets/*.css"
```

**Git Bash**:
```bash
gsutil -m setmeta -h "Content-Type:text/html" gs://$BUCKET_NAME/*.html
gsutil -m setmeta -h "Content-Type:application/javascript" gs://$BUCKET_NAME/assets/*.js
gsutil -m setmeta -h "Content-Type:text/css" gs://$BUCKET_NAME/assets/*.css
```

---

## Step 9: Verify Deployment

### 9.1 Get Frontend URL

Your frontend is now available at:

```
https://storage.googleapis.com/YOUR_BUCKET_NAME/index.html
```

Replace `YOUR_BUCKET_NAME` with your actual bucket name.

### 9.2 Test in Browser

1. Open browser
2. Navigate to: `https://storage.googleapis.com/ai-interviewer-frontend/index.html`
3. Verify the page loads correctly
4. Check browser console for any errors

### 9.3 Verify Files Are Uploaded

```cmd
gsutil ls -r gs://%BUCKET_NAME%
```

**PowerShell**:
```powershell
gsutil ls -r "gs://$env:BUCKET_NAME"
```

**Git Bash**:
```bash
gsutil ls -r gs://$BUCKET_NAME
```

Should list all uploaded files.

---

## Step 10: Update Frontend After Code Changes

When you make changes to frontend code:

### 10.1 Rebuild

```cmd
cd frontend
set VITE_API_URL=%BACKEND_URL%
npm run build
cd ..
```

### 10.2 Redeploy

```cmd
gsutil -m cp -r frontend\dist\* gs://%BUCKET_NAME%\
```

That's it! Your changes are live.

---

## 🎯 Quick Reference: All Commands Together

**For Command Prompt** (copy-paste ready):

```cmd
REM Step 1: Set variables
set PROJECT_ID=your-project-id
set BUCKET_NAME=ai-interviewer-frontend
set REGION=us-central1
set BACKEND_URL=https://your-backend-service.run.app

REM Step 2: Authenticate
gcloud auth login
gcloud auth application-default login

REM Step 3: Set project
gcloud config set project %PROJECT_ID%

REM Step 4: Enable APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable storage-api.googleapis.com

REM Step 5: Create bucket
gsutil mb -p %PROJECT_ID% -c STANDARD -l %REGION% gs://%BUCKET_NAME%
gsutil web set -m index.html -e index.html gs://%BUCKET_NAME%
gsutil iam ch allUsers:objectViewer gs://%BUCKET_NAME%

REM Step 6: Build frontend
cd frontend
set VITE_API_URL=%BACKEND_URL%
npm install
npm run build
cd ..

REM Step 7: Deploy
gsutil -m cp -r frontend\dist\* gs://%BUCKET_NAME%\
gsutil -m setmeta -h "Content-Type:text/html" gs://%BUCKET_NAME%\*.html

REM Step 8: Verify
echo Frontend URL: https://storage.googleapis.com/%BUCKET_NAME%/index.html
```

**For PowerShell** (copy-paste ready):

```powershell
# Step 1: Set variables
$env:PROJECT_ID = "your-project-id"
$env:BUCKET_NAME = "ai-interviewer-frontend"
$env:REGION = "us-central1"
$env:BACKEND_URL = "https://your-backend-service.run.app"

# Step 2: Authenticate
gcloud auth login
gcloud auth application-default login

# Step 3: Set project
gcloud config set project $env:PROJECT_ID

# Step 4: Enable APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable storage-api.googleapis.com

# Step 5: Create bucket
gsutil mb -p $env:PROJECT_ID -c STANDARD -l $env:REGION "gs://$env:BUCKET_NAME"
gsutil web set -m index.html -e index.html "gs://$env:BUCKET_NAME"
gsutil iam ch allUsers:objectViewer "gs://$env:BUCKET_NAME"

# Step 6: Build frontend
cd frontend
$env:VITE_API_URL = $env:BACKEND_URL
npm install
npm run build
cd ..

# Step 7: Deploy
gsutil -m cp -r frontend/dist/* "gs://$env:BUCKET_NAME/"
gsutil -m setmeta -h "Content-Type:text/html" "gs://$env:BUCKET_NAME/*.html"

# Step 8: Verify
Write-Host "Frontend URL: https://storage.googleapis.com/$env:BUCKET_NAME/index.html"
```

**For Git Bash** (copy-paste ready):

```bash
# Step 1: Set variables
export PROJECT_ID=your-project-id
export BUCKET_NAME=ai-interviewer-frontend
export REGION=us-central1
export BACKEND_URL=https://your-backend-service.run.app

# Step 2: Authenticate
gcloud auth login
gcloud auth application-default login

# Step 3: Set project
gcloud config set project $PROJECT_ID

# Step 4: Enable APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable storage-api.googleapis.com

# Step 5: Create bucket
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME
gsutil web set -m index.html -e index.html gs://$BUCKET_NAME
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME

# Step 6: Build frontend
cd frontend
export VITE_API_URL=$BACKEND_URL
npm install
npm run build
cd ..

# Step 7: Deploy
gsutil -m cp -r frontend/dist/* gs://$BUCKET_NAME/
gsutil -m setmeta -h "Content-Type:text/html" gs://$BUCKET_NAME/*.html

# Step 8: Verify
echo "Frontend URL: https://storage.googleapis.com/$BUCKET_NAME/index.html"
```

---

## 🐛 Troubleshooting

### Issue: "gsutil: command not found"

**Solution**: Install Google Cloud SDK (see Step 1)

### Issue: "Access Denied" when creating bucket

**Solution**: 
- Verify you're logged in: `gcloud auth list`
- Check project permissions
- Ensure billing is enabled

### Issue: "Bucket name already exists"

**Solution**: 
- Use a different bucket name
- Or delete existing bucket: `gsutil rm -r gs://BUCKET_NAME`

### Issue: Frontend shows blank page

**Solution**:
- Check browser console for errors
- Verify `index.html` exists: `gsutil ls gs://BUCKET_NAME/index.html`
- Check CORS settings if API calls fail

### Issue: "npm: command not found"

**Solution**: Install Node.js from https://nodejs.org/

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Frontend URL loads in browser
- [ ] No console errors
- [ ] API calls work (check Network tab)
- [ ] All assets load (images, CSS, JS)
- [ ] Login/authentication works

---

## 📚 Next Steps

1. **Set up Cloud CDN** (optional, for better performance)
2. **Configure custom domain** (optional)
3. **Set up automated deployment** using Cloud Build triggers
4. **Monitor usage** in GCP Console

---

## 🆘 Need Help?

- Check `DEPLOYMENT_GUIDE.md` for detailed information
- Review `WHERE_TO_RUN_COMMANDS.md` for terminal guidance
- See `INSTALL_GCLOUD_WINDOWS.md` for gcloud installation help

---

**Last Updated**: 2025-01-27

