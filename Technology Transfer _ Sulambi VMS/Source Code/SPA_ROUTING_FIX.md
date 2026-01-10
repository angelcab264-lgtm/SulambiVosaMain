# Fix 404 on Page Refresh - Node.js Web Service Solution

## Problem
The `_redirects` file approach wasn't working reliably with Render's static site hosting. When refreshing pages outside the homepage, you get 404 errors.

## Solution
Changed from **Static Site** to **Node.js Web Service** with Express server that properly handles SPA routing.

## What Changed

### 1. Created Express Server (`server.js`)
- Serves static files from the `dist` directory
- Handles all routes by serving `index.html` (SPA fallback)
- Works reliably on Render

### 2. Updated `package.json`
- Added `express` as a dependency
- Added `start` script to run the server

### 3. Updated `render.yaml`
- Changed frontend service from `env: static` to `env: node`
- Changed from `staticPublishPath` to using `startCommand` with Node.js server
- Added PORT environment variable

## Files Modified

1. `server.js` - New Express server file
2. `package.json` - Added express dependency and start script
3. `render.yaml` - Changed frontend service type to Node.js web service

## Deployment Steps

### Step 1: Commit and Push Changes
```bash
git add .
git commit -m "Fix 404 on refresh: Switch to Node.js web service with Express"
git push
```

### Step 2: Update Service on Render

**IMPORTANT:** You need to update your existing service on Render:

1. Go to Render Dashboard
2. Find your frontend service (`sulambi-vosa`)
3. Click **"Settings"**
4. Change **"Environment"** from `Static Site` to `Node`
5. **Update Start Command:**
   ```
   cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main" && npm start
   ```
6. Remove or ignore the **"Publish Directory"** field (we're using Node.js now, not static)
7. Click **"Save Changes"**
8. The service will automatically redeploy

**OR** (Easier option):
- Delete the old static site service
- Let Render recreate it using the updated `render.yaml` (if using Blueprint)
- Or manually create a new Web Service with Node.js

### Step 3: Verify Deployment

After deployment:
1. ✅ Visit your homepage - should work
2. ✅ Navigate to `/dashboard` - should work  
3. ✅ **Refresh** `/dashboard` - should work (no 404)
4. ✅ Navigate to `/admin/dashboard` - should work
5. ✅ **Refresh** `/admin/dashboard` - should work (no 404)

## How It Works

1. **Express server** listens on the PORT provided by Render
2. **Static files** (CSS, JS, images) are served from the `dist` directory
3. **All routes** (`/*`) serve `index.html`, allowing React Router to handle client-side routing
4. When you refresh `/dashboard`, Express serves `index.html`, React loads, and React Router shows the dashboard

## Benefits

✅ **Guaranteed to work** - Express properly handles all routes
✅ **No dependency on `_redirects` file** - Server handles routing
✅ **Same performance** - Still serves static files efficiently
✅ **Future-proof** - Easy to add API routes or middleware if needed

## Troubleshooting

### Issue: Service won't start
- Check that `express` is installed: The build script runs `npm install`, which should install it
- Check build logs to verify `express` was installed

### Issue: Still getting 404
- Verify the service type is `Node` (not `Static Site`)
- Check that the start command is correct
- Check the logs tab to see if the server started successfully

### Issue: Port errors
- Render automatically sets the PORT environment variable
- The server.js file uses `process.env.PORT || 10000` as fallback
- This should work automatically

## Notes

- The Express server only runs in production (on Render)
- For local development, continue using `npm run dev` (Vite dev server)
- The build process remains the same - Vite builds to `dist/`, then Express serves it


