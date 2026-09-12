# API Reference

## Existing core

`GET /health`, `POST /upload`, `GET /repository/{id}`, `GET /analysis/{id}`, `GET /report/{id}`, `GET /analytics`, troubleshooting, repair, rollback, and execution stream routes remain supported.

## Enterprise APIs

- `/research/*` - repository, paper, dataset, environment, scores
- `/agents/*` and `/orchestrator/*` - agent workflows and lifecycle control
- `/providers/*` - provider discovery, health, models, capabilities, test
- `/memory/*` - records, search, context, graph
- `/knowledge/*` - entities, graph, search, neighbors, relationships, indexing
- `/rag/*` - indexing, search, query, context, citations, sources
- `/observability/*` - metrics, health, platform, system, traces, telemetry
- `/performance/*` - cache, resources, queues, latency, workers, benchmarks
- `/deployment/*` - profiles, plans, validation, reports, Kubernetes, Docker, pipelines
- `/platform/*` - overview, README, architecture, PDF, PPTX, Markdown, JSON, CSV exports
- `/demo/*` - sample repositories, datasets, papers, run, overview, report

OpenAPI remains available at `/docs` and `/redoc`.
