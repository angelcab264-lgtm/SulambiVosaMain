# Testing Satisfaction Analytics Locally with SQLite

This guide helps you test the satisfaction analytics locally with SQLite to verify everything works before deploying to PostgreSQL.

## Quick Start

1. **Navigate to backend directory:**
   ```powershell
   cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-backend-main/sulambi-backend-main"
   ```

2. **Ensure SQLite is used (don't set DATABASE_URL):**
   ```powershell
   # Make sure DATABASE_URL is NOT set (unset it if it exists)
   $env:DATABASE_URL = $null
   ```

3. **Initialize database (if needed):**
   ```powershell
   python server.py --init
   ```

4. **Start the backend server:**
   ```powershell
   python server.py
   ```

   The server should start on `http://localhost:8000`

5. **Test the satisfaction analytics endpoint:**
   - Open browser: `http://localhost:8000/api/analytics/satisfaction?year=2023`
   - Or use curl: `curl http://localhost:8000/api/analytics/satisfaction?year=2023`

## Full Steps

### Step 1: Check Python Version
```powershell
python --version
```
Should be Python 3.x

### Step 2: Install Dependencies (if not already installed)
```powershell
pip install -r requirements.txt
```

### Step 3: Ensure SQLite Mode
Make sure `DATABASE_URL` environment variable is **NOT set** or is empty. This makes the backend use SQLite:

```powershell
# Check if DATABASE_URL is set
echo $env:DATABASE_URL

# If it's set, unset it to use SQLite
$env:DATABASE_URL = $null
```

### Step 4: Initialize Database
Initialize the SQLite database (this creates `app/database/database.db`):

```powershell
python server.py --init
```

This will create all necessary tables including:
- `evaluation`
- `satisfactionSurveys`
- `semester_satisfaction`
- etc.

### Step 5: Start the Server
```powershell
python server.py
```

You should see output like:
```
 * Running on http://127.0.0.1:8000
```

### Step 6: Test Satisfaction Analytics

**Option 1: Browser**
- Open: `http://localhost:8000/api/analytics/satisfaction`
- Or with year: `http://localhost:8000/api/analytics/satisfaction?year=2023`

**Option 2: PowerShell (curl)**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/analytics/satisfaction?year=2023" | Select-Object -ExpandProperty Content
```

**Option 3: Python script**
Create a test file `test_satisfaction.py`:
```python
import requests
response = requests.get("http://localhost:8000/api/analytics/satisfaction?year=2023")
print(response.json())
```

## Testing with Your Frontend

If you want to test with your frontend running locally:

1. **Backend (Terminal 1):**
   ```powershell
   cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-backend-main/sulambi-frontend-main"
   $env:DATABASE_URL = $null
   python server.py
   ```

2. **Frontend (Terminal 2):**
   ```powershell
   cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main"
   $env:VITE_API_URI = "http://localhost:8000/api"
   npm run dev
   ```

3. Open browser: `http://localhost:5173` (or whatever port Vite shows)

## Troubleshooting

**"Database file not found"**
- Run `python server.py --init` to initialize the database

**"Module not found" errors**
- Run `pip install -r requirements.txt`

**Port 8000 already in use**
- Change the port in `server.py` or kill the process using port 8000

**Getting empty data**
- The database might be empty. Add some evaluation data first, or check if you have data in your SQLite database.

## Verifying SQLite is Being Used

The backend will print:
- `Using SQLite database...` when using SQLite
- `Using PostgreSQL database...` when using PostgreSQL

You can also check:
- SQLite database file: `app/database/database.db` (should exist)
- No DATABASE_URL environment variable set

