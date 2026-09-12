# ReproProof Deployment Guide

## Backend Deployment (Render)

### Prerequisites
- Python 3.13+
- All dependencies in requirements.txt installed

### Render Setup
1. Connect your GitHub repository to Render
2. Create new Web Service with these settings:
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `backend/`
   - **Environment**: Python 3.13

### Environment Variables (Render)
```
APP_ENV=production
DEBUG=false
CORS_ORIGINS=["https://reproproof-frontend.vercel.app"]
HOST=0.0.0.0
PORT=$PORT (auto-set by Render)
UPLOAD_DIR=uploads
REPORTS_DIR=reports
MAX_UPLOAD_SIZE_MB=50
```

### Verification
- Health Check: `GET https://<your-backend>.onrender.com/health` → 200 OK
- API Docs: `https://<your-backend>.onrender.com/docs`

---

## Frontend Deployment (Vercel)

### Prerequisites
- Node.js 18+
- npm or yarn

### Vercel Setup
1. Connect your GitHub repository to Vercel
2. Configure with these settings:
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Root Directory**: `frontend/`

### Environment Variables (Vercel)
```
NEXT_PUBLIC_API_URL=https://<your-backend>.onrender.com
```

### Verification
- Frontend loads: `https://<your-frontend>.vercel.app/`
- Dashboard accessible: `https://<your-frontend>.vercel.app/dashboard`

---

## Environment Files

### Backend (.env or Render Secrets)
See `backend/.env.example` for all available variables.

Key production settings:
- `APP_ENV=production`
- `DEBUG=false`
- `CORS_ORIGINS` with your Vercel frontend URL
- `HOST=0.0.0.0` (required for Render)
- `PORT=$PORT` (auto-managed by Render)

### Frontend (.env.local or Vercel Secrets)
See `frontend/.env.example`

Key setting:
- `NEXT_PUBLIC_API_URL=https://<your-backend>.onrender.com`

---

## CORS Configuration

The backend accepts CORS requests from origins in the `CORS_ORIGINS` environment variable.

**Development** (localhost):
```
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:3001"]
```

**Production** (deployed):
```
CORS_ORIGINS=["https://reproproof-frontend.vercel.app"]
```

---

## Important Notes

1. **Folders Auto-Created**: Uploads and reports folders are automatically created on startup
2. **Health Check**: Both services respond to `GET /health` with HTTP 200
3. **API URLs**: All frontend requests use the `NEXT_PUBLIC_API_URL` environment variable
4. **Startup Command**: Backend uses Uvicorn with 0.0.0.0 binding for Render compatibility

---

## Files Changed

- `backend/.env.example` - Added production configuration guide
- `backend/app/core/config.py` - Added CORS documentation
- `backend/render.yaml` - Render deployment configuration
- `frontend/.env.example` - Created with API URL documentation
- `frontend/vercel.json` - Vercel deployment configuration

No business logic, AI, verification, confidence engine, or dashboard logic was modified.
