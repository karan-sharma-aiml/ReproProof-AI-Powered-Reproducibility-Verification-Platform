# ReproProof AI Enterprise Architecture Transformation Plan

## 1. Objective

Convert the current project into a modular enterprise-grade AI platform suitable for an IIT Hackathon Grand Finale while preserving the working FastAPI backend and existing frontend flows.

This plan intentionally does not modify runtime behavior, API contracts, or business logic. It defines a future-state architecture and phased migration strategy.

---

## 2. Current Architecture Summary

### Backend

The existing backend already contains a working layered service model:

- FastAPI app factory in `backend/app/main.py`
- Route layer in `backend/app/api/routes.py`
- Configuration in `backend/app/core/config.py`
- Core exceptions in `backend/app/core/exceptions.py`
- Domain models under `backend/app/models/`
- Business logic under `backend/app/services/`
- Static analysis and verification orchestration under `backend/app/services/*`

Current active capabilities include:

- repository upload and extraction
- repository intelligence analysis
- execution planning
- sandbox execution
- verification metrics
- error analysis
- troubleshooting
- patch generation
- self-healing retry and rollback
- report generation
- analytics and health scoring

### Frontend

The frontend is a Next.js app with a dashboard-driven UI:

- app pages: home, dashboard, analytics, troubleshooting, report
- reusable UI components under `frontend/components/`
- shared hooks under `frontend/hooks/`
- API client under `frontend/services/api.ts`
- shared type definitions under `frontend/types/index.ts`

The app already demonstrates a functional product workflow, but it is organized more as a feature prototype than as a platform-grade enterprise architecture.

### Architectural Gaps

1. Service responsibility overlap
   - `RepositoryAnalysisService`, `RepositoryAIAnalyzer`, `ReproProofAgent`, and observation/orchestration modules all partially cover repository intelligence.
   - This should be consolidated under a clearer repository intelligence domain.

2. Parallel retry architectures
   - `RetryEngine` and `SmartRetryEngine` represent competing implementations for the same responsibility.
   - One canonical retry path must be chosen.

3. Mixed operational state vs source code
   - `uploads/`, `reports/`, `backups/`, temp directories, `.next`, `__pycache__`, and node install artifacts are mixed into the repo tree.
   - These should be separated from source-controlled code.

4. UI architecture drift
   - Frontend pages rely on many dashboard-specific behaviors but are not yet organized into true feature modules.
   - A feature-based architecture will improve reasoning and scalability.

5. Modular boundaries are not explicit
   - The code currently has business services, but not a consistent enterprise layering model.
   - A clear domain/application/infrastructure split is needed.

---

## 3. Target Architecture

The target architecture follows Clean Architecture with enterprise-ready separation:

### 3.1 Backend Target Architecture

```text
backend/
app/
  api/
    controllers/
    routes/
    schemas/
  core/
    config/
    constants/
    exceptions/
    logging/
    security/
    middleware/
  domain/
    entities/
    interfaces/
    value_objects/
    rules/
  application/
    use_cases/
    services/
    ports/
  infrastructure/
    database/
      repositories/
      models/
    cache/
    storage/
    external/
    sandbox/
    monitoring/
  ai/
    agents/
    llm/
    reasoning/
    embeddings/
    prompts/
    confidence/
  modules/
    repository_analysis/
    execution_engine/
    risk_engine/
    repair_engine/
    deployment_engine/
    analytics/
    health/
    monitoring/
    notification/
    audit/
  shared/
    utils/
    validators/
    types/
  tasks/
    queue/
    scheduler/
    workers/
  events/
    publishers/
    handlers/
  main.py
```

### 3.2 Frontend Target Architecture

```text
frontend/
  src/
    app/
      pages/
    features/
      dashboard/
      repository/
      deployment/
      risk/
      repair/
      analytics/
    components/
      shared/
      layout/
      ui/
    hooks/
      auth/
      repository/
      execution/
      analytics/
    services/
      api/
      repository/
      verification/
      analytics/
    store/
      slices/
      providers/
    types/
      api/
      domain/
      ui/
    utils/
    contexts/
    layouts/
    config/
    styles/
```

---

## 4. Enterprise Layers to Introduce

### 4.1 Domain Layer

Purpose: hold business rules, entities, value objects, and interfaces without any infrastructure or HTTP dependencies.

Responsible modules:

- `domain/entities/`
- `domain/value_objects/`
- `domain/interfaces/`

Examples:

- RepositoryEntity
- ExecutionResult
- VerificationReport
- RiskAssessment
- RepairRecommendation
- DeploymentConfig

### 4.2 Application Layer

Purpose: define orchestration and use cases without coupling directly to FastAPI or UI details.

Responsible modules:

- `application/use_cases/`
- `application/services/`

Examples:

- AnalyzeRepositoryUseCase
- VerifyExecutionUseCase
- GenerateRepairPlanUseCase
- BuildExecutiveSummaryUseCase
- EvaluateRiskUseCase

### 4.3 Infrastructure Layer

Purpose: implement concrete repositories, storage, external APIs, caching, sandboxes, and system integrations.

Responsible modules:

- `infrastructure/repositories/`
- `infrastructure/cache/`
- `infrastructure/storage/`
- `infrastructure/sandbox/`
- `infrastructure/external/`

Examples:

- RepositoryStore
- ReportRepository
- RedisCacheAdapter
- LocalStorageAdapter
- SandboxExecutionAdapter

### 4.4 AI Layer

Purpose: separate agent intelligence and reasoning from the rest of the application.

Responsible modules:

- `ai/agents/`
- `ai/reasoning/`
- `ai/llm/`
- `ai/prompts/`
- `ai/confidence/`
- `ai/repair/`

Examples:

- RepositoryIntelligenceAgent
- TroubleshooterAgent
- RepairPlannerAgent
- ConfidenceEngine

### 4.5 Shared / Utilities Layer

Purpose: centralized helpers that do not belong to a business domain but are used across modules.

Responsible modules:

- `shared/utils/`
- `shared/validators/`
- `shared/types/`

Examples:

- logger
- time utilities
- request parsing helpers
- file validators
- serialization helpers

---

## 5. Planned Modules and Responsibilities

### 5.1 Repository Scanner

Purpose: profile uploaded repositories and extract project metadata.

Responsibilities:

- detect language, framework, dependencies
- map file tree and entry points
- identify configuration files
- determine repository health and risk indicators
- provide structured repository intelligence output

Primary boundary:

- `modules/repository_analysis/`

### 5.2 Execution Sandbox

Purpose: isolate and execute repository runs in a controlled environment.

Responsibilities:

- prepare execution environment
- capture logs, stdio, exit codes, and execution time
- manage failures and timeout handling
- isolate file-system side effects
- emit structured execution events

Primary boundary:

- `infrastructure/sandbox/`
- `modules/execution_engine/`

### 5.3 Risk Analysis Engine

Purpose: evaluate project and execution risk before and after execution.

Responsibilities:

- classify project maturity and reproducibility risk
- score repository quality
- assess risk of patching or deployment
- surface warnings and confidence metrics

Primary boundary:

- `modules/risk_engine/`

### 5.4 Repair Recommendation Engine

Purpose: produce actionable repair plans based on root causes and execution failures.

Responsibilities:

- classify root cause categories
- map failures to remediation strategies
- generate patch suggestion metadata
- rank recommendations by confidence and cost

Primary boundary:

- `modules/repair_engine/`
- `ai/repair/`

### 5.5 Deployment Engine

Purpose: prepare and track deployment readiness of a repository or validated project.

Responsibilities:

- build deployment descriptors
- verify environment compatibility
- surface deployment risk and prerequisites
- integrate with future deployment targets

Primary boundary:

- `modules/deployment_engine/`

### 5.6 AI Agent Layer

Purpose: separate autonomous reasoning from infrastructure and business logic.

Responsibilities:

- repository reasoning
- troubleshooting reasoning
- repair planning
- confidence estimation
- future multi-agent orchestration

Primary boundary:

- `ai/agents/`
- `ai/reasoning/`

### 5.7 Repository Intelligence

Purpose: unify static and dynamic repository understanding.

Responsibilities:

- framework detection
- dependency health checks
- repository quality scoring
- execution probability analysis

Primary boundary:

- `modules/repository_analysis/`
- `ai/agents/repository_intelligence/`

### 5.8 Analytics Engine

Purpose: aggregate verification results for dashboards, reports, and executive summaries.

Responsibilities:

- totals, averages, trends, success/failure metrics
- root cause distribution
- confidence summaries
- temporal analytics

Primary boundary:

- `modules/analytics/`

### 5.9 Monitoring Engine

Purpose: monitor health, execution state, and platform operations.

Responsibilities:

- system health tracking
- request health
- pipeline progress monitoring
- alerting lifecycle

Primary boundary:

- `modules/monitoring/`

### 5.10 Notification Engine

Purpose: centralize operational notifications for UI and future alerting systems.

Responsibilities:

- UI toast events
- dashboard alerts
- platform notifications
- progress updates

Primary boundary:

- `modules/notification/`

### 5.11 Execution History

Purpose: preserve durable execution records for debugging, retry, and diagnostics.

Responsibilities:

- store attempts and stages
- track patch application events
- preserve audit trail
- support replay and analysis

Primary boundary:

- `modules/monitoring/`
- `events/`
- `infrastructure/repositories/`

### 5.12 Audit Logger

Purpose: provide centralized audit evidence for system operations.

Responsibilities:

- API audit trail
- AI reasoning logs
- execution logs
- change traces

Primary boundary:

- `core/logging/`
- `modules/audit/`

### 5.13 Health Score Engine

Purpose: compute overall health of repository execution readiness.

Responsibilities:

- repository health computation
- execution health scoring
- patch success scoring
- retry health interpretation

Primary boundary:

- `modules/health/`

### 5.14 Executive Summary Engine

Purpose: convert technical results into stakeholder-ready summaries.

Responsibilities:

- generate summary narratives
- aggregate risk and quality signals
- produce final executive-ready output

Primary boundary:

- `modules/analytics/`
- `application/use_cases/`

---

## 6. Logging Strategy

Introduce central structured logging with explicit cross-cutting concerns.

### 6.1 Logging Layers

- Central logger: single entry point for app-wide log emission
- Structured logging: JSON-like or key-value logging for analysis and monitoring
- Request logging: HTTP metadata, route, status, latency, user context
- Execution logging: repository execution lifecycle, stage transitions, runtime output
- AI logging: model reasoning prompts, confidence scores, fallback decisions
- Performance logging: latency metrics for AI tasks, execution phases, and repository analysis

### 6.2 Logging Boundaries

- `core/logging/` for log configuration and formatter setup
- `modules/monitoring/` for service-level operational logs
- `ai/` modules for reasoning and model telemetry
- `events/` for execution event publishing

---

## 7. Configuration and Global Settings

Introduce a central configuration registry and environment abstraction without breaking existing settings access.

### Proposed configuration structure

- `core/config/`
  - app_config.py
  - database_config.py
  - ai_config.py
  - logging_config.py
  - feature_flags.py
  - security_config.py
- `core/constants/`
  - app_constants.py
  - execution_status.py
  - error_codes.py
  - platform_modes.py

### Features

- environment management
- feature flags
- global settings with typed defaults
- environment-specific overrides
- readiness validation for AI and deployment features

---

## 8. Error Handling Strategy

The project should separate errors by domain and layer.

### Proposed exception hierarchy

- `core/exceptions/`
  - `AppException`
  - `ValidationException`
  - `DomainException`
  - `InfrastructureException`
  - `AIException`
  - `ExecutionException`
  - `RepositoryException`

### Global handling

- central exception middleware in FastAPI
- consistent API error envelope
- explicit domain event for failure classification
- AI failure fallback and degraded mode support

---

## 9. Background Tasks and Future Queueing

This phase is architecture-only and should not implement a queue yet.

Planned structure:

- `tasks/queue/`
- `tasks/scheduler/`
- `tasks/workers/`

Planned future integration:

- Celery
- RQ
- async background dispatch for
  - repository analysis
  - AI repair planning
  - controlling long-running verification
  - scheduled health and analytics jobs

This gives the platform a path to production-scale async work without changing current synchronous flows.

---

## 10. Caching Strategy

Prepare abstractions for:

- Redis cache
- in-memory cache
- session cache
- report cache
- repository cache

Proposed abstraction:

- `infrastructure/cache/cache_interface.py`
- `infrastructure/cache/redis_cache.py`
- `infrastructure/cache/memory_cache.py`
- `infrastructure/cache/report_cache.py`

Purpose:

- reduce repeated repository scans
- cache health scores and summaries
- store temporary execution metadata
- improve AI reasoning and dashboard responsiveness

---

## 11. Database Preparation

This project should be designed for future persistence without changing the current in-memory or file-based storage.

### Proposed repository interfaces

- `database/repositories/repository_store.py`
- `database/repositories/report_store.py`
- `database/repositories/execution_history_store.py`
- `database/repositories/audit_store.py`

### Future database adapters

- PostgreSQL adapter
- MongoDB adapter
- SQLite adapter

This remains an abstraction layer only; the current system continues to use the existing artifact-based storage model until a production persistence decision is made.

---

## 12. Dependency Injection Strategy

Refactor services toward dependency injection and interface-based wiring.

### Example boundaries

- Repository scanner depends on a repository metadata provider interface
- Execution engine depends on sandbox adapter interface
- Risk engine depends on rule evaluators and scoring services
- AI agent depends on reasoning provider interface
- Report generation depends on repository/report stores

### Goal

- reduce tight coupling
- improve testability
- enable future provider swaps
- preserve current functionality while enabling enterprise extensibility

---

## 13. AI Engine Separation

The company-grade architecture should separate AI concerns into explicit modules.

### AI modules

- `ai/reasoning/` - root cause reasoning and evidence synthesis
- `ai/planning/` - execution and repair planning
- `ai/execution/` - execution-state intelligence and evaluation
- `ai/evaluation/` - scoring and verification assessment
- `ai/repair/` - patch planning and repair proposal generation
- `ai/confidence/` - confidence scoring and calibration
- `ai/patch_generation/` - patch generation support
- `ai/repository_intelligence/` - repository analysis and evidence extraction
- `ai/troubleshooter/` - root-cause interpretation and actions
- `ai/agents/` - future multi-agent orchestration

This ensures AI logic does not bleed into the route layer or core services.

---

## 14. Frontend Transformation

### 14.1 Feature-based module layout

The dashboard should be converted from a single dashboard page pattern into feature directories.

Planned feature modules:

- `features/dashboard/`
- `features/repository/`
- `features/deployment/`
- `features/risk/`
- `features/repair/`
- `features/analytics/`

### 14.2 Frontend design principles

- no duplicated components
- one source of truth for shared UI primitives
- shared hooks for fetch logic and lifecycle behavior
- global state via provider/store patterns
- reusable API service clients per domain
- clear separation of UI, logic, and external API boundaries

### 14.3 Recommended route mapping

- `/dashboard` -> feature dashboard aggregator
- `/analytics` -> analytics feature
- `/troubleshooting` -> repair/risk feature
- `/report/:id` -> report feature

---

## 15. Migration Plan

### Phase 1 - Stabilize and isolate

- keep current APIs untouched
- identify canonical modules for repo analysis, verification, and repair
- define clear boundaries for domain/application/infrastructure
- separate generated artifacts from source-controlled code

### Phase 2 - Introduce enterprise folders

- add new directories for domain, application, infrastructure, AI, shared, tasks, and events
- move logic only by abstraction boundaries, not by ad hoc convenience
- preserve route compatibility through adapters

### Phase 3 - Consolidate duplicate logic

- unify retry engines
- choose a canonical repository intelligence pathway
- choose a canonical patch logic path
- merge overlapping analytics and health score responsibilities

### Phase 4 - Frontend feature modularization

- split dashboard into feature modules
- centralize API services, hooks, and shared UI primitives
- remove alias wrappers and compatibility-only exports

### Phase 5 - Hardening for production demo readiness

- add structured logging and monitoring
- add middleware, health checks, and request tracing
- add feature flags and central configuration
- add future database and cache abstraction ready for enterprise expansion

---

## 16. Files to Move, Merge, Split, and Keep

### Files to Keep (as canonical core)

Keep the currently working operational files as the foundation of the new architecture:

- `backend/app/main.py`
- `backend/app/api/routes.py`
- `backend/app/core/config.py`
- `backend/app/services/repository_analysis_service.py`
- `backend/app/services/repository_ai_analyzer.py`
- `backend/app/services/verification_engine.py`
- `backend/app/services/troubleshooter/service.py`
- `backend/app/services/patch_generator/patch_service.py`
- `backend/app/services/self_healing/retry_engine.py`
- `frontend/app/*.tsx`
- `frontend/services/api.ts`
- `frontend/types/index.ts`

### Files to Merge

- `RepositoryAnalysisService` + `RepositoryAIAnalyzer` + `ReproProofAgent` -> canonical repository intelligence domain
- `RetryEngine` + `SmartRetryEngine` -> single retry policy implementation
- `HealthScoreService` + `ExecutiveSummaryService` + analytics services -> canonical platform analytics domain
- duplicated card/export wrappers in `frontend/components/cards/` -> single UI exports under shared components

### Files to Split

- `routes.py` should be reduced to thin HTTP adapters and delegate to use cases
- `services/` modules should be split into application services and infrastructure adapters
- dashboard logic should be split by feature domain rather than a single monolithic command center

### Files to Move

Planned future move targets only, not immediate action:

- all domain models from `backend/app/models/` into `backend/app/domain/entities/` and `backend/app/domain/value_objects/`
- service orchestration into `backend/app/application/use_cases/`
- persistence/storage implementations into `backend/app/infrastructure/`
- AI logic into `backend/app/ai/`
- UI feature code to `frontend/src/features/*`

---

## 17. Responsibilities Mapping

| Concern | Planned Layer | Example Modules |
| --- | --- | --- |
| Repository metadata and analysis | Domain + Application + AI | repository intelligence, scanner, analyzers |
| Execution sandbox and runner | Infrastructure + Modules | sandbox, execution_engine |
| Repair and patch planning | Application + AI | repair_engine, ai/repair |
| Verification and scoring | Application + Domain | verification_engine, risk_engine |
| Dashboard and UI | Frontend features | dashboard, repository, analytics |
| AI prompts, reasoning, confidence | AI layer | ai/reasoning, ai/confidence, ai/agents |
| Monitoring and health | Modules + monitoring | health, analytics, monitoring |
| Logging and alerts | Core + modules | core/logging, audit, notification |
| Persistence and cache | Infrastructure | repositories, cache, storage |

---

## 18. Estimated Refactoring Impact

### Backend

- Low: logging, config, exception boundaries
- Medium: service layer cleanup and dependency injection
- Medium: split route responsibilities into controllers/use cases
- High: consolidate repository intelligence and retry logic
- High: move operational state to infrastructure boundaries

### Frontend

- Medium: feature decomposition
- Medium: shared hook and API layer cleanup
- Low to Medium: component deduplication and layout normalization

### Overall impact

- Estimated refactor complexity: Medium
- Estimated delivery risk: Medium, if kept incremental
- Estimated production readiness gain: High

---

## 19. Risk Level

### Low Risk

- logging centralization
- config abstraction
- folder restructuring for non-runtime code
- frontend component cleanup

### Medium Risk

- consolidating repository intelligence modules
- abstracting storage and cache interfaces
- converting route logic into use cases
- introducing dependency injection without breaking the current API response contracts

### High Risk

- removing or rewriting retry orchestration without preserving failure recovery semantics
- changing current report-generation contracts
- altering backend execution flow or verification outputs

---

## 20. Recommended Execution Order

1. Stabilize canonical responsibilities
2. Add enterprise folders without moving runtime code yet
3. Split route and service responsibilities into application use cases
4. Consolidate repository intelligence and retry logic
5. Introduce AI, monitoring, configuration, and logging abstractions
6. Reorganize frontend into features with shared primitives
7. Add future database/cache interfaces and async task system stubs
8. Validate the app against current API flows and dashboard behavior

---

## 21. Final Recommendation

The project is already functionally strong and should not be rewritten. The best enterprise transformation is a layered refactor that preserves runtime behavior while progressively introducing:

- domain/application/infrastructure separation
- modular AI architecture
- centralized configuration and logging
- feature-based frontend organization
- repository/service/use-case boundaries
- future-ready cache and database abstractions

This approach keeps the project hackathon-ready while creating a clear upgrade path to a production-grade AI platform.

---

## 22. Strategic Conclusion

This is not a rebuild project. It is an architectural refinement project.

The correct strategy is:

- keep the working product
- formalize modular structure
- reduce duplicate responsibility
- enforce clean layering
- prepare for enterprise-grade scale and monitoring

This creates a final-round architecture story without breaking the proof-of-concept product.
