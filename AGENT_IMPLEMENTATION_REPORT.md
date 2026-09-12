# Agent Implementation Report

## Milestone

ReproProof AI now has an opt-in production multi-agent workflow built on the existing framework. The implementation preserves all existing APIs and keeps the legacy upload, repository analysis, execution, repair, and reporting paths unchanged.

## Files created

- `backend/app/ai/framework/base_agent.py`
- `backend/app/ai/agents.py`
- `backend/app/ai/composition.py`
- `backend/app/api/agent_routes.py`

The existing framework files were extended only where required for runtime injection, dependency batches, timeouts, cancellation reporting, and optional parallel scheduling:

- `backend/app/ai/framework/__init__.py`
- `backend/app/ai/framework/workflow.py`
- `backend/app/ai/framework/scheduler.py`
- `backend/app/ai/framework/orchestrator.py`

## Agents implemented

1. Repository Agent: delegates risk heatmap, dependency graph, health, and environment analysis to `ResearchIntelligenceService`.
2. Research Paper Agent: delegates document processing and optional research questions to injected document/LLM providers.
3. Dataset Agent: delegates dataset inspection to the research service.
4. Execution Agent: records existing execution evidence and requires a sandbox provider for future execution.
5. Security Agent: consumes repository security evidence from shared context.
6. Repair Agent: creates evidence-linked repair suggestions and delegates patch generation to the existing patch service.
7. Reviewer Agent: reviews collected context sections and reports consistency status.
8. Judge Agent: produces a final evidence-based verdict and score.

Every agent inherits `BaseAgent`, uses `AgentContext`, receives the workflow `MessageBus` and `AgentMemory`, publishes context events, returns a confidence score, and generates explainable output.

## Workflow

The canonical workflow is defined in `default_reproducibility_workflow()`:

```text
Repository
  -> Research Paper
  -> Dataset
  -> Execution
  -> Security
  -> Repair
  -> Reviewer
  -> Judge
```

The workflow is configurable. `WorkflowStep` supports dependencies, retries, and timeouts. `Workflow.parallel=True` enables dependency-batch concurrency for independent branches.

## New API

- `POST /agents/workflows/reproducibility/{repository_id}`

This endpoint is opt-in and runs against an already extracted repository inside the configured upload directory. It returns agent results, confidence scores, and the actual event history.

## Orchestration capabilities

- Dynamic workflow graph ordering through `WorkflowEngine`
- Agent registry and fresh-instance factory creation
- Sequential execution by default
- Parallel execution for independent dependency batches
- Context and memory injection
- Per-step retries
- Per-step timeout handling
- Cancellation-safe workflow failure events
- Agent failure recovery through bounded retries
- Event publication for workflow, agent, and context lifecycle changes
- Result aggregation and per-agent duration/CPU/attempt metrics

## Architecture decisions

- Agents never import or invoke one another.
- Existing business services remain the source of truth; agents act as orchestration adapters.
- Provider-dependent capabilities never fabricate results. Missing LLM, OCR, or sandbox providers are represented explicitly.
- The new workflow is not automatically inserted into upload processing, preventing behavior changes to existing endpoints.
- Repository paths are confined to the configured upload directory at the new API boundary.

## Validation

Passed:

- Compilation of `app/ai` and `app/api/agent_routes.py`
- Existing FastAPI startup/import check
- Agent inheritance check for all eight agents
- Complete eight-agent workflow smoke test
- ContextUpdated event assertion
- Additive workflow route registration check
- VS Code diagnostics for touched application files

The full pytest suite could not be executed because `pytest` is not installed in the configured environment.

## Remaining production work

- Inject real OCR, LLM, novelty, and sandbox providers through deployment composition.
- Replace the current in-process memory/event history with durable stores where required.
- Add individual pytest suites for each agent and workflow failure mode.
- Connect workflow results to final report persistence after regression coverage is established.
- Add explicit JSON, Parquet, and Excel dataset parser adapters.

## Risk boundary

The current Execution Agent is intentionally non-executing until a `SandboxProvider` is configured. This prevents arbitrary repository code from running on the application host.
