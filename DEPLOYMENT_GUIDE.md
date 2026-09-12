# Deployment Guide

## Local

1. Create and activate the Python virtual environment.
2. Install `backend/requirements.txt`.
3. Start the API with `uvicorn app.main:app --reload` from `backend`.
4. Install frontend dependencies in `frontend` and run `npm run dev`.
5. Use `http://localhost:3000/demo` for the judge flow.

## Containers

Use the existing root `docker-compose.yml` for backend, frontend, and Redis. Existing Dockerfiles and health checks remain the supported baseline.

## Production composition

Configure environment-driven secrets, trusted hosts, CORS, durable stores, external AI providers, Redis-backed queues/cache, isolated sandbox execution, telemetry exporters, image scanning, SBOM generation, and signed artifacts before multi-instance deployment.

## Health

Use `/health/live`, `/health/ready`, and `/metrics` for deployment probes and monitoring.
