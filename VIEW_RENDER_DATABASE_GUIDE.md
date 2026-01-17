# How to View Your Render PostgreSQL Database

## Option 1: Using the Python Script (Recommended)

### Step 1: Get Your Database Connection String

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your database service (e.g., `sulambi-database`)
3. Click on the **"Connection Info"** tab
4. Copy the **"Internal Database URL"** (or "External Database URL" if connecting from outside Render)

The URL looks like:
```
postgresql://username:password@hostname:port/database_name
```

### Step 2: Set the DATABASE_URL Environment Variable

**Windows PowerShell:**
```powershell
$env:DATABASE_URL = "postgresql://username:password@hostname:port/database_name"
```

**Windows Command Prompt:**
```cmd
set DATABASE_URL=postgresql://username:password@hostname:port/database_name
```

**Or create/update `.env` file** in the backend directory:
```
DATABASE_URL=postgresql://username:password@hostname:port/database_name
```

### Step 3: Run the View Script

Navigate to the backend directory and run:

```bash
cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-backend-main/sulambi-backend-main"
python view_render_database.py
```

Or for detailed view:

```bash
python check_render_database_detailed.py
```

## Option 2: Using Render's psql Console (In Browser)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your database service
3. Click on the **"Shell"** tab (or **"psql"** button)
4. You'll get an interactive SQL console where you can run queries like:

```sql
-- List all tables
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- View all accounts
SELECT * FROM accounts LIMIT 10;

-- View all membership applications
SELECT id, fullname, email, accepted, active FROM membership LIMIT 10;

-- View all requirements
SELECT id, email, eventid, type, accepted FROM requirements LIMIT 10;

-- View specific table
SELECT COUNT(*) FROM membership WHERE accepted IS NULL;
```

## Option 3: Using GUI Tools (pgAdmin, DBeaver, etc.)

### Using DBeaver (Free & Easy)

1. **Download DBeaver**: https://dbeaver.io/download/
2. **Install and open DBeaver**
3. **Create new connection**:
   - Right-click "Database Connections" → "New Database Connection"
   - Select "PostgreSQL"
4. **Enter connection details** (from Render Dashboard):
   - **Host**: Your database hostname (from connection string)
   - **Port**: Usually 5432
   - **Database**: Database name
   - **Username**: Database username
   - **Password**: Database password
5. **Click "Test Connection"** then "Finish"
6. **Browse tables** in the tree view on the left

### Using pgAdmin

1. Download pgAdmin from https://www.pgadmin.org/download/
2. Install and create a new server connection
3. Use the same connection details from Render Dashboard

## Quick Query Examples

Once connected via any method, you can run queries like:

```sql
-- Count records in each table
SELECT 
    table_name, 
    (SELECT COUNT(*) FROM information_schema.tables t2 
     WHERE t2.table_name = t1.table_name) as row_count
FROM information_schema.tables t1
WHERE table_schema = 'public';

-- View pending membership applications
SELECT id, fullname, email, srcode, accepted 
FROM membership 
WHERE accepted IS NULL
ORDER BY id DESC;

-- View recent requirements
SELECT id, email, "eventId", type, accepted, "createdAt"
FROM requirements
ORDER BY id DESC
LIMIT 20;

-- View active accounts
SELECT id, username, "accountType", active 
FROM accounts 
WHERE active = true;
```

## Troubleshooting

**If connection fails:**
- Make sure you're using the correct connection string from Render
- Check that your IP is whitelisted (if using External Database URL)
- Verify the database is running in Render Dashboard

**If psycopg2 error:**
```bash
pip install psycopg2-binary
```





