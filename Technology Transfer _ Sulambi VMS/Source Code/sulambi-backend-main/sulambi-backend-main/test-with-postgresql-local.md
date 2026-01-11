# Testing Locally with PostgreSQL (Has Your Data)

Since you migrated to PostgreSQL, your data is in PostgreSQL, not SQLite. To test locally with your actual data:

## Quick Setup

**1. Get your PostgreSQL connection string from Render:**
- Go to Render Dashboard → sulambi-database
- Click "Connection Info" tab
- Copy the **"External Database URL"** (for connecting from your local machine)

**2. Set DATABASE_URL and start backend:**
```powershell
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-backend-main/sulambi-backend-main"

# Set DATABASE_URL to your Render PostgreSQL database
$env:DATABASE_URL = "postgresql://user:password@host:port/database"
# (Replace with your actual connection string)

# Start the server
python server.py
```

**3. Test the satisfaction analytics:**
- Backend: `http://localhost:8000/api/analytics/satisfaction?year=2025`
- Your data should be visible!

## Option 2: Check if SQLite Database Has Data

If you want to check if your local SQLite database has any data:

```powershell
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-backend-main/sulambi-backend-main"

# Make sure DATABASE_URL is NOT set (to use SQLite)
$env:DATABASE_URL = $null

# Run the check script
python check_satisfaction_data.py
```

This will show:
- How many rows are in satisfactionSurveys table
- How many rows are in semester_satisfaction table
- Sample data if it exists

## Why This Happens

When you migrated to PostgreSQL:
- ✅ Data moved from SQLite → PostgreSQL
- ❌ SQLite database is now empty (or was reset)
- Your production data is in PostgreSQL on Render

To test with real data locally, you need to connect to PostgreSQL.

