# Testing Satisfaction Analytics Locally

## Quick Test Steps

### 1. Start Backend (SQLite)

Open **Terminal 1 (PowerShell)**:

```powershell
cd "C:\SulambiVosaMain\Technology Transfer _ Sulambi VMS\Source Code\sulambi-backend-main\sulambi-backend-main"

# Make sure DATABASE_URL is NOT set (to use SQLite)
$env:DATABASE_URL = $null

# Start the backend server
python server.py
```

You should see:
```
 * Running on http://127.0.0.1:8000
```

### 2. Start Frontend

Open **Terminal 2 (PowerShell)**:

```powershell
cd "C:\SulambiVosaMain\Technology Transfer _ Sulambi VMS\Source Code\sulambi-frontend-main\sulambi-frontend-main"

# Set API to use local backend
$env:VITE_API_URI = "http://localhost:8000/api"

# Start the frontend dev server
npm run dev
```

You should see:
```
VITE v... ready in ... ms
➜  Local:   http://localhost:5173/
```

### 3. Test in Browser

1. **Open browser**: Go to `http://localhost:5173`
2. **Login** to your account
3. **Navigate to Dashboard** (or Analytics page if available)
4. **Look for "Predictive Satisfaction Ratings"** section
5. **Check the year filter** - select "2025"
6. **Verify data displays**:
   - Should show 2 semesters (2025-1 and 2025-2)
   - Scores should be around 4.1-4.2
   - Progress bars should show the values

### 4. Check Browser Console

Open **Developer Tools** (F12) and check the **Console** tab:

You should see logs like:
```
[Satisfaction Analytics] Processing response: { hasResponse: true, success: true, hasData: true, satisfactionDataLength: 2 }
```

If you see errors, check:
- Network tab: Is the API call to `http://localhost:8000/api/analytics/satisfaction?year=2025` returning 200?
- Console: Are there any JavaScript errors?

### 5. Test API Directly (Optional)

Open browser or use PowerShell:

```powershell
# Test the API endpoint directly
Invoke-WebRequest -Uri "http://localhost:8000/api/analytics/satisfaction?year=2025" | Select-Object -ExpandProperty Content
```

Or open in browser:
```
http://localhost:8000/api/analytics/satisfaction?year=2025
```

You should see JSON response with:
```json
{
  "success": true,
  "data": {
    "satisfactionData": [
      { "semester": "2025-1", "score": 4.1, ... },
      { "semester": "2025-2", "score": 4.2, ... }
    ]
  }
}
```

## Troubleshooting

### No data showing in frontend?

1. **Check backend is running**: `http://localhost:8000/api/analytics/satisfaction?year=2025`
2. **Check frontend API URL**: Browser DevTools → Network tab → Look for the request URL
   - Should be: `http://localhost:8000/api/analytics/satisfaction?year=2025`
   - NOT: `https://sulambi-backend1.onrender.com/api/...`
3. **Clear browser cache**: Ctrl+Shift+Delete → Clear cache
4. **Hard refresh**: Ctrl+F5
5. **Check console logs**: Look for the `[Satisfaction Analytics] Processing response:` log

### Backend not starting?

- Check if port 8000 is in use
- Check Python version: `python --version` (should be 3.x)
- Check dependencies: `pip install -r requirements.txt`

### Frontend not starting?

- Check if Node.js is installed: `node --version`
- Install dependencies: `npm install`
- Check PowerShell execution policy (if npm commands fail)

## Expected Results

✅ **Success looks like:**
- Backend running on port 8000
- Frontend running on port 5173 (or similar)
- Browser shows satisfaction analytics with data for 2025
- Two semesters displayed (2025-1 and 2025-2)
- Scores around 4.1-4.2
- No errors in browser console

❌ **Failure looks like:**
- "No satisfaction rating data available" message
- Empty charts/graphs
- Errors in browser console
- 404 or 500 errors in Network tab

