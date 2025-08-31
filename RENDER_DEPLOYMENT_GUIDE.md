# Render Deployment Guide for AI Interviewer

This guide covers deploying both the Django backend and React frontend on Render.

## 📋 Prerequisites

1. **GitHub Repository**: Ensure your code is in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **Environment Variables**: Prepare your environment variables

## 🚀 Backend Deployment (Django)

### Step 1: Update render.yaml

The current `render.yaml` needs some updates for production deployment:

```yaml
services:
  - type: web
    name: ai-interviewer-backend
    runtime: python
    plan: free
    buildCommand: |
      pip install -r requirements.txt
      python manage.py collectstatic --noinput
      python manage.py migrate --noinput
    startCommand: gunicorn ai_platform.wsgi:application --bind 0.0.0.0:$PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: aiinterviewer-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: DJANGO_SETTINGS_MODULE
        value: ai_platform.settings
      - key: DEBUG
        value: false
      - key: ALLOWED_HOSTS
        value: ".onrender.com"
      - key: CORS_ALLOWED_ORIGINS
        value: "https://your-frontend-app.onrender.com"

databases:
  - name: aiinterviewer-db
    plan: free
```

### Step 2: Update Django Settings

Create a production settings file or update your existing settings:

```python
# ai_platform/settings.py (production section)

import os
import dj_database_url

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600
    )
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CORS settings for production
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Step 3: Deploy Backend

1. **Connect Repository**: In Render dashboard, click "New +" → "Web Service"
2. **Connect GitHub**: Link your repository
3. **Configure Service**:
   - **Name**: `ai-interviewer-backend`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
   - **Start Command**: `gunicorn ai_platform.wsgi:application --bind 0.0.0.0:$PORT`
4. **Add Environment Variables**:
   - `SECRET_KEY`: Generate a secure key
   - `DEBUG`: `false`
   - `ALLOWED_HOSTS`: `.onrender.com`
   - `CORS_ALLOWED_ORIGINS`: Your frontend URL
5. **Deploy**: Click "Create Web Service"

## 🎨 Frontend Deployment (React)

### Step 1: Update Frontend Configuration

Update your `frontend/vite.config.js`:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  server: {
    port: 3000,
  },
})
```

### Step 2: Update API Endpoints

Update all API calls in your frontend to use the production backend URL:

```javascript
// frontend/src/config/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://your-backend-app.onrender.com';

export const API_ENDPOINTS = {
  base: API_BASE_URL,
  auth: `${API_BASE_URL}/auth/`,
  candidates: `${API_BASE_URL}/candidates/`,
  interviews: `${API_BASE_URL}/interviews/`,
  // ... other endpoints
};
```

### Step 3: Create Environment File

Create `frontend/.env.production`:

```env
VITE_API_URL=https://your-backend-app.onrender.com
```

### Step 4: Deploy Frontend

1. **Create Static Site**: In Render dashboard, click "New +" → "Static Site"
2. **Connect Repository**: Link your frontend repository
3. **Configure Site**:
   - **Name**: `ai-interviewer-frontend`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`
4. **Add Environment Variables**:
   - `VITE_API_URL`: Your backend URL
5. **Deploy**: Click "Create Static Site"

## 🔧 Alternative: Monorepo Deployment

If you want to deploy both from the same repository:

### Step 1: Update render.yaml for Both Services

```yaml
services:
  # Backend Service
  - type: web
    name: ai-interviewer-backend
    runtime: python
    plan: free
    buildCommand: |
      pip install -r requirements.txt
      python manage.py collectstatic --noinput
      python manage.py migrate --noinput
    startCommand: gunicorn ai_platform.wsgi:application --bind 0.0.0.0:$PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: aiinterviewer-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: DJANGO_SETTINGS_MODULE
        value: ai_platform.settings
      - key: DEBUG
        value: false
      - key: ALLOWED_HOSTS
        value: ".onrender.com"
      - key: CORS_ALLOWED_ORIGINS
        value: "https://ai-interviewer-frontend.onrender.com"

  # Frontend Service
  - type: web
    name: ai-interviewer-frontend
    runtime: static
    plan: free
    buildCommand: |
      cd frontend
      npm install
      npm run build
    staticPublishPath: ./frontend/dist
    envVars:
      - key: VITE_API_URL
        value: https://ai-interviewer-backend.onrender.com

databases:
  - name: aiinterviewer-db
    plan: free
```

## 🔐 Environment Variables Setup

### Backend Environment Variables

```bash
# Required
SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://user:password@host:port/database
DEBUG=false
ALLOWED_HOSTS=.onrender.com,your-domain.com

# CORS
CORS_ALLOWED_ORIGINS=https://your-frontend-app.onrender.com

# Optional (if using external services)
AI_MODEL_API_KEY=your-ai-api-key
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Frontend Environment Variables

```bash
# API Configuration
VITE_API_URL=https://your-backend-app.onrender.com

# Optional
VITE_APP_NAME=AI Interviewer
VITE_APP_VERSION=1.0.0
```

## 🚨 Important Considerations

### 1. Database Migration
- Ensure all migrations are applied during deployment
- Test migrations locally before deploying

### 2. Static Files
- Django static files are collected during build
- Frontend build creates optimized static files

### 3. CORS Configuration
- Update CORS settings to allow your frontend domain
- Test API calls from frontend to backend

### 4. Environment Variables
- Never commit sensitive data to Git
- Use Render's environment variable management

### 5. SSL/HTTPS
- Render provides automatic SSL certificates
- Ensure your app works with HTTPS

## 🔍 Post-Deployment Checklist

### Backend Verification
- [ ] API endpoints are accessible
- [ ] Database connections work
- [ ] Static files are served correctly
- [ ] CORS is configured properly
- [ ] Environment variables are set

### Frontend Verification
- [ ] App loads without errors
- [ ] API calls to backend work
- [ ] All features function correctly
- [ ] Build process completes successfully

### Integration Testing
- [ ] Frontend can communicate with backend
- [ ] Authentication flows work
- [ ] File uploads/downloads work
- [ ] Real-time features (if any) work

## 🛠️ Troubleshooting

### Common Issues

1. **Build Failures**:
   - Check build logs in Render dashboard
   - Verify all dependencies are in requirements.txt/package.json

2. **Database Connection Issues**:
   - Verify DATABASE_URL format
   - Check database service is running

3. **CORS Errors**:
   - Update CORS_ALLOWED_ORIGINS with correct frontend URL
   - Check browser console for specific errors

4. **Static Files Not Loading**:
   - Ensure collectstatic runs during build
   - Check STATIC_ROOT configuration

### Debug Commands

```bash
# Check backend logs
# In Render dashboard → Logs tab

# Test API endpoints
curl https://your-backend-app.onrender.com/api/health/

# Check frontend build
# In Render dashboard → Build logs
```

## 📈 Scaling Considerations

### Free Tier Limitations
- **Backend**: 750 hours/month, sleeps after 15 minutes of inactivity
- **Frontend**: 750 hours/month, always on
- **Database**: 1GB storage, 90 days retention

### Paid Plans
- **Backend**: $7/month for always-on service
- **Database**: $7/month for persistent storage
- **Frontend**: Remains free

## 🔄 Continuous Deployment

### Automatic Deployments
- Render automatically deploys on Git pushes
- Configure branch protection rules
- Set up staging environment

### Manual Deployments
- Use Render dashboard for manual deployments
- Rollback to previous versions if needed

## 📞 Support

- **Render Documentation**: [docs.render.com](https://docs.render.com)
- **Render Community**: [community.render.com](https://community.render.com)
- **Django Deployment**: [docs.djangoproject.com](https://docs.djangoproject.com/en/stable/howto/deployment/)

---

**Note**: Replace `your-backend-app.onrender.com` and `your-frontend-app.onrender.com` with your actual Render URLs after deployment.

