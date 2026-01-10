# Quick Deployment Steps - Render

## 🚀 Quick Start (5 Steps)

### 1. Create PostgreSQL Database on Render
- Go to Render Dashboard → New + → PostgreSQL
- Name: `sulambi-database`
- Copy the **External Database URL** (for migration)

### 2. Deploy Backend
- Go to Render Dashboard → New + → Web Service
- Connect GitHub repo
- Use `render.yaml` (auto-configures everything)
- Or manually:
  - Root: `Technology Transfer _ Sulambi VMS/Source Code/sulambi-backend-main/sulambi-backend-main`
  - Build: `pip install -r requirements.txt`
  - Start: `chmod +x start.sh && ./start.sh`
  - Set `DATABASE_URL` from database connection

### 3. Migrate Data (Local Machine)
```powershell
cd "Technology Transfer _ Sulambi VMS\Source Code\sulambi-backend-main\sulambi-backend-main"
$env:DATABASE_URL = "postgresql://user:pass@host:port/db"  # External URL
python migrate_sqlite_to_postgresql.py
```

### 4. Deploy Frontend
- Go to Render Dashboard → New + → Static Site
- Connect GitHub repo
- Root: `Technology Transfer _ Sulambi VMS/Source Code/sulambi-frontend-main/sulambi-frontend-main`
- Build: `chmod +x build.sh && ./build.sh`
- Publish: `dist`
- Set `VITE_API_URI` = `https://your-backend.onrender.com/api`

### 5. Verify
- Backend: `https://your-backend.onrender.com/api`
- Frontend: `https://your-frontend.onrender.com`
- Login with: `Admin` / `sulambi@2024`

## 📝 Important Notes

- **Database URLs:**
  - Internal URL: For services on Render (backend)
  - External URL: For local migration script

- **First Deploy:** Backend will auto-create tables on startup

- **Migration:** Run after backend is deployed (tables must exist)

## 🔧 What Was Updated

✅ `tableInitializer.py` - Now supports PostgreSQL syntax
✅ `connection.py` - Already supports PostgreSQL
✅ `migrate_sqlite_to_postgresql.py` - Ready to use
✅ `render.yaml` - Configured for deployment

## 📚 Full Guide

See `RENDER_DEPLOYMENT_GUIDE.md` for detailed instructions.




