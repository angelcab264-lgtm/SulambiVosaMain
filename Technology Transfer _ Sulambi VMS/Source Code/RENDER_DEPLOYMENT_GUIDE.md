# Render Deployment Guide - SQLite to PostgreSQL Migration

This guide will help you deploy your Sulambi VMS application to Render and migrate your SQLite database to PostgreSQL.

## Prerequisites

1. A GitHub account with your code pushed to a repository
2. A Render account (sign up at https://render.com)
3. Your local SQLite database file (`app/database/database.db`)

## Step 1: Prepare Your Repository

1. Make sure all your code is committed and pushed to GitHub
2. Verify that `render.yaml` exists in the root of your repository
3. Ensure `requirements.txt` includes `psycopg2-binary` and `gunicorn`

## Step 2: Create PostgreSQL Database on Render

1. Log in to your Render dashboard: https://dashboard.render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Configure the database:
   - **Name:** `sulambi-database`
   - **Database:** `sulambi`
   - **User:** `sulambi_user`
   - **Region:** `Oregon` (or your preferred region)
   - **Plan:** `Free` (or upgrade if needed)
4. Click **"Create Database"**
5. **Important:** Copy the **External Database URL** (you'll need this for migration)
   - Go to your database → **Connection Info** tab
   - Copy the **External Database URL** (format: `postgresql://user:password@host:port/database`)

## Step 3: Deploy Backend Service

1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure the service:
   - **Name:** `sulambi-backend`
   - **Region:** `Oregon` (same as database)
   - **Branch:** `main` (or your default branch)
   - **Root Directory:** `Technology Transfer _ Sulambi VMS/Source Code/sulambi-backend-main/sulambi-backend-main`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `chmod +x start.sh && ./start.sh`
4. Add Environment Variables:
   - `PYTHON_VERSION` = `3.11.0`
   - `DATABASE_URL` = (from database connection info - **Internal Database URL**)
   - `DEBUG` = `False`
   - `HOST` = `0.0.0.0`
   - `PORT` = (auto-set by Render)
   - `AUTOMAILER_EMAIL` = (your email)
   - `AUTOMAILER_PASSW` = (your email password)
5. Click **"Create Web Service"**

**Note:** The backend will automatically create tables on first startup using `tableInitializer.py` (now supports PostgreSQL!)

## Step 4: Migrate Data from SQLite to PostgreSQL

### Option A: Using the Migration Script (Recommended)

1. **On your local machine**, navigate to the backend directory:
   ```powershell
   cd "Technology Transfer _ Sulambi VMS\Source Code\sulambi-backend-main\sulambi-backend-main"
   ```

2. **Set the DATABASE_URL environment variable** to your Render PostgreSQL External URL:
   ```powershell
   # Windows PowerShell
   $env:DATABASE_URL = "postgresql://user:password@host:port/database"
   
   # Or create/update .env file:
   # DATABASE_URL=postgresql://user:password@host:port/database
   ```

3. **Run the migration script**:
   ```powershell
   python migrate_sqlite_to_postgresql.py
   ```

4. The script will:
   - Connect to your local SQLite database
   - Connect to your Render PostgreSQL database
   - Migrate all tables and data
   - Show progress for each table

### Option B: Manual Migration (If script fails)

1. Use a database tool like pgAdmin, DBeaver, or TablePlus
2. Connect to your Render PostgreSQL database using the External URL
3. Export data from SQLite and import to PostgreSQL manually

## Step 5: Deploy Frontend Service

1. In Render dashboard, click **"New +"** → **"Static Site"**
2. Connect your GitHub repository
3. Configure the service:
   - **Name:** `sulambi-frontend`
   - **Branch:** `main`
   - **Root Directory:** `Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main`
   - **Build Command:** `chmod +x build.sh && ./build.sh`
   - **Publish Directory:** `dist`
4. Add Environment Variable:
   - `VITE_API_URI` = `https://sulambi-backend.onrender.com/api`
     (Replace `sulambi-backend` with your actual backend service name)
5. Click **"Create Static Site"**

## Step 6: Verify Deployment

1. **Backend:**
   - Visit: `https://sulambi-backend.onrender.com/api`
   - Should see: `{"message":"Api route is working"}`

2. **Frontend:**
   - Visit your static site URL (e.g., `https://sulambi-frontend.onrender.com`)
   - Should load the landing page

3. **Database:**
   - Log in to your app using default credentials:
     - Admin: `Admin` / `sulambi@2024`
     - Officer: `Sulambi-Officer` / `password@2024`
   - Verify that your data migrated correctly

## Step 7: Update Environment Variables (If Needed)

If you need to update environment variables after deployment:

1. Go to your service in Render dashboard
2. Click **"Environment"** tab
3. Add or update variables
4. Click **"Save Changes"** (service will automatically redeploy)

## Troubleshooting

### Backend Issues

**Error: "psycopg2 not installed"**
- Solution: Make sure `psycopg2-binary` is in `requirements.txt`

**Error: "Database connection failed"**
- Check that `DATABASE_URL` is set correctly
- Use **Internal Database URL** (not External) for services on Render
- Verify database is running and accessible

**Error: "Table already exists"**
- This is normal if tables were already created
- The migration script will skip or update existing tables

### Frontend Issues

**Error: "Cannot connect to API"**
- Verify `VITE_API_URI` is set correctly
- Check backend service is running
- Ensure CORS is configured (already done in `server.py`)

**Error: "Build failed"**
- Check that `VITE_API_URI` is set before build
- Verify Node.js version compatibility

### Migration Issues

**Error: "Tables don't exist"**
- Solution: Deploy backend first (tables will be created automatically)
- Or run `create_postgresql_tables.py` manually before migration

**Error: "Connection timeout"**
- Check firewall settings
- Verify you're using the **External Database URL** for local migration
- Ensure your IP is whitelisted (Render free tier may have restrictions)

## Important Notes

1. **Database URLs:**
   - **Internal URL:** Use this for services running on Render (backend service)
   - **External URL:** Use this for connecting from your local machine (migration script)

2. **Free Tier Limitations:**
   - Services spin down after 15 minutes of inactivity
   - First request after spin-down may take 30-60 seconds
   - Consider upgrading for production use

3. **File Storage:**
   - Render's filesystem is ephemeral (files are lost on redeploy)
   - Consider using cloud storage (S3, Cloudinary) for uploads
   - Update upload paths in your code if needed

4. **Environment Variables:**
   - Never commit `.env` files to GitHub
   - Always set sensitive variables in Render dashboard
   - Use Render's environment variable sync for related services

## Next Steps

1. Set up custom domains (if needed)
2. Configure SSL certificates (automatic on Render)
3. Set up monitoring and alerts
4. Configure backups for PostgreSQL database
5. Update email service configuration for production

## Support

- Render Documentation: https://render.com/docs
- Render Community: https://community.render.com
- Check logs in Render dashboard for detailed error messages

---

**Last Updated:** 2024
**Version:** 1.0





