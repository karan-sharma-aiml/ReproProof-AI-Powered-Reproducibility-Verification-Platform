# IIT Hackathon Deployment Checklist

## ✅ Completed

### Backend Deployment Readiness
- [x] FastAPI configured with host=0.0.0.0
- [x] PORT read from environment variable
- [x] Startup command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [x] Upload/reports folders auto-created on startup
- [x] Health check endpoint returns HTTP 200
- [x] CORS configured for environment-based frontend URLs
- [x] `.env.example` created with production settings
- [x] `render.yaml` created with deployment config

### Frontend Deployment Readiness
- [x] All hardcoded localhost URLs replaced with `process.env.NEXT_PUBLIC_API_URL`
- [x] Files checked:
  - frontend/services/api.ts ✓
  - frontend/hooks/useExecutionStream.ts ✓
  - frontend/hooks/usePlatformProgress.ts ✓
  - frontend/components/dashboard/VerificationResultPanel.tsx ✓
- [x] `.env.example` created with API URL documentation
- [x] `vercel.json` created with build configuration
- [x] Frontend builds successfully with `npm run build`

### Environment Configuration
- [x] Backend `.env.example` documents all settings
- [x] Frontend `.env.example` documents NEXT_PUBLIC_API_URL
- [x] CORS_ORIGINS supports environment variable configuration
- [x] No secrets hardcoded in example files

### Verification Tests
- [x] Health check: GET /health → 200 OK
- [x] Upload API: POST /upload → 201 Created with upload_id
- [x] Frontend build: npm run build → successful
- [x] API URL resolution: All using process.env.NEXT_PUBLIC_API_URL

### No Breaking Changes
- [x] AI logic untouched
- [x] Confidence Engine untouched
- [x] Verification Engine untouched
- [x] Patch Generator untouched
- [x] Dashboard logic untouched
- [x] Database logic untouched
- [x] Tests untouched
- [x] Business logic untouched

---

## Files Created/Modified

### Backend
- `backend/.env.example` - Created/Updated
- `backend/app/core/config.py` - Updated (CORS documentation only)
- `backend/render.yaml` - Created

### Frontend
- `frontend/.env.example` - Created
- `frontend/vercel.json` - Created
- (No source files modified)

### Root
- `DEPLOYMENT.md` - Created
- `DEPLOYMENT_CHECKLIST.md` - This file

---

## Render Deployment Steps

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect GitHub repository
4. Configure:
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `backend/`
5. Set Environment Variables:
   ```
   APP_ENV=production
   DEBUG=false
   CORS_ORIGINS=["https://reproproof-frontend.vercel.app"]
   ```
6. Deploy

---

## Vercel Deployment Steps

1. Push code to GitHub
2. Import project on Vercel
3. Configure:
   - **Root Directory**: `frontend/`
   - **Build Command**: `npm run build`
4. Set Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://<your-backend>.onrender.com
   ```
5. Deploy

---

## Testing After Deployment

1. **Backend Health**: `GET https://<backend>.onrender.com/health`
2. **Frontend Load**: `https://<frontend>.vercel.app/`
3. **Upload**: POST ZIP to `/upload`
4. **Report**: GET `/report/{upload_id}`
5. **Dashboard**: Navigate to `/dashboard`

---

## Environment Variables Reference

### Backend (Render)
- `APP_ENV` = production
- `DEBUG` = false
- `HOST` = 0.0.0.0
- `PORT` = $PORT (auto-set)
- `CORS_ORIGINS` = ["https://your-frontend.vercel.app"]
- `UPLOAD_DIR` = uploads
- `REPORTS_DIR` = reports
- `MAX_UPLOAD_SIZE_MB` = 50

### Frontend (Vercel)
- `NEXT_PUBLIC_API_URL` = https://your-backend.onrender.com

---

## Demo URLs (Example)

- Frontend: `https://reproproof-demo.vercel.app`
- Backend API: `https://reproproof-demo.onrender.com`
- API Docs: `https://reproproof-demo.onrender.com/docs`

---

Ready for IIT Hackathon deployment! 🚀
