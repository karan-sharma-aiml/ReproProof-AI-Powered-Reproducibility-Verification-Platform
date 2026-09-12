from __future__ import annotations

from typing import Any

from .models import DeploymentProfile


class DockerArtifactBuilder:
    def backend_dockerfile(self) -> str:
        return """FROM python:3.13-slim\nENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\nWORKDIR /app\nCOPY backend/requirements.txt ./requirements.txt\nRUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 appuser\nCOPY backend/app ./app\nRUN mkdir -p uploads reports && chown -R appuser:appuser /app\nUSER appuser\nEXPOSE 8000\nHEALTHCHECK CMD python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')\"\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n"""

    def frontend_dockerfile(self) -> str:
        return """FROM node:22-alpine AS build\nWORKDIR /app\nCOPY package*.json ./\nRUN npm ci\nCOPY . .\nRUN npm run build\nFROM node:22-alpine AS runtime\nWORKDIR /app\nENV NODE_ENV=production\nCOPY --from=build /app/.next ./.next\nCOPY --from=build /app/package*.json ./\nRUN npm ci --omit=dev && addgroup -S appgroup && adduser -S appuser -G appgroup\nUSER appuser\nEXPOSE 3000\nCMD [\"npm\", \"start\"]\n"""

    def compose(
        self, profile: DeploymentProfile, mode: str = "production"
    ) -> dict[str, Any]:
        services: dict[str, Any] = {
            "backend": {
                "image": profile.backend_image,
                "ports": ["8000:8000"],
                "restart": "unless-stopped",
                "healthcheck": {
                    "test": [
                        "CMD",
                        "python",
                        "-c",
                        "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')",
                    ]
                },
            },
            "frontend": {
                "image": profile.frontend_image,
                "ports": ["3000:3000"],
                "depends_on": ["backend"],
                "restart": "unless-stopped",
            },
            "redis": {
                "image": "redis:7-alpine",
                "command": "redis-server --appendonly yes",
                "volumes": ["redis-data:/data"],
                "restart": "unless-stopped",
            },
        }
        if mode in {"worker", "monitoring"}:
            services["worker"] = {
                "image": profile.backend_image,
                "command": ["python", "-m", "app.worker"],
                "depends_on": ["redis"],
            }
        if mode == "monitoring":
            services["prometheus"] = {
                "image": "prom/prometheus:latest",
                "ports": ["9090:9090"],
            }
            services["grafana"] = {
                "image": "grafana/grafana:latest",
                "ports": ["3001:3000"],
            }
        return {"services": services, "volumes": {"redis-data": {}}}
