# Testing Production Build Locally

This guide shows you how to test your production build locally, just like it runs on Render, so you can test changes quickly without deploying.

## Quick Start

**Important:** Make sure you're in the frontend directory first!

1. **Navigate to the frontend directory:**
   ```powershell
   cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main"
   ```

2. **Build and run production server:**
   ```powershell
   npm run test:production
   ```

3. **Open your browser:**
   - Go to `http://localhost:10000`
   - Test your app like it's in production!

## Step by Step

### Option 1: Build and Serve in One Command (Recommended)

**From the frontend directory:**
```powershell
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main"
npm run test:production
```
This will:
- Build the production version (like Render does)
- Start the Express server on port 10000
- Serve your built app just like in production

### Option 2: Build and Serve Separately

**From the frontend directory:**
```powershell
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main"

# Step 1: Build the production version
npm run build:local

# Step 2: Start the server (in a separate terminal if you want)
npm run serve:local
```

## Setting the API URL

By default, the build uses your `.env` file or the `VITE_API_URI` environment variable.

### Test with Local Backend (localhost)

**Windows (PowerShell):**
```powershell
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main"
$env:VITE_API_URI="http://localhost:8000/api"
npm run test:production
```

**Windows (Command Prompt):**
```cmd
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main"
set VITE_API_URI=http://localhost:8000/api
npm run test:production
```

**Linux/Mac:**
```bash
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main"
VITE_API_URI=http://localhost:8000/api npm run test:production
```

### Test with Render Backend (Production Database) ⭐ Recommended

**This is what you want!** Run the frontend locally but use your Render backend (and database):

**Windows (PowerShell):**
```powershell
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main"
$env:VITE_API_URI="https://sulambi-backend1.onrender.com/api"
npm run test:production
```

**Windows (Command Prompt):**
```cmd
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main"
set VITE_API_URI=https://sulambi-backend1.onrender.com/api
npm run test:production
```

**Linux/Mac:**
```bash
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main"
VITE_API_URI=https://sulambi-backend1.onrender.com/api npm run test:production
```

**Benefits of testing with Render backend:**
- ✅ Uses your production database (real data)
- ✅ Tests against the actual backend API
- ✅ No need to run backend locally
- ✅ Faster testing (frontend builds locally, backend is already running)
- ✅ More accurate production testing

## What's Different from Dev Mode?

- **Production build**: Code is minified and optimized (slower builds, faster runtime)
- **Express server**: Uses the same `server.js` as production (tests SPA routing)
- **No hot reload**: You need to rebuild after changes
- **Port 10000**: Default port (same as Render)

## Testing SPA Routing

One of the main benefits of testing locally is verifying that page refreshes work correctly:

1. Navigate to any route (e.g., `/dashboard`)
2. Refresh the page (F5)
3. It should load correctly (not 404) - this is what we fixed!

## Stopping the Server

Press `Ctrl+C` in the terminal to stop the server.

## Troubleshooting

**Port already in use?**
- Change the port in `server.js` or set `PORT` environment variable:
  ```powershell
  $env:PORT="3000"; npm run serve:local
  ```

**Build errors?**
- Try `npm run build-ignore` first to skip TypeScript checks
- Fix TypeScript errors if any, then use `npm run build`

**API not connecting?**
- Make sure your backend is running (if testing with local backend)
- Check the `VITE_API_URI` environment variable is set correctly
- Check browser console for API errors

## Workflow Recommendation

1. **During development**: 
   - Use `npm run dev` (fast hot reload)
   - Connect to Render backend: `$env:VITE_API_URI="https://sulambi-backend1.onrender.com/api"; npm run dev`

2. **Before deploying (recommended)**: 
   - Test production build with Render backend: `$env:VITE_API_URI="https://sulambi-backend1.onrender.com/api"; npm run test:production`
   - This tests your production build against your production database

3. **After deploying**: 
   - Test on Render (final verification)

This way you catch production issues before deploying! 🚀

## Common Scenarios

### Scenario 1: Test frontend changes with production data
```powershell
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main"
$env:VITE_API_URI="https://sulambi-backend1.onrender.com/api"
npm run test:production
```
**Use case:** You changed the frontend UI and want to see how it looks with real production data.

### Scenario 2: Test with local backend (requires backend running)
```powershell
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main"
$env:VITE_API_URI="http://localhost:8000/api"
npm run test:production
```
**Use case:** You're also developing backend changes and want to test both locally.

