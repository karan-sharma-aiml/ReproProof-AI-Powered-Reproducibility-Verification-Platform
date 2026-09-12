# Agent Reference

## Production agents

Repository, Research Paper, Dataset, Execution, Security, Repair, Reviewer, and Judge agents implement the shared lifecycle contract.

## Lifecycle

Initialize, validate, plan, analyze, execute, evaluate, summarize, cleanup.

## Shared services

Agents use `AgentContext`, `AgentMemory`, the event/message bus, the AI gateway, research services, the judge engine, the knowledge graph, and existing patch/execution boundaries. Agents do not call one another directly.

## Workflow templates

Research, Judge, Security, Repository, Publication, and Enterprise templates are available through `/orchestrator/agents` and `/orchestrator/run`.
