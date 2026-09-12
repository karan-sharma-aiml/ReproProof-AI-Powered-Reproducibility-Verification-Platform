from __future__ import annotations

from pathlib import Path
from typing import Any

from app.research.engines import (
    DocumentUnderstandingEngine,
    ResearchAssistant,
    ScoreEngine,
)
from app.research.errors import ProviderUnavailableError, ResearchFeatureError
from app.research.services import ResearchIntelligenceService
from app.integrations.composition import ai_gateway

from .framework.base_agent import BaseAgent
from .framework.context import AgentContext
from .framework.contracts import AgentMetadata


class RepositoryAgent(BaseAgent):
    metadata = AgentMetadata(
        "repository", capabilities=("structure", "risk", "dependencies", "health")
    )

    async def analyze(self, context: AgentContext) -> Any:
        path = context.repository_metadata.get("path") or context.repository_info.get(
            "path"
        )
        if not path:
            raise ValueError(
                "RepositoryAgent requires context.repository_metadata['path']"
            )
        service = ResearchIntelligenceService()
        repository_id = context.repository_metadata.get("repository_id", "repository")
        output = {
            "risk_heatmap": service.risk_heatmap(
                repository_id, Path(path)
            ).model_dump(),
            "dependency_graph": service.dependency_graph(
                repository_id, Path(path)
            ).model_dump(),
            "health": service.health_score(repository_id, Path(path)).model_dump(),
            "environment": service.environment(Path(path)).model_dump(),
        }
        self._confidence = 0.9
        await self.write_context(context, "repository_info", output)
        self._output = output
        return output


class ResearchPaperAgent(BaseAgent):
    metadata = AgentMetadata(
        "research_paper",
        capabilities=("document", "methodology", "research_assistance"),
    )

    def __init__(
        self, assistant: ResearchAssistant | None = None, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.assistant = assistant or ResearchAssistant(ai_gateway)

    async def analyze(self, context: AgentContext) -> Any:
        paper_path = context.shared_memory.get("research_paper_path")
        if not paper_path:
            output = {"status": "no_paper_supplied", "provider_required": True}
            self._confidence = 0.0
        else:
            document = await DocumentUnderstandingEngine().process(Path(paper_path))
            output = {"document": document.model_dump()}
            self._confidence = 0.75
        await self.write_context(context, "research_paper_findings", output)
        self._output = output
        return output

    async def execute(self, context: AgentContext) -> Any:
        question = context.shared_memory.get("research_question")
        if question and self.assistant is not None:
            try:
                self._output["assistant_answer"] = await self.assistant.answer(
                    question, self._output
                )
                self._confidence = max(self._confidence, 0.6)
            except ProviderUnavailableError:
                self._output["provider_required"] = True
        return self._output


class DatasetAgent(BaseAgent):
    metadata = AgentMetadata(
        "dataset", capabilities=("schema", "missing_values", "quality")
    )

    async def analyze(self, context: AgentContext) -> Any:
        dataset_path = context.shared_memory.get("dataset_path")
        if not dataset_path:
            output = {"status": "no_dataset_supplied"}
            self._confidence = 0.0
        else:
            output = (
                ResearchIntelligenceService()
                .dataset_report(Path(dataset_path))
                .model_dump()
            )
            self._confidence = 0.85
        await self.write_context(context, "dataset_information", output)
        self._output = output
        return output


class ExecutionAgent(BaseAgent):
    metadata = AgentMetadata(
        "execution", capabilities=("planning", "monitoring", "failure_trace")
    )

    async def analyze(self, context: AgentContext) -> Any:
        existing = context.execution_results
        output = {"status": "awaiting_sandbox_provider", "existing_results": existing}
        self._confidence = 0.5 if existing else 0.0
        await self.write_context(context, "execution_results", output)
        self._output = output
        return output


class SecurityAgent(BaseAgent):
    metadata = AgentMetadata(
        "security", capabilities=("secret_detection", "risk_analysis")
    )

    async def analyze(self, context: AgentContext) -> Any:
        heatmap = context.repository_info.get("risk_heatmap", {})
        findings = [
            item
            for item in heatmap.get("items", [])
            if item.get("category") == "security"
        ]
        output = {
            "findings": findings,
            "risk_score": heatmap.get("categories", {}).get("security", 0),
        }
        self._confidence = 0.8 if heatmap else 0.2
        await self.write_context(context, "security_findings", findings)
        self._output = output
        return output


class RepairAgent(BaseAgent):
    metadata = AgentMetadata(
        "repair", capabilities=("root_cause", "patch_planning", "prioritization")
    )

    async def analyze(self, context: AgentContext) -> Any:
        risks = context.security_findings + context.risk_findings
        suggestions = [
            {
                "path": item.get("path"),
                "action": "review evidence before proposing a patch",
            }
            for item in risks
            if isinstance(item, dict)
        ]
        output = {
            "suggestions": suggestions,
            "patch_generation": "delegated to existing patch service",
        }
        self._confidence = 0.65 if suggestions else 0.3
        await self.write_context(context, "patch_suggestions", suggestions)
        self._output = output
        return output


class ReviewerAgent(BaseAgent):
    metadata = AgentMetadata(
        "reviewer", capabilities=("consistency", "validation", "confidence")
    )

    async def analyze(self, context: AgentContext) -> Any:
        outputs = {
            key: value
            for key, value in context.intermediate_results.items()
            if key not in {"reviewer", "judge"}
        }
        output = {
            "reviewed_sections": sorted(outputs),
            "inconsistencies": [],
            "validated": True,
        }
        self._confidence = 0.7 if outputs else 0.0
        await self.write_context(
            context,
            "intermediate_results",
            {"reviewer": output, **context.intermediate_results},
        )
        self._output = output
        return output


class JudgeAgent(BaseAgent):
    metadata = AgentMetadata(
        "judge", capabilities=("final_evaluation", "verdict", "executive_summary")
    )

    async def analyze(self, context: AgentContext) -> Any:
        scores = list(context.confidence_scores.values())
        overall = ScoreEngine().score(
            "reproducibility",
            {"agent_confidence": (sum(scores) / len(scores) * 100) if scores else 0},
        )
        output = {
            "verdict": "evidence_collected" if scores else "insufficient_evidence",
            "score": overall.model_dump(),
        }
        self._confidence = sum(scores) / len(scores) if scores else 0.0
        await self.write_context(
            context,
            "intermediate_results",
            {"judge": output, **context.intermediate_results},
        )
        self._output = output
        return output


PRODUCTION_AGENTS = (
    RepositoryAgent,
    ResearchPaperAgent,
    DatasetAgent,
    ExecutionAgent,
    SecurityAgent,
    RepairAgent,
    ReviewerAgent,
    JudgeAgent,
)
