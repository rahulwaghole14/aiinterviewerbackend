# Render Deployment Fix Guide

## Problem
Render is trying to use `ai_platform.wsgi:application` which doesn't exist. The correct WSGI path is `interview_app.wsgi:application`.

## Solution

### Option 1: Update Render Dashboard (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Navigate to your web service (`ai_interviewer_backend`)
3. Click on **Settings** tab
4. Scroll down to **Start Command** section
5. **Delete or update** the start command to:
   ```
   gunicorn interview_app.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```
6. **Save Changes**
7. **Manual Deploy** → **Deploy latest commit**

### Option 2: Use Blueprint (render.yaml)

If your service was created manually, you may need to:

1. Delete the existing service
2. Create a new service using **Blueprint** (render.yaml)
3. Connect your GitHub repository
4. Render will automatically use the `render.yaml` configuration

### Option 3: Verify Configuration Files

All configuration files are correct:

- ✅ **Procfile**: `web: gunicorn interview_app.wsgi:application --bind 0.0.0.0:$PORT`
- ✅ **render.yaml**: `startCommand: gunicorn interview_app.wsgi:application --bind 0.0.0.0:$PORT`

## Verification

After updating, the deployment should show:
```
==> Running 'gunicorn interview_app.wsgi:application --bind 0.0.0.0:$PORT'
```

Instead of:
```
==> Running 'gunicorn ai_platform.wsgi:application --bind 0.0.0.0:$PORT'
```

## Files Updated

- ✅ `Procfile` - Correct WSGI path
- ✅ `render.yaml` - Correct startCommand with workers and timeout
- ✅ `verify_deployment.py` - Verification script added to build
- ✅ `start.sh` - Alternative startup script (if needed)

## Important Notes

- The `render.yaml` file takes precedence if using Blueprint
- The `Procfile` is used if the service was created manually
- Manual start command in dashboard **overrides** both files
- Always check the dashboard settings if deployment fails



