# How to Import Your Local SQLite Database to Render PostgreSQL

## Prerequisites

1. Make sure you have `psycopg2-binary` installed:
   ```powershell
   pip install psycopg2-binary
   ```

2. Have your local SQLite database file ready
   - Default location: `Technology Transfer _ Sulambi VMS/Source Code/sulambi-backend-main/sulambi-backend-main/app/database/database.db`

3. Get your Render PostgreSQL connection string:
   - Go to Render Dashboard → `sulambi-database`
   - Click "Connection Info" tab
   - Copy the "External Database URL" (for connecting from your local machine)
   - Note: Use "Internal Database URL" only for services within Render's network

## Steps to Import

### Step 1: Navigate to Backend Directory

```powershell
cd "Technology Transfer _ Sulambi VMS\Source Code\sulambi-backend-main\sulambi-backend-main"
```

### Step 2: Set Your DATABASE_URL Environment Variable

**Windows PowerShell:**
```powershell
$env:DATABASE_URL = "postgresql://sulambi_user:YOUR_PASSWORD@YOUR_HOST.onrender.com/sulambi"
```

Replace:
- `YOUR_PASSWORD` with your actual database password
- `YOUR_HOST` with your actual hostname

**Example:**
```powershell
$env:DATABASE_URL = "postgresql://sulambi_user:abc123@dpg-xxxxx-a.singapore-postgres.render.com/sulambi"
```

### Step 3: Make Sure Your Local Database Path is Set (if different from default)

If your `.env` file has a different `DB_PATH`, or if you want to specify it:
```powershell
$env:DB_PATH = "app/database/database.db"
```

### Step 4: Run the Migration Script

```powershell
python migrate_sqlite_to_postgresql.py
```

### Step 5: Verify the Migration

After migration completes, you can verify by:

1. **Using the viewer script:**
   ```powershell
   python view_render_database.py
   ```

2. **Or check in Render:**
   - Restart your backend service
   - Check logs to see if database queries work

## Troubleshooting

### Error: "psycopg2 not installed"
```powershell
pip install psycopg2-binary
```

### Error: "Table does not exist"
The PostgreSQL tables might not have been created yet. The backend should create them on first startup. If not:
1. Make sure your backend service has `DATABASE_URL` set correctly
2. Restart the backend service
3. Check the logs to see if tables were created

### Error: "Could not connect to PostgreSQL"
- Verify your connection string is correct
- Make sure you copied the "External Database URL" (for local connections)
- Check that the database service is running in Render
- External Database URL allows connections from outside Render's network

### Error: "Syntax error" when creating tables
The `tableInitializer.py` uses SQLite syntax. You may need to:
1. First let the backend initialize tables (even with errors)
2. Then run the migration
3. Or manually create tables with PostgreSQL syntax

## Important Notes

- The migration script will **TRUNCATE** (clear) existing data in PostgreSQL tables before importing
- Make sure your local SQLite database has all the data you want to migrate
- Large databases may take several minutes to migrate
- After migration, restart your Render backend service

