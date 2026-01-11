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

**To test with a specific API URL:**

**Windows (PowerShell):**
```powershell
$env:VITE_API_URI="http://localhost:8000/api"; npm run test:production
```

**Windows (Command Prompt):**
```cmd
set VITE_API_URI=http://localhost:8000/api && npm run test:production
```

**Linux/Mac:**
```bash
VITE_API_URI=http://localhost:8000/api npm run test:production
```

**To test with your Render backend:**
```powershell
$env:VITE_API_URI="https://sulambi-backend1.onrender.com/api"; npm run test:production
```

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

1. **During development**: Use `npm run dev` (fast hot reload)
2. **Before deploying**: Use `npm run test:production` (test production build)
3. **After deploying**: Test on Render (final verification)

This way you catch production issues before deploying! 🚀

