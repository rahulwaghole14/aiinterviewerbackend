# 🖥️ Where to Run Deployment Commands

## 📍 Overview

This guide explains **where** and **how** to run the deployment commands for Windows, Linux, and macOS.

---

## 🪟 Windows Users

### Option 1: Git Bash (Recommended) ⭐

**Location**: Installed with Git for Windows

**How to Access**:
1. Right-click in your project folder → **"Git Bash Here"**
2. Or open Git Bash and navigate:
   ```bash
   cd "/c/Users/ADMIN/Downloads/ai interview portal (1)"
   ```

**Why Use Git Bash**:
- ✅ Supports bash scripts (`deploy-frontend.sh`, `deploy-backend.sh`)
- ✅ Unix-like commands (`ls`, `cd`, `chmod`)
- ✅ Works with `gcloud` CLI
- ✅ Path handling compatible with Windows

**Example**:
```bash
# In Git Bash
export GCP_PROJECT_ID=your-project-id
./deploy-backend.sh
```

---

### Option 2: Windows Subsystem for Linux (WSL) ⭐⭐

**Best for**: Full Linux compatibility

**Setup** (if not installed):
```powershell
# In PowerShell (as Administrator)
wsl --install
# Restart computer after installation
```

**How to Access**:
1. Open **WSL** or **Ubuntu** from Start Menu
2. Navigate to project:
   ```bash
   cd /mnt/c/Users/ADMIN/Downloads/ai\ interview\ portal\ \(1\)/
   ```

**Why Use WSL**:
- ✅ Full Linux environment
- ✅ Native bash support
- ✅ Better performance than Git Bash
- ✅ Can install Linux tools easily

**Example**:
```bash
# In WSL/Ubuntu terminal
export GCP_PROJECT_ID=your-project-id
chmod +x deploy-backend.sh
./deploy-backend.sh
```

---

### Option 3: PowerShell (For gcloud commands only)

**Location**: Built into Windows

**How to Access**:
- Press `Win + X` → **Windows PowerShell**
- Or search "PowerShell" in Start Menu

**Limitations**:
- ❌ Cannot run `.sh` bash scripts directly
- ✅ Can run `gcloud` commands
- ✅ Can run individual commands manually

**Example**:
```powershell
# In PowerShell
$env:GCP_PROJECT_ID = "your-project-id"
gcloud config set project $env:GCP_PROJECT_ID
gcloud builds submit --tag gcr.io/$env:GCP_PROJECT_ID/ai-interviewer-backend
```

**Note**: For bash scripts, use Git Bash or WSL instead.

---

### Option 4: Command Prompt (cmd)

**Location**: Built into Windows

**Limitations**:
- ❌ Cannot run bash scripts
- ✅ Can run `gcloud` commands
- ⚠️ Different syntax than bash

**Example**:
```cmd
REM In Command Prompt
set GCP_PROJECT_ID=your-project-id
gcloud config set project %GCP_PROJECT_ID%
```

---

## 🐧 Linux/macOS Users

### Terminal (Native)

**Location**: Built-in terminal application

**How to Access**:
- **Linux**: `Ctrl + Alt + T` or search "Terminal"
- **macOS**: `Cmd + Space` → type "Terminal"

**Example**:
```bash
# In Terminal
export GCP_PROJECT_ID=your-project-id
chmod +x deploy-backend.sh
./deploy-backend.sh
```

---

## 📂 Project Directory Structure

Your project is located at:
```
Windows: C:\Users\ADMIN\Downloads\ai interview portal (1)
Linux/WSL: /mnt/c/Users/ADMIN/Downloads/ai interview portal (1)
macOS: /Users/ADMIN/Downloads/ai interview portal (1)
```

---

## 🚀 Step-by-Step: Where to Run Each Command

### Step 1: Install gcloud CLI

**Windows (PowerShell)**:
```powershell
# Download from: https://cloud.google.com/sdk/docs/install
# Or use Chocolatey:
choco install gcloudsdk
```

**Linux/macOS (Terminal)**:
```bash
# Linux
curl https://sdk.cloud.google.com | bash

# macOS
brew install --cask google-cloud-sdk
```

---

### Step 2: Authenticate

**Where**: Any terminal (Git Bash, WSL, PowerShell, Terminal)

```bash
# In Git Bash, WSL, or Terminal
gcloud auth login
gcloud auth application-default login
```

**PowerShell**:
```powershell
gcloud auth login
gcloud auth application-default login
```

---

### Step 3: Run Deployment Scripts

**Where**: Git Bash or WSL (Windows) / Terminal (Linux/macOS)

```bash
# Navigate to project directory
cd "/c/Users/ADMIN/Downloads/ai interview portal (1)"  # Git Bash
# OR
cd "/mnt/c/Users/ADMIN/Downloads/ai interview portal (1)"  # WSL

# Make scripts executable (first time only)
chmod +x deploy-frontend.sh deploy-backend.sh setup-gcp-project.sh

# Run setup
./setup-gcp-project.sh

# Deploy backend
export GCP_PROJECT_ID=your-project-id
export SERVICE_NAME=ai-interviewer-backend
./deploy-backend.sh

# Deploy frontend
export GCS_BUCKET_NAME=ai-interviewer-frontend
export BACKEND_URL=https://your-backend-service.run.app
./deploy-frontend.sh
```

---

### Step 4: Run Individual gcloud Commands

**Where**: Any terminal (Git Bash, WSL, PowerShell, Terminal)

**Example - Build Docker Image**:
```bash
# Git Bash, WSL, Terminal
export PROJECT_ID=your-project-id
gcloud builds submit --tag gcr.io/$PROJECT_ID/ai-interviewer-backend
```

**PowerShell**:
```powershell
$env:PROJECT_ID = "your-project-id"
gcloud builds submit --tag "gcr.io/$env:PROJECT_ID/ai-interviewer-backend"
```

---

## 🔧 Windows-Specific Adaptations

### If Bash Scripts Don't Work

**Option A: Use Git Bash**
```bash
# Right-click folder → Git Bash Here
./deploy-backend.sh
```

**Option B: Use WSL**
```bash
# Open WSL, navigate to project
cd /mnt/c/Users/ADMIN/Downloads/ai\ interview\ portal\ \(1\)/
./deploy-backend.sh
```

**Option C: Run Commands Manually**

Instead of running `./deploy-backend.sh`, run each command individually:

**In PowerShell**:
```powershell
# Set variables
$env:GCP_PROJECT_ID = "your-project-id"
$env:SERVICE_NAME = "ai-interviewer-backend"
$env:GCP_REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$env:GCP_PROJECT_ID/$env:SERVICE_NAME"

# Build image
gcloud builds submit --tag $IMAGE_NAME

# Deploy
gcloud run deploy $env:SERVICE_NAME `
  --image $IMAGE_NAME `
  --platform managed `
  --region $env:GCP_REGION `
  --allow-unauthenticated
```

---

## 📝 Quick Reference: Which Terminal for What

| Task | Windows | Linux/macOS |
|------|---------|-------------|
| Run `.sh` scripts | Git Bash or WSL | Terminal |
| Run `gcloud` commands | PowerShell, Git Bash, WSL, or CMD | Terminal |
| Install gcloud CLI | PowerShell or Download | Terminal |
| Build frontend (`npm`) | Git Bash, WSL, or PowerShell | Terminal |
| Docker commands | PowerShell, Git Bash, or WSL | Terminal |

---

## ✅ Recommended Setup for Windows

1. **Install Git for Windows** (includes Git Bash)
   - Download: https://git-scm.com/download/win

2. **Install gcloud CLI**
   - Download: https://cloud.google.com/sdk/docs/install

3. **Use Git Bash for deployment**
   - Right-click project folder → **Git Bash Here**
   - Run all commands there

---

## 🎯 Example: Complete Windows Workflow

### Using Git Bash:

```bash
# 1. Open Git Bash in project folder
# Right-click → Git Bash Here

# 2. Authenticate (first time)
gcloud auth login
gcloud auth application-default login

# 3. Set project
export GCP_PROJECT_ID=your-project-id
gcloud config set project $GCP_PROJECT_ID

# 4. Make scripts executable
chmod +x *.sh

# 5. Setup GCP project
./setup-gcp-project.sh

# 6. Deploy backend
export SERVICE_NAME=ai-interviewer-backend
export GCP_REGION=us-central1
./deploy-backend.sh

# 7. Get backend URL and deploy frontend
export BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $GCP_REGION --format 'value(status.url)')
export GCS_BUCKET_NAME=ai-interviewer-frontend
./deploy-frontend.sh
```

---

## 🆘 Troubleshooting

### Issue: "Permission denied" when running scripts

**Solution**:
```bash
# In Git Bash or Terminal
chmod +x deploy-frontend.sh deploy-backend.sh setup-gcp-project.sh
```

### Issue: "gcloud: command not found"

**Solution**:
1. Install gcloud CLI
2. Restart terminal
3. Verify: `gcloud --version`

### Issue: Scripts have Windows line endings (CRLF)

**Solution**:
```bash
# In Git Bash
dos2unix deploy-backend.sh deploy-frontend.sh setup-gcp-project.sh
```

### Issue: Paths with spaces don't work

**Solution**: Use quotes:
```bash
cd "/c/Users/ADMIN/Downloads/ai interview portal (1)"
```

---

## 📞 Summary

**For Windows Users**:
- ✅ **Best**: Use **Git Bash** (right-click folder → Git Bash Here)
- ✅ **Alternative**: Use **WSL** for full Linux experience
- ⚠️ **Limited**: PowerShell (can't run bash scripts directly)

**For Linux/macOS Users**:
- ✅ Use native **Terminal**

**All Commands Work In**:
- Git Bash (Windows)
- WSL (Windows)
- Terminal (Linux/macOS)
- PowerShell (for gcloud commands only, not bash scripts)

---

**Last Updated**: 2025-01-27

