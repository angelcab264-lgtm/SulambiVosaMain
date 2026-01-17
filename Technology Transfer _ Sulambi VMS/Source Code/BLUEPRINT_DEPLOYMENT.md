# Render Blueprint Deployment Guide

This guide explains how to deploy Sulambi VMS using Render's Blueprint feature for one-click deployment.

## What is a Blueprint?

A Render Blueprint is a YAML configuration file (`render.yaml`) that defines all your services (backend, frontend, database) in one place. When you deploy a Blueprint, Render automatically creates and configures all services for you.

## Quick Start (3 Steps)

### Step 1: Push to GitHub

Make sure your `render.yaml` file is in your repository root or in the directory you'll specify as the root directory.

```powershell
git add render.yaml
git commit -m "Add Render Blueprint configuration"
git push
```

### Step 2: Deploy Blueprint on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. **Set Root Directory** (if `render.yaml` is not in root):
   - If `render.yaml` is in `Technology Transfer _ Sulambi VMS/Source Code/`
   - Set Root Directory to: `Technology Transfer _ Sulambi VMS/Source Code`
5. Click **"Apply"**

Render will automatically:
- ✅ Create PostgreSQL database (`sulambi-database`)
- ✅ Create backend service (`sulambi-backend`)
- ✅ Create frontend service (`sulambi-frontend`)
- ✅ Link database to backend
- ✅ Set up environment variables

### Step 3: Configure Frontend API URL

**⚠️ IMPORTANT:** Do this **BEFORE** the frontend builds for the first time!

1. Wait for backend service to deploy and get its URL
2. Go to **Frontend Service** → **Environment** tab
3. Add environment variable:
   - **Key:** `VITE_API_URI`
   - **Value:** `https://sulambi-backend.onrender.com/api`
     (Replace `sulambi-backend` with your actual backend service name)
4. Click **"Save Changes"**
5. The frontend will automatically rebuild with the correct API URL

## What Gets Created

### 1. PostgreSQL Database
- **Name:** `sulambi-database`
- **Database:** `sulambi`
- **User:** `sulambi_user`
- Automatically connected to backend via `DATABASE_URL`

### 2. Backend Service
- **Name:** `sulambi-backend`
- **Type:** Python Web Service
- **Auto-configured:**
  - Database connection (`DATABASE_URL`)
  - Port (`PORT`)
  - Python version (`3.11.0`)
- **You need to set:**
  - `AUTOMAILER_EMAIL` (your email)
  - `AUTOMAILER_PASSW` (your email password)

### 3. Frontend Service
- **Name:** `sulambi-frontend`
- **Type:** Static Site
- **You need to set:**
  - `VITE_API_URI` (backend URL + `/api`)

## Environment Variables Setup

### Backend Service (`sulambi-backend`)

Go to **Backend Service** → **Environment** tab:

| Variable | Value | Notes |
|----------|-------|-------|
| `AUTOMAILER_EMAIL` | your-email@example.com | Your email for automated mailings |
| `AUTOMAILER_PASSW` | your-password | Email account password |
| `DEBUG` | `False` | Already set in Blueprint |

**Auto-set by Blueprint:**
- `DATABASE_URL` - From database connection
- `PORT` - From service
- `HOST` - `0.0.0.0`
- `PYTHON_VERSION` - `3.11.0`

### Frontend Service (`sulambi-frontend`)

Go to **Frontend Service** → **Environment** tab:

| Variable | Value | Notes |
|----------|-------|-------|
| `VITE_API_URI` | `https://sulambi-backend.onrender.com/api` | Replace with your backend URL |

**Important:**
- Set this **BEFORE** first build
- Format: `https://[your-backend-name].onrender.com/api`
- If you change this later, you'll need to rebuild

## Database Migration

After deployment, migrate your local SQLite data to PostgreSQL:

1. **Get External Database URL:**
   - Go to `sulambi-database` → **Connection Info**
   - Copy **External Database URL**

2. **Run Migration Script Locally:**
   ```powershell
   cd "Technology Transfer _ Sulambi VMS\Source Code\sulambi-backend-main\sulambi-backend-main"
   $env:DATABASE_URL = "postgresql://user:pass@host:port/database"
   python migrate_sqlite_to_postgresql.py
   ```

3. **Verify Migration:**
   - Check Render database or use the app to verify data

## Blueprint Structure

```yaml
services:
  - Backend (Python Web Service)
    - Auto-connects to database
    - Auto-sets port and host
  - Frontend (Static Site)
    - Needs VITE_API_URI set manually

databases:
  - PostgreSQL Database
    - Auto-connects to backend
```

## Troubleshooting

### Frontend Can't Connect to Backend

**Problem:** Frontend shows API connection errors

**Solution:**
1. Check `VITE_API_URI` is set correctly
2. Verify backend URL is correct (check backend service URL)
3. Rebuild frontend after changing `VITE_API_URI`

### Backend Database Connection Failed

**Problem:** Backend can't connect to database

**Solution:**
1. Verify database is running (check database service status)
2. Check `DATABASE_URL` is set (should be auto-set by Blueprint)
3. Verify database name matches in Blueprint

### Tables Not Created

**Problem:** Database initialized but no tables

**Solution:**
1. Check backend logs for initialization errors
2. Verify `tableInitializer.py` supports PostgreSQL (already updated)
3. Manually run: `python server.py --init` in backend shell

## Benefits of Using Blueprint

✅ **One-Click Deployment** - Deploy all services at once  
✅ **Automatic Linking** - Services automatically connect  
✅ **Version Control** - Configuration in your repo  
✅ **Easy Updates** - Update `render.yaml` and redeploy  
✅ **Reproducible** - Same setup every time  

## Updating the Blueprint

1. Edit `render.yaml` in your repository
2. Commit and push changes
3. In Render Dashboard → Blueprint → **"Apply"** again
4. Render will update services according to new configuration

## Next Steps

1. ✅ Deploy Blueprint
2. ✅ Set environment variables
3. ✅ Migrate database
4. ✅ Test application
5. ✅ Change default passwords
6. ✅ Set up custom domain (optional)
7. ✅ Configure backups

---

**Need Help?** Check the full deployment guide: `RENDER_DEPLOYMENT_GUIDE.md`















