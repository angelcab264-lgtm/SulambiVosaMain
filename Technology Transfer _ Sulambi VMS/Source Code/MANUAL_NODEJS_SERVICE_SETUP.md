# Manual Node.js Web Service Setup Guide

This guide shows how to manually create a new Node.js frontend service on Render **without** affecting your existing services or database.

## Why Manual Setup?

- ✅ Your existing services stay unchanged
- ✅ Database remains untouched
- ✅ No risk of recreating/reconfiguring existing services
- ✅ You can test the new service alongside the static site

## Step-by-Step Instructions

### Step 1: Go to Render Dashboard

1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**

### Step 2: Connect Your Repository

1. If not already connected:
   - Connect your GitHub/GitLab/Bitbucket repository
   - Or select your existing repository if already connected
2. Click **"Connect"**

### Step 3: Configure the Web Service

Fill in the following settings:

#### Basic Settings:
- **Name:** `sulambi-frontend` (or any name you prefer)
- **Region:** `Oregon` (or same region as your other services)
- **Branch:** `main` (or your default branch)
- **Root Directory:** 
  ```
  Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main
  ```

#### Build & Start:
- **Environment:** `Node`
- **Build Command:**
  ```bash
  chmod +x build.sh && ./build.sh
  ```
- **Start Command:**
  ```bash
  npm install --production && node server.js
  ```

#### Plan:
- Select **"Free"** plan (or your preferred plan)

### Step 4: Set Environment Variables

Click **"Advanced"** or scroll down to **"Environment Variables"** section:

Add these variables:

1. **VITE_API_URI**
   - **Key:** `VITE_API_URI`
   - **Value:** `https://sulambi-backend1.onrender.com/api`
     (Replace `sulambi-backend1` with your actual backend service name)

2. **PORT** (Optional - Render sets this automatically)
   - **Key:** `PORT`
   - **Value:** Leave empty or Render will set it automatically

### Step 5: Create the Service

1. Review all settings
2. Click **"Create Web Service"**
3. Render will start building and deploying

### Step 6: Verify Deployment

1. Wait for the build to complete (check the **"Logs"** tab)
2. You should see:
   ```
   ✅ Building with VITE_API_URI=...
   ✅ _redirects file ensured in dist/
   ✅ Build verification complete!
   ```
3. Then the server should start:
   ```
   Server is running on port 10000
   Serving static files from: ...
   ```

### Step 7: Test the Service

1. Once deployed, you'll get a URL like: `https://sulambi-frontend.onrender.com`
2. Visit the URL - should see your app
3. Navigate to any route (e.g., `/dashboard`)
4. **Refresh the page** - should work without 404! ✅

## Configuration Summary

Here's what you need:

| Setting | Value |
|---------|-------|
| **Name** | `sulambi-frontend` |
| **Environment** | `Node` |
| **Root Directory** | `Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main` |
| **Build Command** | `chmod +x build.sh && ./build.sh` |
| **Start Command** | `npm install --production && node server.js` |
| **Environment Variable** | `VITE_API_URI` = `https://your-backend.onrender.com/api` |

## Important Notes

1. **Both services will exist:**
   - `sulambi-vosa` (static site) - original, keeps working
   - `sulambi-frontend` (Node.js) - new, handles routing correctly

2. **You can switch URLs later:**
   - Once the Node.js service is working, you can:
     - Update your domain/CNAME to point to the new service
     - Or simply use the new service URL

3. **No database impact:**
   - This only creates a new frontend service
   - Your database and backend services remain unchanged

## Troubleshooting

### Build fails with "express not found"
- Make sure `express` is in `package.json` dependencies (it should be)
- Check build logs to verify `npm install` ran successfully

### Service won't start
- Check the logs tab for error messages
- Verify `server.js` exists in the root directory
- Make sure `dist` folder was created during build

### Still getting 404 on refresh
- Verify the service type is `Node` (not `Static Site`)
- Check logs to see if server started successfully
- Make sure you're using the new service URL (not the old static site URL)

## Next Steps

After the service is working:
1. Test all routes with page refresh
2. Once confirmed working, you can:
   - Delete the old static site service (optional)
   - Or keep both for redundancy

