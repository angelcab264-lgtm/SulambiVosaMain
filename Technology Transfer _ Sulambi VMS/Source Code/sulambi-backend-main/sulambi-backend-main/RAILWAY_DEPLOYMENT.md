# Railway Deployment Guide for Sulambi VMS Backend

## ✅ What Was Fixed

The backend was always showing as offline on Railway because:

1. **Missing Health Check Endpoint** - Railway checks the root `/` endpoint to determine if your service is online
2. **Missing Procfile** - Railway needs a Procfile to know how to start your application
3. **Port Configuration** - The server now properly binds to `0.0.0.0:$PORT` for Railway

## 📋 Files Created/Updated

1. **`Procfile`** - Tells Railway how to start your app with Gunicorn
2. **`railway.json`** - Railway configuration file (optional but recommended)
3. **`server.py`** - Added health check endpoints at `/` and `/health`

## 🚀 Deployment Steps

### Step 1: Connect Your Repository to Railway

1. Go to [Railway.app](https://railway.app) and sign in
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will automatically detect the backend

### Step 2: Configure Environment Variables

Go to your service → **Variables** tab and add:

| Variable | Value | Required |
|----------|-------|----------|
| `DATABASE_URL` | Your PostgreSQL connection string | ✅ Yes (if using PostgreSQL) |
| `DB_PATH` | `app/database/database.db` | ✅ Yes (if using SQLite) |
| `AUTOMAILER_EMAIL` | Your email for automated mailings | ✅ Yes |
| `AUTOMAILER_PASSW` | Your email password | ✅ Yes |
| `DEBUG` | `False` | Optional (recommended for production) |
| `HOST` | `0.0.0.0` | Optional (Railway sets this automatically) |
| `PORT` | (Auto-set by Railway) | ❌ No (Railway provides this) |

**Important Notes:**
- Railway automatically provides the `PORT` environment variable
- If using PostgreSQL, add a PostgreSQL service in Railway and connect it
- The `DATABASE_URL` will be automatically set if you connect a PostgreSQL database

### Step 3: Set Root Directory (if needed)

If your backend is in a subdirectory:
1. Go to your service → **Settings**
2. Set **Root Directory** to: `Technology Transfer _ Sulambi VMS/Source Code/sulambi-backend-main/sulambi-backend-main`

### Step 4: Deploy

Railway will automatically:
1. Detect the `Procfile`
2. Install dependencies from `requirements.txt`
3. Run database initialization (`python server.py --init`)
4. Start the server with Gunicorn

## 🔍 Health Check Endpoints

After deployment, you can verify your backend is online:

- **Root endpoint:** `https://your-app.railway.app/`
- **Health check:** `https://your-app.railway.app/health`
- **API endpoint:** `https://your-app.railway.app/api/`

All should return JSON responses indicating the service is online.

## 🐛 Troubleshooting

### Backend Still Shows Offline

1. **Check Logs:**
   - Go to your service → **Deployments** → Click on latest deployment → **View Logs**
   - Look for errors during startup

2. **Common Issues:**
   - **Missing dependencies:** Check if `requirements.txt` includes all packages
   - **Database connection errors:** Verify `DATABASE_URL` is set correctly
   - **Port binding errors:** Railway sets `PORT` automatically, don't override it

3. **Verify Health Check:**
   ```bash
   curl https://your-app.railway.app/
   ```
   Should return: `{"status": "online", "message": "Sulambi VMS Backend is running"}`

### Database Issues

If using PostgreSQL:
- Make sure PostgreSQL service is added to your Railway project
- The `DATABASE_URL` should be automatically connected
- Run migrations if needed: `python server.py --init`

If using SQLite:
- Make sure `DB_PATH` is set correctly
- Note: SQLite may have issues with Railway's file system (PostgreSQL recommended)

## 📝 Procfile Details

The Procfile contains:
```
web: python server.py --init || true && gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 server:app
```

This:
- Initializes the database (or continues if already initialized)
- Starts Gunicorn with 2 workers
- Binds to `0.0.0.0:$PORT` (Railway's port)
- Uses a 120-second timeout

## ✅ Verification Checklist

- [ ] Repository connected to Railway
- [ ] Environment variables set (especially `AUTOMAILER_EMAIL` and `AUTOMAILER_PASSW`)
- [ ] Database configured (PostgreSQL or SQLite)
- [ ] Deployment successful (check logs)
- [ ] Health check endpoint returns `{"status": "online"}`
- [ ] API endpoint accessible at `/api/`

## 🔗 Next Steps

After backend is deployed:
1. Get your Railway backend URL (e.g., `https://your-app.railway.app`)
2. Update your frontend to point to: `https://your-app.railway.app/api`
3. Deploy your frontend (if needed)
