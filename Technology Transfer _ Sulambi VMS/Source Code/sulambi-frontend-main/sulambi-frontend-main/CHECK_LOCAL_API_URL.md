# Important: Using Local Backend for Testing

## Problem
Your frontend is still calling `sulambi-backend1.onrender.com` instead of `localhost:8000`.

## Solution

### Step 1: Stop the Frontend Dev Server
Press `Ctrl+C` in the terminal where `npm run dev` is running.

### Step 2: Set Environment Variable
**Windows PowerShell:**
```powershell
$env:VITE_API_URI = "http://localhost:8000/api"
```

### Step 3: Verify It's Set
```powershell
echo $env:VITE_API_URI
```
Should show: `http://localhost:8000/api`

### Step 4: Start Frontend Again
```powershell
npm run dev
```

### Step 5: Check Browser Network Tab
1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Refresh the page
4. Look for API requests
5. They should be going to: `http://localhost:8000/api/...`
6. NOT: `https://sulambi-backend1.onrender.com/api/...`

## Alternative: Create .env File

You can also create a `.env` file in the frontend root directory:

```env
VITE_API_URI=http://localhost:8000/api
```

Then restart the dev server. The `.env` file will be used automatically.

## Why This Matters

- **Local backend (localhost:8000)**: Uses your SQLite database with test data
- **Render backend (sulambi-backend1.onrender.com)**: Uses PostgreSQL on Render (production database)

For testing satisfaction analytics locally, you need to use the local backend!

