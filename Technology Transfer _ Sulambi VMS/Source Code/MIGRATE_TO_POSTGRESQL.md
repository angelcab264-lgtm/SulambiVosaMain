# Migrate SQLite to PostgreSQL on Render

## Current Status

✅ **Backend is configured** to use PostgreSQL  
✅ **Tables are created** automatically on Render (empty)  
❌ **Data migration** - NOT DONE YET (you need to run this)

## Step-by-Step Migration

### Step 1: Get Your Render PostgreSQL Connection URL

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your database: `sulambi-database`
3. Go to **"Connection Info"** tab
4. Copy the **"External Database URL"** (NOT Internal)
   - Format: `postgresql://user:password@host:port/database`
   - Example: `postgresql://sulambi_user:abc123@dpg-xxxxx-a.oregon-postgres.render.com/sulambi`

### Step 2: Run Migration Script Locally

**On your local machine:**

1. **Navigate to backend directory:**
   ```powershell
   cd "Technology Transfer _ Sulambi VMS\Source Code\sulambi-backend-main\sulambi-backend-main"
   ```

2. **Set the DATABASE_URL environment variable:**
   ```powershell
   # Windows PowerShell
   $env:DATABASE_URL = "postgresql://user:password@host:port/database"
   
   # Replace with your actual External Database URL from Step 1
   ```

3. **Make sure psycopg2 is installed:**
   ```powershell
   pip install psycopg2-binary
   ```

4. **Run the migration script:**
   ```powershell
   python migrate_sqlite_to_postgresql.py
   ```

### Step 3: Verify Migration

The script will:
- ✅ Connect to your local SQLite database
- ✅ Connect to Render PostgreSQL database
- ✅ Copy all tables and data
- ✅ Show progress for each table
- ✅ Report any errors

**Expected Output:**
```
==========================================================
MIGRATING SQLITE DATABASE TO POSTGRESQL
==========================================================
Source (SQLite): app/database/database.db
Target (PostgreSQL): dpg-xxxxx-a.oregon-postgres.render.com
✓ Connected to PostgreSQL database
✓ Connected to SQLite database

Found 15 tables to migrate: accounts, sessions, membership, ...

==========================================================
Migrating table: accounts
==========================================================
  Found 5 columns
  Found 2 rows to migrate
  ✓ Cleared existing data from PostgreSQL table
  ✓ Successfully migrated 2/2 rows
...
```

### Step 4: Verify Data on Render

After migration completes:

1. **Test your app on Render:**
   - Try logging in with your credentials
   - Check if your data appears

2. **Or check database directly:**
   - Use a PostgreSQL client (pgAdmin, DBeaver, etc.)
   - Connect using the External Database URL
   - Query tables to verify data

## Troubleshooting

### Error: "Table doesn't exist in PostgreSQL"

**Solution:** The backend hasn't created tables yet. 
1. Make sure your backend service has deployed successfully
2. Check backend logs - it should run `python server.py --init` on first startup
3. Wait for backend to finish initializing
4. Then run migration script again

### Error: "Cannot connect to PostgreSQL"

**Possible causes:**
- Using Internal URL instead of External URL (use External!)
- Firewall blocking connection (Render free tier may restrict external connections)
- Wrong credentials

**Solution:**
- Double-check you're using **External Database URL**
- Verify credentials are correct
- Try connecting with a PostgreSQL client first

### Error: "psycopg2 not installed"

**Solution:**
```powershell
pip install psycopg2-binary
```

### Migration Partially Failed

If some tables failed to migrate:
1. Check the error messages in the script output
2. Common issues:
   - Data type mismatches (script handles most automatically)
   - Foreign key constraints
   - Invalid data
3. You can run the script again - it will skip already migrated tables or update them

## Important Notes

⚠️ **Backup First:** The migration script will **TRUNCATE** (clear) existing data in PostgreSQL tables before inserting. Make sure you want to do this!

⚠️ **One-Time Operation:** After migration, your app on Render will use PostgreSQL. Your local SQLite database remains unchanged.

⚠️ **External URL Only:** Use the **External Database URL** for connecting from your local machine. Internal URL only works from within Render's network.

## After Migration

Once migration is complete:
1. ✅ Your data is now in PostgreSQL on Render
2. ✅ Your app on Render will use PostgreSQL automatically
3. ✅ Local development still uses SQLite (unless you change it)
4. ✅ Future data added on Render stays in PostgreSQL

## Quick Reference

```powershell
# 1. Set environment variable
$env:DATABASE_URL = "postgresql://user:pass@host:port/db"

# 2. Run migration
cd "Technology Transfer _ Sulambi VMS\Source Code\sulambi-backend-main\sulambi-backend-main"
python migrate_sqlite_to_postgresql.py
```

---

**Need Help?** Check the migration script output for detailed error messages.




