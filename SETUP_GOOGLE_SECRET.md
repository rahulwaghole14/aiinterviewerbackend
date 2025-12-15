# 🔐 Setup Google Cloud Secret for TTS Service Account

## Current Setup
- Secret name: `my-service-key`
- Contains: Google Cloud service account JSON key for Text-to-Speech

## Option 1: Mount Secret as File (Recommended)

### Correct Syntax:
```bash
gcloud run services update talaroai \
  --region asia-southeast1 \
  --set-secrets=/etc/secrets/my-service-key.json=my-service-key:latest \
  --set-env-vars=GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/my-service-key.json \
  --project=eastern-team-480811-e6
```

**Note**: The format is `MOUNT_PATH=SECRET_NAME:VERSION`

---

## Option 2: Use Secret as Environment Variable (Alternative)

If mounting as file doesn't work, you can use it as an environment variable:

```bash
# First, get the secret value
SECRET_VALUE=$(gcloud secrets versions access latest --secret=my-service-key --project=eastern-team-480811-e6)

# Then set it as environment variable (base64 encoded or as-is)
gcloud run services update talaroai \
  --region asia-southeast1 \
  --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS_JSON=${SECRET_VALUE}" \
  --project=eastern-team-480811-e6
```

**Then update code to read from environment variable instead of file.**

---

## Option 3: Update Code to Read from Secret Manager Directly

Update the code to fetch from Secret Manager at runtime:

```python
import os
from google.cloud import secretmanager

def get_google_credentials():
    """Get Google credentials from Secret Manager or file."""
    # Try Secret Manager first
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "eastern-team-480811-e6")
        secret_name = f"projects/{project_id}/secrets/my-service-key/versions/latest"
        response = client.access_secret_version(request={"name": secret_name})
        credentials_json = response.payload.data.decode("UTF-8")
        
        # Write to temp file
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.write(credentials_json)
        temp_file.close()
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file.name
        print(f"✅ Loaded credentials from Secret Manager: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        print(f"⚠️ Could not load from Secret Manager: {e}")
        # Fallback to file path
        credentials_path = os.path.join(settings.BASE_DIR, "ringed-reach-471807-m3-cf0ec93e3257.json")
        if os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            return credentials_path
    return None
```

---

## Recommended: Option 1 (Mount as File)

Try this command:

```bash
gcloud run services update talaroai \
  --region asia-southeast1 \
  --set-secrets=/etc/secrets/my-service-key.json=my-service-key:latest \
  --update-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/my-service-key.json" \
  --project=eastern-team-480811-e6
```

**Note**: Use `--update-env-vars` instead of `--set-env-vars` to preserve existing environment variables.

---

## Verify Secret Exists

```bash
# Check if secret exists
gcloud secrets describe my-service-key --project=eastern-team-480811-e6

# List all secrets
gcloud secrets list --project=eastern-team-480811-e6

# Check secret versions
gcloud secrets versions list my-service-key --project=eastern-team-480811-e6
```

---

## Update Code to Use Environment Variable

After mounting the secret, update the code to check the environment variable first:

**File**: `interview_app/views.py` (around line 625)

```python
def synthesize_speech(text, lang_code, accent_tld, output_path):
    # ... existing code ...
    
    # Get credentials path from environment or use default
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path or not os.path.exists(credentials_path):
        # Fallback to hardcoded path
        credentials_path = os.path.join(settings.BASE_DIR, "ringed-reach-471807-m3-cf0ec93e3257.json")
    
    if os.path.exists(credentials_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        print(f"✅ Google Cloud credentials set: {credentials_path}")
    else:
        print(f"❌ Google Cloud credentials not found at: {credentials_path}")
        raise Exception("Google Cloud credentials not found")
```

---

## Testing

After updating:

1. **Check if secret is mounted:**
```bash
# Check service configuration
gcloud run services describe talaroai \
  --region asia-southeast1 \
  --project=eastern-team-480811-e6 \
  --format="value(spec.template.spec.containers[0].env)"
```

2. **Test TTS functionality:**
- Start an interview
- Check logs for: `"✅ Google Cloud credentials set"`
- Verify TTS works (questions are spoken)

---

**Last Updated**: 2025-01-27

