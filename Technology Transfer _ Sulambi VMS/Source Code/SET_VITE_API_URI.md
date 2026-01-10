# How to Set VITE_API_URI on Render

## Quick Fix

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Open your Frontend Service**: Click on `sulambi-frontend` (or your frontend service name)
3. **Go to Environment Tab**: Click on "Environment" in the left sidebar
4. **Add Environment Variable**:
   - Click "Add Environment Variable"
   - **Key**: `VITE_API_URI`
   - **Value**: `https://YOUR-BACKEND-NAME.onrender.com/api`
     - Replace `YOUR-BACKEND-NAME` with your actual backend service name
     - Example: If your backend is `sulambi-backend`, use: `https://sulambi-backend.onrender.com/api`
5. **Save Changes**: Click "Save Changes"
6. **Redeploy**: The service will automatically redeploy, or click "Manual Deploy" → "Deploy latest commit"

## How to Find Your Backend URL

1. Go to your **Backend Service** in Render Dashboard
2. Look at the top of the page - you'll see the service URL
3. It will be something like: `https://sulambi-backend.onrender.com`
4. Add `/api` to the end: `https://sulambi-backend.onrender.com/api`

## Important Notes

- ⚠️ **Set this BEFORE the first build** if possible
- If you set it after the first build, you'll need to **rebuild** the frontend
- The value must include `/api` at the end
- Use `https://` not `http://`

## Verify It's Set

After setting the variable and redeploying:
1. Check the build logs - you should see: `✅ Building with VITE_API_URI=https://...`
2. No more warnings about VITE_API_URI not being set
3. Your frontend should be able to connect to the backend API

## Troubleshooting

**Problem**: Still seeing the warning after setting it
- **Solution**: Make sure you saved the environment variable and triggered a new deployment

**Problem**: Frontend can't connect to backend
- **Solution**: 
  1. Verify the backend URL is correct
  2. Check that the backend service is running
  3. Make sure you included `/api` at the end of the URL
  4. Verify CORS is enabled on the backend (should already be configured)




