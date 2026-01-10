# Fix 404 Error on Page Refresh

## Problem
When you refresh a page (e.g., `/dashboard` or `/admin/dashboard`), you get a 404 error:
```
Failed to load resource: the server responded with a status of 404 ()
```

This happens because the server is trying to find a file at that path instead of serving your React app's `index.html`.

## Solution

### Step 1: Verify `_redirects` File Exists

The `_redirects` file should be in:
```
public/_redirects
```

With this content:
```
/*    /index.html   200
```

**Important:** Make sure there are no extra spaces or characters. The format is:
- `/*` (matches all routes)
- Three spaces
- `/index.html` (what to serve)
- Two spaces  
- `200` (HTTP status code)

### Step 2: Build Script Update

The build script (`build.sh`) has been updated to:
1. Automatically create the `_redirects` file in the `dist` folder after build
2. Verify it exists before deployment

### Step 3: Deploy the Fix

1. **Commit and push the changes:**
   ```bash
   git add .
   git commit -m "Fix 404 on refresh - ensure _redirects file is deployed"
   git push
   ```

2. **Redeploy on Render:**
   - Go to Render Dashboard
   - Find your frontend service (`sulambi-vosa`)
   - Click **"Manual Deploy"** → **"Deploy latest commit"**
   - Wait for deployment to complete

3. **Verify the fix:**
   - Check the build logs - you should see:
     ```
     ✅ _redirects file ensured in dist/
     📄 Final contents:
     /*    /index.html   200
     ```
   - After deployment, visit your site and refresh on any route
   - It should work without 404 errors

### Step 4: If It Still Doesn't Work

#### Option A: Check Build Logs
1. Go to Render Dashboard → Your frontend service
2. Click on **"Logs"** tab
3. Look for the build output
4. Verify you see: `✅ _redirects file ensured in dist/`

#### Option B: Verify File in Build Output
1. In Render Dashboard → Your frontend service
2. Check that the `staticPublishPath` is correct:
   ```
   Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main/dist
   ```
3. The `_redirects` file should be at the root of this path

#### Option C: Manual File Check
If the automatic creation isn't working, you can manually ensure the file exists:

1. After the build completes, check if `dist/_redirects` exists
2. If not, the build script should create it automatically
3. If it still doesn't exist, there might be an issue with file permissions

#### Option D: Alternative - Check Render Settings
1. Go to Render Dashboard → Your frontend service
2. Click **"Settings"**
3. Look for any SPA (Single Page Application) or routing settings
4. Ensure the service type is set to **"Static Site"**

## How It Works

1. When you navigate to `/dashboard` in your React app, React Router handles it on the client side
2. When you **refresh** the page, the browser asks the server for `/dashboard`
3. The `_redirects` file tells Render: "For any route (`/*`), serve `/index.html` with status 200"
4. Your React app loads and React Router sees the `/dashboard` URL and shows the correct page

## Common Issues

### Issue: Still getting 404 after deploying
**Solution:** 
- Make sure you **redeployed** after pushing the changes
- Check the build logs to confirm `_redirects` file was created
- Try clearing your browser cache (Ctrl+Shift+R or Cmd+Shift+R)

### Issue: Build fails
**Solution:**
- Check build logs for errors
- Ensure `build.sh` has execute permissions (chmod +x build.sh)
- Verify Node.js and npm are working correctly

### Issue: Routes work initially but fail on refresh
**Solution:**
- This confirms the `_redirects` file isn't working
- Follow Step 3 to redeploy with the fix
- Verify the file exists in the `dist` folder after build

## Testing

After deployment:
1. ✅ Visit your homepage - should work
2. ✅ Navigate to `/dashboard` - should work
3. ✅ **Refresh** `/dashboard` - should work (no 404)
4. ✅ Navigate to `/admin/dashboard` - should work
5. ✅ **Refresh** `/admin/dashboard` - should work (no 404)
6. ✅ Directly visit any route URL - should work

If all of these work, the fix is successful! ✅


