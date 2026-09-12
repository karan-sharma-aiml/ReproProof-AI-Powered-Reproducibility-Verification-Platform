# System Architecture

```mermaid
flowchart TB
  UI[Next.js dashboard, demo, executive, knowledge, performance] --> API[FastAPI additive APIs]
  API --> Core[Upload, verification, repair, reporting]
  API --> Agents[Agent registry and orchestrator]
  API --> Research[Research intelligence and paper engines]
  API --> Judge[Explainable judge]
  API --> Graph[Knowledge graph and RAG]
  API --> Ops[Security, observability, performance]
  API --> Deploy[Deployment contracts and artifacts]
  Agents --> Gateway[AI provider gateway]
  Graph --> Memory[Existing memory and vector ports]
  Ops --> Providers[Redis, telemetry, sandbox, database ports]
```

The application follows additive bounded contexts. HTTP routes compose application services; provider ports isolate external systems; local adapters keep development and demo execution deterministic.
