# Frontend Repository Changes Needed

## Issue
The frontend is hardcoded to use `http://127.0.0.1:8000` instead of the Render backend URL, causing CORS errors.

## Frontend Repository
**Repo:** https://github.com/rahulwaghole14/aiinterviewfrontend.git

## Changes Needed

### 1. Update `src/config/constants.js`

Change from:
```javascript
export const API_BASE_URL = 'http://127.0.0.1:8000';
```

To:
```javascript
// API Configuration Constants
// Use environment variable if available, otherwise use Render backend URL
const getApiBaseUrl = () => {
  // Check for Vite environment variable
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // Check for process.env (for build-time)
  if (typeof process !== 'undefined' && process.env?.VITE_API_URL) {
    return process.env.VITE_API_URL;
  }
  // Production: Use Render backend URL
  if (import.meta.env.PROD) {
    return 'https://aiinterviewerbackend-2.onrender.com';
  }
  // Development: Use localhost
  return 'http://127.0.0.1:8000';
};

export const API_BASE_URL = getApiBaseUrl();
```

### 2. Update `vite.config.js`

Change from:
```javascript
define: {
  'process.env.VITE_API_URL': JSON.stringify('https://aiinterviewerbackend-2.onrender.com'),
},
```

To:
```javascript
define: {
  // Use environment variable if set, otherwise default to Render backend
  'process.env.VITE_API_URL': JSON.stringify(
    process.env.VITE_API_URL || 'https://aiinterviewerbackend-2.onrender.com'
  ),
},
```

### 3. Render Environment Variable (Optional)

In Render dashboard for frontend service, you can set:
- **Key:** `VITE_API_URL`
- **Value:** `https://aiinterviewerbackend-2.onrender.com`

## Deployment Setup

### Backend Service (aiinterviewerbackend-2)
- **Repo:** https://github.com/rahulwaghole14/aiinterviewerbackend.git
- **URL:** https://aiinterviewerbackend-2.onrender.com
- **Purpose:** Serves API endpoints and static frontend files

### Frontend Service (aiinterviewerbackend-3)
- **Repo:** https://github.com/rahulwaghole14/aiinterviewfrontend.git
- **URL:** https://aiinterviewerbackend-3.onrender.com
- **Purpose:** Serves React frontend (if deployed separately)

## Notes

- Frontend changes should be committed to: https://github.com/rahulwaghole14/aiinterviewfrontend.git
- Backend changes should be committed to: https://github.com/rahulwaghole14/aiinterviewerbackend.git
- Both services should connect to each other via their Render URLs

