# Phase 16 - Enterprise Knowledge Graph, RAG and AI Memory Platform

## Architecture

Phase 16 adds two additive bounded contexts:

- `backend/app/knowledge_graph`
- `backend/app/rag`

The knowledge graph reuses the existing `app.memory` graph storage boundary and its thread-safe in-memory graph store. The RAG engine reuses the existing AI gateway for answer generation and remains functional with deterministic lexical retrieval when no external provider is configured. No vendor SDK or new API key is required.

Managed workflows now publish workflow and agent entities into the shared graph, so agents share one knowledge representation in addition to the existing `AgentContext` and `AgentMemory`.

## Graph Model

Supported entity types:

- Repository, Project, Research Paper, Dataset
- Agent, User, Workflow, Score, Judge Result
- Dependency, File, Function, Class
- Experiment, Publication, Evidence, Recommendation

Supported relationship types:

- `depends_on`
- `generated_by`
- `reviewed_by`
- `related_to`
- `cites`
- `imports`
- `extends`
- `executes`
- `evaluates`
- `references`
- `contains`

The graph engine provides entity upsert, relationship upsert, graph retrieval, ranked text search, breadth-first neighbor traversal, centrality statistics, and repository AST indexing. Python files produce class, function, import, dependency, file, and repository entities.

## RAG Pipeline

```text
Document or repository
        |
Document intelligence
(PDF/Markdown/DOCX/TXT/CSV/JSON/code)
        |
Metadata + sections + citations + chunks
        |
Lexical retrieval / vector-ready provider boundary
        |
Ranked context and source attribution
        |
AI Gateway answer generation
        |
Answer + confidence + evidence + citations + related documents
```

RAG supports:

- Chunking
- Metadata extraction
- Sections, references, citations, CSV columns/rows, JSON keys
- DOCX text extraction through standard-library ZIP/XML handling
- Ranked retrieval
- Source attribution
- Citation tracking
- Explainable context assembly
- AI Gateway answer generation
- Credential-free local retrieval fallback
- Repository indexing for Python, Markdown, text, JSON, CSV, TypeScript, and TSX files

## APIs

### Knowledge graph

- `POST /knowledge/index`
- `GET /knowledge/entities`
- `GET /knowledge/graph`
- `GET /knowledge/search`
- `GET /knowledge/neighbors`
- `GET /knowledge/relationships`
- `POST /knowledge/relationships`
- `GET /knowledge/statistics`

### RAG

- `POST /rag/index`
- `POST /rag/index/repository`
- `GET /rag/search`
- `POST /rag/query`
- `GET /rag/context`
- `GET /rag/citations`
- `GET /rag/sources`

All APIs are additive and existing API contracts remain unchanged.

## Explainability

Every generated `RAGAnswer` includes:

- Answer text
- Confidence score
- Source documents
- Evidence excerpts
- Retrieved context chunks
- Citation objects with source URI, title, quote, and score
- Related documents
- Provider identity

## Provider Compatibility

The implementation uses:

- Existing `AI Gateway` for answer generation
- Existing provider-neutral embedding and vector boundaries as extension points
- Existing memory graph store for graph persistence
- Existing research document conventions and upload-root security boundary

No direct vendor calls were added.

## Validation

Passed:

- Compilation of knowledge graph and RAG modules
- Full Phase 16 module compilation
- FastAPI startup
- Legacy route registration checks
- Provider and orchestration compatibility checks
- Repository AST indexing
- Graph search
- Graph traversal and neighbor discovery
- Centrality statistics
- RAG chunking and retrieval
- Citation and source attribution validation
- AI Gateway answer generation
- Agent workflow to shared knowledge graph bridge
- Frontend production build
- Diagnostics for touched graph, RAG, route, and application modules

## Compatibility

Existing research, provider, memory, orchestration, deployment, observability, security, judge, execution, and dashboard contracts were preserved. No existing dashboard behavior was changed. An additive `/knowledge` frontend route now provides graph exploration and RAG inspection using the new backend contracts.

## Remaining Production Work

- Durable graph database adapter for multi-instance deployments
- Durable chunk/vector index and ingestion jobs
- Concrete vector provider SDK adapters through deployment configuration
- Advanced PDF layout, table, figure, and OCR extraction adapters
- Hybrid lexical/vector ranking calibration
- Tenant-aware graph and source authorization
- Citation quality evaluation and answer groundedness scoring
- Streaming RAG responses through the existing gateway
- Additional deep-link navigation and repository-specific graph/RAG drill-down views
