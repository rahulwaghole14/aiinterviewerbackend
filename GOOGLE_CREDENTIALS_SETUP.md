# Google Cloud TTS Credentials Setup

## ⚠️ Security Warning

GitHub has blocked pushing the `ringed-reach-471807-m3-cf0ec93e3257.json` file because it contains sensitive credentials. **Never commit service account keys to public repositories.**

## Recommended Solution: Use Environment Variables

Instead of committing the JSON file, use environment variables:

### Option 1: Set GOOGLE_APPLICATION_CREDENTIALS Environment Variable

1. **On Render:**
   - Go to your Render dashboard
   - Navigate to your service → Environment
   - Add environment variable:
     ```
     GOOGLE_APPLICATION_CREDENTIALS=/opt/render/project/src/ringed-reach-471807-m3-cf0ec93e3257.json
     ```

2. **Upload the file separately:**
   - Use Render's file upload feature, or
   - Add it manually after deployment via SSH, or
   - Store it in a secure location and reference it via environment variable

### Option 2: Store JSON Content as Environment Variable

1. **Convert JSON to base64:**
   ```bash
   cat ringed-reach-471807-m3-cf0ec93e3257.json | base64
   ```

2. **On Render, add environment variable:**
   ```
   GOOGLE_CLOUD_CREDENTIALS_BASE64=<base64_encoded_content>
   ```

3. **Update code to decode it:**
   ```python
   import base64
   import json
   import tempfile
   import os
   
   if os.environ.get('GOOGLE_CLOUD_CREDENTIALS_BASE64'):
       creds_base64 = os.environ.get('GOOGLE_CLOUD_CREDENTIALS_BASE64')
       creds_json = base64.b64decode(creds_base64).decode('utf-8')
       creds_dict = json.loads(creds_json)
       
       # Write to temp file
       temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
       json.dump(creds_dict, temp_file)
       temp_file.close()
       
       os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file.name
   ```

## Current File Paths

The code is already configured to look for files in these locations:

### YOLOv8n Model:
- **Primary:** `BASE_DIR/yolov8n.pt` ✅ (already pushed)
- **Fallback:** `./yolov8n.pt`

### Google Cloud Credentials:
- **Primary:** `BASE_DIR/ringed-reach-471807-m3-cf0ec93e3257.json`
- **Fallback:** Environment variable `GOOGLE_APPLICATION_CREDENTIALS`

## Files Updated

1. ✅ `.gitignore` - Added exception for `ringed-reach-471807-m3-cf0ec93e3257.json`
2. ✅ `interview_app/yolo_face_detector.py` - Updated to use `BASE_DIR/yolov8n.pt`
3. ✅ `interview_app/simple_real_camera.py` - Updated to use `BASE_DIR/yolov8n.pt`
4. ✅ `interview_app/complete_ai_bot.py` - Already uses `BASE_DIR/ringed-reach-471807-m3-cf0ec93e3257.json`
5. ✅ `interview_app/simple_ai_bot.py` - Already uses `BASE_DIR/ringed-reach-471807-m3-cf0ec93e3257.json`

## Next Steps

1. **Remove the JSON file from git history** (if you want to keep it private)
2. **Upload the file manually to Render** after deployment
3. **Or use environment variables** as described above

