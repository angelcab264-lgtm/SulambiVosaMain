# Railway Deployment - Complete Setup Guide

## ⚠️ IMPORTANT: Root Directory Configuration

When you upload the **entire folder** `SulambiVosaMain-main` to Railway, you have **TWO options**:

---

## Option 1: Use Root Procfile (EASIEST - Recommended)

✅ **Files are already set up at the root level:**
- `Procfile` (at repository root)
- `railway.json` (at repository root)

**Steps:**
1. Upload your entire repository to Railway
2. Railway will automatically detect the `Procfile` at the root
3. **NO need to set Root Directory** - Railway will use the root
4. The Procfile will automatically navigate to the backend folder

**This is the recommended approach!**

---

## Option 2: Set Root Directory in Railway

If you prefer to set a specific root directory:

1. Go to Railway Dashboard → Your Service → **Settings**
2. Under **Root Directory**, set:
   ```
   Technology Transfer _ Sulambi VMS/Source Code/sulambi-backend-main/sulambi-backend-main
   ```
3. Railway will then use the `Procfile` in that directory

---

## 🔧 Required Environment Variables

Go to Railway Dashboard → Your Service → **Variables** tab:

| Variable | Value | Required |
|----------|-------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ Yes (if using PostgreSQL) |
| `DB_PATH` | `app/database/database.db` | ✅ Yes (if using SQLite) |
| `AUTOMAILER_EMAIL` | Your email | ✅ Yes |
| `AUTOMAILER_PASSW` | Your email password | ✅ Yes |
| `DEBUG` | `False` | Optional |
| `PORT` | (Auto-set by Railway) | ❌ No |

**Note:** Railway automatically sets `PORT` - don't override it!

---

## 🐛 Troubleshooting: Service Still Offline

### 1. Check Railway Logs
- Go to Railway Dashboard → Your Service → **Deployments**
- Click on the latest deployment → **View Logs**
- Look for errors like:
  - `ModuleNotFoundError` → Missing dependencies
  - `Port already in use` → Port conflict
  - `Database connection failed` → Check DATABASE_URL

### 2. Verify Procfile Location
- If using **Option 1**: Procfile should be at repository root
- If using **Option 2**: Procfile should be in the backend directory

### 3. Test Health Check Manually
After deployment, test:
```bash
curl https://your-app.railway.app/
```
Should return: `{"status": "online", "message": "Sulambi VMS Backend is running"}`

### 4. Common Issues

**Issue: "No Procfile found"**
- Solution: Make sure Procfile is at the root OR set Root Directory correctly

**Issue: "Module not found"**
- Solution: Check that `requirements.txt` is in the backend directory
- Verify build logs show: `pip install -r requirements.txt`

**Issue: "Port binding failed"**
- Solution: Don't set PORT manually - Railway provides it automatically
- Make sure Procfile uses `$PORT` (not a hardcoded number)

**Issue: "Database connection failed"**
- Solution: 
  - If using PostgreSQL: Add PostgreSQL service in Railway and connect it
  - If using SQLite: Set `DB_PATH` environment variable

---

## 📁 File Structure

```
SulambiVosaMain-main/                    ← Repository Root
├── Procfile                             ← Root Procfile (Option 1)
├── railway.json                         ← Root Railway config
├── Technology Transfer _ Sulambi VMS/
│   └── Source Code/
│       └── sulambi-backend-main/
│           └── sulambi-backend-main/
│               ├── server.py
│               ├── requirements.txt
│               ├── Procfile             ← Backend Procfile (Option 2)
│               └── app/
```

---

## ✅ Verification Checklist

After deployment:

- [ ] Service shows "Active" in Railway dashboard
- [ ] Health check works: `https://your-app.railway.app/`
- [ ] API endpoint works: `https://your-app.railway.app/api/`
- [ ] No errors in Railway logs
- [ ] Environment variables are set correctly

---

## 🚀 Quick Start

1. **Push code to GitHub/GitLab**
2. **Connect to Railway:**
   - New Project → Deploy from GitHub repo
   - Select your repository
3. **Set Environment Variables** (see above)
4. **Deploy** - Railway will automatically:
   - Detect Procfile
   - Install dependencies
   - Start the server

That's it! Your backend should now stay online! 🎉
