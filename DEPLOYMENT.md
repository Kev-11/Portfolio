# Deployment Guide

## Current Deployment Setup

### Frontend (Vercel)
- **URL**: https://portfolio-kevpatz.vercel.app
- **Platform**: Vercel
- **Config**: `vercel.json`

### Backend (Render)
- **Service Name**: portfolio-api
- **URL**: https://portfolio-anuh.onrender.com
- **Platform**: Render
- **Config**: `render.yaml`

## Important Configuration

### 1. Verify Your Render Backend URL

Your backend is deployed at: **https://portfolio-anuh.onrender.com**

To verify it's working:
1. Visit [https://portfolio-anuh.onrender.com/api/health](https://portfolio-anuh.onrender.com/api/health)
2. Should return: `{"status": "healthy", "message": "API is running", ...}`

### 2. Update Frontend API URL (if needed)

The frontend is currently configured to use `https://portfolio-anuh.onrender.com`.

If you change your Render service URL, update these files:

**frontend/js/main.js**
```javascript
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://YOUR-ACTUAL-RENDER-URL.onrender.com';  // Update this
```

**frontend/js/admin.js**
```javascript
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://YOUR-ACTUAL-RENDER-URL.onrender.com';  // Update this
```

### 3. CORS Configuration

Make sure your backend allows requests from your Vercel frontend:

**On Render** (in render.yaml):
```yaml
- key: CORS_ORIGINS
  value: "https://portfolio-kevpatz.vercel.app"
```

Or set it in Render Dashboard → Environment Variables

### 4. Test Your Deployment

1. **Backend Health Check**: Visit `https://your-backend-url.onrender.com/api/health`
   - Should return: `{"status": "healthy", "message": "API is running", ...}`

2. **Frontend**: Visit `https://portfolio-kevpatz.vercel.app`
   - Open browser console (F12)
   - Look for `[API] Fetching...` messages
   - Should show data loading successfully

## Common Issues

### "Failed to fetch" errors
- **Cause**: Wrong backend URL or CORS not configured
- **Fix**: 
  1. Check backend URL is correct
  2. Verify CORS_ORIGINS includes your Vercel domain
  3. Check backend is running (visit health endpoint)

### Empty data arrays
- **Cause**: Database not seeded or backend not connected
- **Fix**:
  1. Go to Render dashboard
  2. Check logs for errors
  3. Manually trigger `python seed_database.py` if needed

### CORS errors in console
- **Cause**: CORS_ORIGINS not set correctly
- **Fix**: Update CORS_ORIGINS environment variable on Render

## Updating Deployments

### Frontend (Vercel)
Vercel auto-deploys from GitHub:
1. Push changes to GitHub
2. Vercel automatically rebuilds and deploys

### Backend (Render)
Render auto-deploys from GitHub:
1. Push changes to GitHub
2. Render automatically rebuilds and deploys
3. Check deployment logs in Render dashboard

## Quick Deploy Checklist

- [ ] Backend deployed on Render
- [ ] Backend health endpoint working
- [ ] CORS_ORIGINS set to Vercel URL
- [ ] Frontend API_URL updated with Render URL
- [ ] Database seeded with data
- [ ] Frontend deployed on Vercel
- [ ] Test all API endpoints from frontend
- [ ] Admin panel working
