# Installation Guide

## Backend

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
Push-Location backend
pip install -r requirements.txt
uvicorn app.main:app --reload
Pop-Location
```

## Frontend

```powershell
Push-Location frontend
npm ci
npm run dev
Pop-Location
```

The backend defaults to port 8000 and the frontend to port 3000. Configure `NEXT_PUBLIC_API_URL` when they are deployed separately.
