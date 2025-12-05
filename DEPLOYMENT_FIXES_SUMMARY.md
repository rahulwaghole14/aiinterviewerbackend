# Deployment Fixes Summary

## Issues Fixed

### 1. Lambda Function Error for Root-Level Assets ✅
**Error:** `TypeError: <lambda>() takes 2 positional arguments but 3 were given`

**Fix:** Updated the lambda function in `interview_app/urls.py` to handle regex capturing groups properly:
```python
lambda request, *args: serve_frontend_assets(request, args[0] if args else request.path.lstrip('/'))
```

**Status:** ✅ Fixed and pushed to backend repo

### 2. CORS Errors - Frontend API Configuration ✅
**Error:** `Access to fetch at 'http://127.0.0.1:8000/api/auth/login/' from origin 'https://aiinterviewerbackend-2.onrender.com' has been blocked by CORS policy`

**Root Cause:** Frontend was hardcoded to use `http://127.0.0.1:8000` instead of Render backend URL

**Fixes Applied:**

#### Frontend Repo (https://github.com/rahulwaghole14/aiinterviewfrontend.git)
- Updated `src/config/constants.js` to use Render backend URL in production
- Updated `vite.config.js` to support environment variables
- **Status:** ✅ Fixed and pushed to frontend repo

#### Backend Repo (https://github.com/rahulwaghole14/aiinterviewerbackend.git)
- Updated CORS settings in `interview_app/settings.py` to allow:
  - `https://aiinterviewerbackend-2.onrender.com` (Backend serving frontend)
  - `https://aiinterviewerbackend-3.onrender.com` (Separate frontend service)
  - All Render subdomains via regex: `r"^https://.*\.onrender\.com$"`
- **Status:** ✅ Fixed and pushed to backend repo

### 3. Static Assets MIME Type Errors ✅
**Error:** CSS and JS files served as `text/html` instead of proper MIME types

**Fix:** 
- Added `/assets/` route exclusion from catch-all
- Created dedicated `serve_frontend_assets` function with proper MIME type detection
- **Status:** ✅ Fixed in previous commits

## Repository Structure

### Backend Repository
- **URL:** https://github.com/rahulwaghole14/aiinterviewerbackend.git
- **Render Service:** https://aiinterviewerbackend-2.onrender.com
- **Purpose:** 
  - Serves Django API endpoints
  - Serves React frontend from `static_frontend_dist/`
  - Handles all backend logic

### Frontend Repository  
- **URL:** https://github.com/rahulwaghole14/aiinterviewfrontend.git
- **Render Service:** https://aiinterviewerbackend-3.onrender.com (if deployed separately)
- **Purpose:**
  - React frontend source code
  - Can be deployed separately or built and included in backend

## Deployment Workflow

### For Frontend Changes Only:
1. Make changes in `frontend/` directory
2. Commit and push to: https://github.com/rahulwaghole14/aiinterviewfrontend.git
3. Rebuild frontend: `cd frontend && npm run build`
4. Copy `frontend/dist` to `static_frontend_dist` in backend repo
5. Commit and push backend repo with updated `static_frontend_dist`

### For Backend Changes:
1. Make changes in backend files (excluding `frontend/` folder)
2. Commit and push to: https://github.com/rahulwaghole14/aiinterviewerbackend.git

## Current Configuration

### Frontend API Configuration
- **Production:** Uses `https://aiinterviewerbackend-2.onrender.com`
- **Development:** Uses `http://127.0.0.1:8000`
- **Environment Variable:** `VITE_API_URL` (can be set in Render dashboard)

### CORS Configuration
- Allows requests from:
  - Localhost (development)
  - `aiinterviewerbackend-2.onrender.com` (backend)
  - `aiinterviewerbackend-3.onrender.com` (frontend service)
  - All Render subdomains

## Next Steps

1. **Backend Deployment:** Will automatically deploy from backend repo
2. **Frontend Deployment:** 
   - If deployed separately, will deploy from frontend repo
   - Frontend service should set `VITE_API_URL=https://aiinterviewerbackend-2.onrender.com` in Render environment variables
3. **Rebuild Frontend:** After frontend changes, rebuild and update `static_frontend_dist` in backend repo

## Files Changed

### Backend Repo:
- `interview_app/urls.py` - Fixed lambda function, added asset routes
- `interview_app/settings.py` - Updated CORS settings
- `static_frontend_dist/` - Frontend build files

### Frontend Repo:
- `src/config/constants.js` - Dynamic API URL configuration
- `vite.config.js` - Environment variable support

