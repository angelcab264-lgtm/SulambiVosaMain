# Fix 404 Error on Frontend Routes

## Problem
Getting `404 (Not Found)` when accessing routes like `/admin/dashboard` on Render.

## Solution

### 1. Verify `_redirects` File is Deployed
The `_redirects` file has been added to `public/_redirects`. This file tells Render to serve `index.html` for all routes (SPA fallback).

**After pushing, Render should automatically redeploy.** If not:
- Go to Render Dashboard → sulambi-frontend service
- Click "Manual Deploy" → "Deploy latest commit"

### 2. Set `VITE_API_URI` Environment Variable

**Critical:** The frontend needs to know where the backend API is located.

1. Go to Render Dashboard
2. Open your **frontend service** (likely named `sulambi-frontend` or `sulambi-vosa`)
3. Go to **Environment** tab
4. Add/Update environment variable:
   - **Key:** `VITE_API_URI`
   - **Value:** `https://YOUR-BACKEND-NAME.onrender.com/api`
   - Replace `YOUR-BACKEND-NAME` with your actual backend service name
   - Example: `https://sulambi-backend.onrender.com/api`

5. **Save** and **Redeploy** the frontend service

### 3. Verify Backend Service is Running

1. Go to Render Dashboard → Backend service
2. Check that it's **Live** (green status)
3. Test the API directly:
   - Visit: `https://YOUR-BACKEND-NAME.onrender.com/api/`
   - Should see: `{"message": "Api route is working"}`

### 4. Check Browser Console

Open browser DevTools (F12) → Console tab and look for:
- API request logs (should show the correct backend URL)
- Any CORS errors
- Network tab to see actual request URLs

### 5. Common Issues

**Issue:** Frontend shows 404 on all routes
- **Fix:** Ensure `_redirects` file is in `public/` directory and deployed

**Issue:** API calls fail with 404
- **Fix:** Set `VITE_API_URI` correctly (must include `/api` at the end)
- **Fix:** Verify backend service name matches in `VITE_API_URI`

**Issue:** CORS errors
- **Fix:** Backend CORS is already configured, but verify backend is running

**Issue:** Routes work but data doesn't load
- **Fix:** Check `VITE_API_URI` is set correctly
- **Fix:** Check browser console for API errors

## Testing

1. Visit: `https://YOUR-FRONTEND-NAME.onrender.com/`
2. Should see landing page
3. Navigate to: `https://YOUR-FRONTEND-NAME.onrender.com/admin/dashboard`
4. Should load dashboard (may show errors if API not configured, but page should load)

## Quick Checklist

- [ ] `_redirects` file exists in `public/` directory
- [ ] `_redirects` file is committed and pushed to GitHub
- [ ] Frontend service has been redeployed after adding `_redirects`
- [ ] `VITE_API_URI` is set in frontend service environment variables
- [ ] `VITE_API_URI` value is correct (includes `/api` at the end)
- [ ] Backend service is running and accessible
- [ ] Backend service name matches what's in `VITE_API_URI`





