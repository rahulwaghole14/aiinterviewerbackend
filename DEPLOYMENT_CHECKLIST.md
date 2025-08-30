# Deployment Checklist for AI Interviewer on Render

## ✅ Pre-Deployment Checklist

### Repository Setup
- [ ] Code is in a GitHub repository
- [ ] All changes are committed and pushed
- [ ] `render.yaml` is properly configured
- [ ] `requirements.txt` is up to date
- [ ] `frontend/package.json` is up to date

### Environment Variables Prepared
- [ ] Backend environment variables list ready
- [ ] Frontend environment variables list ready
- [ ] API keys and secrets prepared (if needed)

## 🚀 Backend Deployment Steps

### 1. Create Web Service on Render
- [ ] Go to https://dashboard.render.com
- [ ] Click "New +" → "Web Service"
- [ ] Connect your GitHub repository
- [ ] Configure service:
  - **Name**: `ai-interviewer-backend`
  - **Environment**: `Python`
  - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
  - **Start Command**: `gunicorn ai_platform.wsgi:application --bind 0.0.0.0:$PORT`

### 2. Configure Environment Variables
- [ ] `SECRET_KEY`: Generate a secure key
- [ ] `DEBUG`: `false`
- [ ] `ALLOWED_HOSTS`: `.onrender.com`
- [ ] `CORS_ALLOWED_ORIGINS`: `https://ai-interviewer-frontend.onrender.com`
- [ ] `DJANGO_SETTINGS_MODULE`: `ai_platform.settings`
- [ ] `DATABASE_URL`: Will be auto-provided by Render

### 3. Create Database
- [ ] In Render dashboard, create a new PostgreSQL database
- [ ] Name: `aiinterviewer-db`
- [ ] Plan: Free
- [ ] Link it to your backend service

### 4. Deploy Backend
- [ ] Click "Create Web Service"
- [ ] Wait for build to complete
- [ ] Check logs for any errors
- [ ] Test API endpoints

## 🎨 Frontend Deployment Steps

### 1. Create Static Site on Render
- [ ] Go to https://dashboard.render.com
- [ ] Click "New +" → "Static Site"
- [ ] Connect your GitHub repository
- [ ] Configure site:
  - **Name**: `ai-interviewer-frontend`
  - **Build Command**: `cd frontend && npm install && npm run build`
  - **Publish Directory**: `frontend/dist`

### 2. Configure Environment Variables
- [ ] `VITE_API_URL`: `https://ai-interviewer-backend.onrender.com`
- [ ] `VITE_APP_NAME`: `AI Interviewer`
- [ ] `VITE_APP_VERSION`: `1.0.0`

### 3. Deploy Frontend
- [ ] Click "Create Static Site"
- [ ] Wait for build to complete
- [ ] Check logs for any errors
- [ ] Test the application

## 🔧 Post-Deployment Verification

### Backend Verification
- [ ] API endpoints are accessible
- [ ] Database connections work
- [ ] Static files are served correctly
- [ ] CORS is configured properly
- [ ] Environment variables are set correctly

### Frontend Verification
- [ ] App loads without errors
- [ ] API calls to backend work
- [ ] All features function correctly
- [ ] Build process completes successfully
- [ ] No console errors in browser

### Integration Testing
- [ ] Frontend can communicate with backend
- [ ] Authentication flows work
- [ ] File uploads/downloads work
- [ ] Real-time features work (if any)
- [ ] Interview portal works correctly

## 🛠️ Troubleshooting Common Issues

### Build Failures
- [ ] Check build logs in Render dashboard
- [ ] Verify all dependencies are in requirements.txt/package.json
- [ ] Check for syntax errors in code

### Database Connection Issues
- [ ] Verify DATABASE_URL format
- [ ] Check database service is running
- [ ] Ensure migrations are applied

### CORS Errors
- [ ] Update CORS_ALLOWED_ORIGINS with correct frontend URL
- [ ] Check browser console for specific errors
- [ ] Verify backend CORS configuration

### Static Files Not Loading
- [ ] Ensure collectstatic runs during build
- [ ] Check STATIC_ROOT configuration
- [ ] Verify whitenoise is configured

## 📊 Performance Monitoring

### After Deployment
- [ ] Monitor application performance
- [ ] Check response times
- [ ] Monitor error rates
- [ ] Check resource usage
- [ ] Set up logging and monitoring

### Security Review
- [ ] All sensitive data is properly secured
- [ ] API endpoints are properly protected
- [ ] CORS settings are appropriate
- [ ] No debug information is exposed

## 🔄 Continuous Deployment Setup

### Automatic Deployments
- [ ] Render automatically deploys on Git pushes
- [ ] Configure branch protection rules (if needed)
- [ ] Set up staging environment (optional)

### Manual Deployments
- [ ] Use Render dashboard for manual deployments
- [ ] Rollback to previous versions if needed
- [ ] Monitor deployment logs

## 📞 Support Resources

- [ ] Render Documentation: https://docs.render.com
- [ ] Render Community: https://community.render.com
- [ ] Django Deployment Guide: https://docs.djangoproject.com/en/stable/howto/deployment/
- [ ] Project-specific documentation: `RENDER_DEPLOYMENT_GUIDE.md`

---

**Note**: This checklist should be completed in order. Each step builds upon the previous one. If you encounter issues at any step, resolve them before proceeding to the next step.
