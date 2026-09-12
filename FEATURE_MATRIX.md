# Feature Matrix

| Feature | Backend | Frontend | Status | Extension point |
| --- | --- | --- | --- | --- |
| Live AI workflow visualization | Agent events, execution stream | React Flow topology, live status | Ready | WebSocket event adapter |
| Agent communication graph | MessageBus event history | Graph-ready dashboard surface | Ready | Durable event stream |
| Repository knowledge graph | Memory graph store/API | Graph component foundation | Ready | Neo4j or graph database |
| AI decision tree | Judge decision tree DTO | Overview-ready | Ready | Interactive tree route |
| Confidence heatmap | Judge per-score confidence | KPI and chart foundation | Ready | Persisted confidence history |
| Explainable AI panels | Score explanations and limitations | Existing insight panels | Ready | Evidence drill-down UI |
| Research gap explorer | Provider capability route | API-ready | Provider required | Research corpus provider |
| Benchmark leaderboard | Benchmark result model/service | API-ready | Data contract ready | Persistent benchmark store |
| Smart recommendations | Judge/showcase recommendations | Dashboard-ready | Ready | Personalized policies |
| Auto README generator | Showcase service | Download-ready | Ready | Template strategy |
| Architecture diagram generator | Mermaid artifact generator | Download-ready | Ready | Interactive graph renderer |
| AI executive summary | Existing summary service + judge overview | Existing report UI | Ready | LLM summarization provider |
| PDF export | Existing PDF service | Existing report links | Ready | Signed artifact storage |
| PPT export | `JudgePresentationExporter` | Download endpoint ready | Ready | Branded slide templates |
| Live progress dashboard | Existing SSE/WebSocket stream | Existing monitor | Ready | Distributed progress broker |
| Multi-user readiness | Request IDs, typed ports, stateless services | Existing session-safe UI | Foundation ready | Auth, tenant isolation |
| Plugin agents | Registry, factory, BaseAgent | Agent status surface | Ready | Marketplace manifest |
| API marketplace | Additive typed routers | API-ready | Foundation ready | API versioning, auth, quotas |
| Secure execution | Sandbox runtime port and Docker specs | Existing monitor | Provider required | Docker/Firecracker/Kubernetes |
| Memory/RAG | Memory namespaces, vector ports, retrieval | API-ready | Provider optional | Embeddings/vector DB |
| DevOps observability | Metrics, health, rate limiting, audit | Operational API | Ready | Prometheus/Grafana/Otel |

## Compatibility status

Existing application routes and frontend workflows remain unchanged. New capabilities are additive and consume established service boundaries.
