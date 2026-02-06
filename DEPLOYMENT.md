# Deployment Guide

## Current Deployment Setup

### Frontend (Vercel)
- **URL**: https://portfolio-kevpatz.vercel.app
- **Platform**: Vercel
- **Config**: `vercel.json`

### Backend (Vercel)
- **URL**: https://portfolio-back-flax-beta.vercel.app
- **Platform**: Vercel
- **Config**: `vercel.json`

## Important Configuration

### 1. Verify Your Vercel Backend URL

Your backend is deployed at: **https://portfolio-back-flax-beta.vercel.app**

To verify it's working:
1. Visit [https://portfolio-back-flax-beta.vercel.app/api/health](https://portfolio-back-flax-beta.vercel.app/api/health)
2. Should return: `{"status": "healthy", "message": "API is running", ...}`

### 2. Update Frontend API URL (if needed)

The frontend reads the backend URL from `frontend/js/config.js` and localStorage.

To update without redeploying:
1. Open `/admin`
2. Set **Backend API URL** and click **Save**

To update defaults, change `frontend/js/config.js`.

### 3. CORS Configuration

Make sure your backend allows requests from your Vercel frontend:

Set `CORS_ORIGINS` in Vercel environment variables:
```
https://portfolio-kevpatz.vercel.app
```

### 4. Test Your Deployment

1. **Backend Health Check**: Visit `https://portfolio-back-flax-beta.vercel.app/api/health`
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
  1. Check Vercel function logs
  2. Manually trigger `python seed_database.py` if needed

### CORS errors in console
- **Cause**: CORS_ORIGINS not set correctly
- **Fix**: Update CORS_ORIGINS environment variable on Vercel

## Updating Deployments

### Frontend (Vercel)
Vercel auto-deploys from GitHub:
1. Push changes to GitHub
2. Vercel automatically rebuilds and deploys

### Backend (Vercel)
Vercel auto-deploys from GitHub:
1. Push changes to GitHub
2. Vercel automatically rebuilds and deploys
3. Check deployment logs in Vercel dashboard

## Quick Deploy Checklist

- [ ] Backend deployed on Vercel
- [ ] Backend health endpoint working
- [ ] CORS_ORIGINS set to Vercel URL
- [ ] Frontend API_URL updated with Vercel URL
- [ ] Database seeded with data
- [ ] Frontend deployed on Vercel
- [ ] Test all API endpoints from frontend
- [ ] Admin panel working
