# 🔧 Installing Google Cloud SDK (gcloud) on Windows

## 📋 Quick Installation Guide

### Method 1: Using Installer (Recommended) ⭐

1. **Download Google Cloud SDK**:
   - Visit: https://cloud.google.com/sdk/docs/install
   - Click "Download for Windows"
   - Or direct link: https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe

2. **Run the Installer**:
   - Double-click `GoogleCloudSDKInstaller.exe`
   - Follow the installation wizard
   - ✅ Check "Run gcloud init" at the end
   - ✅ Check "Add to PATH" (important!)

3. **Restart Terminal**:
   - Close and reopen your terminal/PowerShell/Command Prompt
   - Or restart your computer

4. **Verify Installation**:
   ```cmd
   gcloud --version
   ```

---

### Method 2: Using Chocolatey (If you have it)

```powershell
# Open PowerShell as Administrator
choco install gcloudsdk
```

Then restart your terminal.

---

### Method 3: Manual Installation

1. **Download ZIP**:
   - https://cloud.google.com/sdk/docs/downloads-versioned-archives
   - Download Windows 64-bit ZIP

2. **Extract**:
   - Extract to `C:\Program Files\Google\Cloud SDK\`

3. **Add to PATH**:
   - Press `Win + X` → **System** → **Advanced system settings**
   - Click **Environment Variables**
   - Under **System Variables**, find `Path` → **Edit**
   - Click **New** → Add: `C:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin`
   - Click **OK** on all dialogs

4. **Restart Terminal**

---

## ✅ Verify Installation

Open a **new** terminal (PowerShell, CMD, or Git Bash) and run:

```cmd
gcloud --version
```

**Expected Output**:
```
Google Cloud SDK 450.0.0
bq 2.0.95
core 2024.01.26
gsutil 5.27
```

---

## 🔐 Initial Setup

After installation, authenticate:

### Step 1: Login
```cmd
gcloud auth login
```
This will open your browser to sign in with your Google account.

### Step 2: Set Default Project
```cmd
gcloud config set project YOUR_PROJECT_ID
```

### Step 3: Enable Application Default Credentials
```cmd
gcloud auth application-default login
```

---

## 🐛 Troubleshooting

### Issue: "gcloud is not recognized" after installation

**Solution 1: Restart Terminal**
- Close all terminal windows
- Open a new terminal
- Try again

**Solution 2: Check PATH**
```powershell
# In PowerShell
$env:PATH -split ';' | Select-String -Pattern "google"
```

If nothing appears, manually add to PATH (see Method 3 above).

**Solution 3: Use Full Path**
```cmd
"C:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" --version
```

If this works, the PATH is not set correctly.

### Issue: "gcloud init" fails

**Solution**: Run as Administrator or check internet connection

### Issue: Installation fails

**Solution**: 
1. Disable antivirus temporarily
2. Run installer as Administrator
3. Check Windows Event Viewer for errors

---

## 🔄 Update gcloud

```cmd
gcloud components update
```

---

## 📚 Next Steps

After installation:

1. **Authenticate**:
   ```cmd
   gcloud auth login
   ```

2. **Set Project**:
   ```cmd
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Enable APIs** (if needed):
   ```cmd
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable storage-api.googleapis.com
   ```

4. **Start Deploying**:
   ```cmd
   gcloud builds submit --config=frontend/cloudbuild-frontend.yaml
   ```

---

## 🆘 Still Having Issues?

1. **Check Installation Path**:
   - Default: `C:\Program Files\Google\Cloud SDK\google-cloud-sdk\`
   - Verify `gcloud.cmd` exists in `bin` folder

2. **Manual PATH Addition**:
   - Add: `C:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin`
   - Restart computer

3. **Reinstall**:
   - Uninstall from Control Panel
   - Download fresh installer
   - Run as Administrator

4. **Check System Requirements**:
   - Windows 7 or later
   - 64-bit system
   - Internet connection

---

## 📞 Alternative: Use Cloud Shell

If installation continues to fail, use **Google Cloud Shell** (browser-based):

1. Go to: https://console.cloud.google.com/
2. Click the **Cloud Shell** icon (top right)
3. Run all commands there (no installation needed!)

---

**Last Updated**: 2025-01-27

