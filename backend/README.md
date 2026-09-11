# ReproProof Backend

Production-ready FastAPI backend for the ReproProof agentic AI hackathon project.

## Tech Stack

- **Python 3.12**
- **FastAPI** – async web framework
- **Uvicorn** – ASGI server
- **Pydantic v2** – data validation and settings management
- **python-multipart** – file upload support
- **GitPython** – Git repository utilities

## Project Structure

```
backend/
├── app/
│   ├── api/            # Route handlers
│   ├── core/           # Config, logging, exception handlers
│   ├── services/       # Business logic layer
│   ├── models/         # Domain models (reserved)
│   ├── schemas/        # Pydantic request/response schemas
│   ├── utils/          # Shared helper utilities
│   └── main.py         # Application factory & ASGI entry point
├── uploads/            # Uploaded ZIP files
├── reports/            # Generated reports
├── requirements.txt
├── .env.example
└── README.md
```

## Quick Start

### 1. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env as needed
```

### 4. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## API Endpoints

| Method | Path      | Description                            |
| ------ | --------- | -------------------------------------- |
| GET    | `/`       | Root – app info and docs link          |
| GET    | `/health` | Health check / liveness probe          |
| POST   | `/upload` | Upload a ZIP file                      |
| GET    | `/status` | System status with upload inventory    |

### Upload Example

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@my_project.zip"
```

**Success Response** (`201 Created`):

```json
{
  "success": true,
  "message": "File uploaded successfully.",
  "data": {
    "upload_id": "a1b2c3d4e5f6",
    "original_filename": "my_project.zip",
    "saved_filename": "a1b2c3d4e5f6_20260911T120000Z_my_project.zip",
    "size_bytes": 102400,
    "uploaded_at": "2026-09-11T12:00:00+00:00"
  }
}
```

## Interactive Docs

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Environment Variables

| Variable            | Default                                              | Description                    |
| ------------------- | ---------------------------------------------------- | ------------------------------ |
| `APP_NAME`          | `ReproProof`                                         | Application display name       |
| `APP_VERSION`       | `1.0.0`                                              | Semantic version               |
| `APP_ENV`           | `development`                                        | Environment label              |
| `DEBUG`             | `true`                                               | Enable debug logging           |
| `HOST`              | `0.0.0.0`                                            | Server bind address            |
| `PORT`              | `8000`                                               | Server bind port               |
| `CORS_ORIGINS`      | `["http://localhost:3000","http://localhost:5173"]`   | JSON array of allowed origins  |
| `UPLOAD_DIR`        | `uploads`                                            | Directory for uploaded files    |
| `REPORTS_DIR`       | `reports`                                             | Directory for generated reports |
| `MAX_UPLOAD_SIZE_MB`| `50`                                                 | Maximum upload size in MB      |

## License

MIT
