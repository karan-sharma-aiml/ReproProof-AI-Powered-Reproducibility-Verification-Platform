from __future__ import annotations

from pathlib import Path

from app.judge.models import JudgeRequest
from app.judge.service import JudgeEngine
from app.memory.engine import MemoryEngine
from app.research.services import ResearchIntelligenceService

from .models import (
    ArchitectureArtifact,
    DecisionNode,
    EnterpriseOverview,
    ReadmeArtifact,
    Recommendation,
    WorkflowNode,
)


class ShowcaseService:
    """Composes judge-ready presentation artifacts from existing evidence services."""

    def __init__(
        self,
        judge: JudgeEngine | None = None,
        research: ResearchIntelligenceService | None = None,
        memory: MemoryEngine | None = None,
    ) -> None:
        self.judge = judge or JudgeEngine()
        self.research = research or ResearchIntelligenceService()
        self.memory = memory or MemoryEngine()

    async def overview(
        self, repository_id: str, repository_path: Path
    ) -> EnterpriseOverview:
        report = await self.judge.evaluate(
            JudgeRequest(repository_id=repository_id), repository_path
        )
        scores = {name: item.score for name, item in report.scores.items()}
        names = (
            "Repository",
            "Research",
            "Dataset",
            "Execution",
            "Security",
            "Repair",
            "Reviewer",
            "Judge",
        )
        workflow = [
            WorkflowNode(
                id=name.lower(),
                label=name,
                status="complete" if index < 2 else "pending",
                confidence=report.confidence,
            )
            for index, name in enumerate(names)
        ]
        recommendations = [
            Recommendation(
                title="Improve evidence coverage",
                reason=item.limitations[0],
                priority="high" if item.score < 45 else "medium",
                source=name,
            )
            for name, item in report.scores.items()
            if item.limitations
        ]
        graph = self.memory.graph(repository_id).model_dump()
        tree = DecisionNode(
            label="Final verdict",
            value=report.verdict.value,
            children=[
                DecisionNode(
                    label=name.replace("_", " ").title(), value=f"{item.score:.0f}/100"
                )
                for name, item in report.scores.items()
            ],
        )
        return EnterpriseOverview(
            repository_id=repository_id,
            verdict=report.verdict.value,
            overall_score=report.overall_score,
            confidence=report.confidence,
            scores=scores,
            workflow=workflow,
            decision_tree=tree,
            recommendations=recommendations,
            knowledge_graph=graph,
        )

    def readme(self, repository_id: str, repository_path: Path) -> ReadmeArtifact:
        health = self.research.health_score(repository_id, repository_path)
        environment = self.research.environment(repository_path)
        content = f"# {repository_id}\n\n## Environment\n\nLanguages: {', '.join(environment.languages) or 'Not detected'}\n\nPackage managers: {', '.join(environment.package_managers) or 'Not detected'}\n\n## Health\n\nRepository health score: {health.overall}/100\n\n## Setup\n\nRecreate the detected environment using the package managers and runtime files listed above.\n"
        return ReadmeArtifact(
            repository_id=repository_id,
            content=content,
            generated_from=[
                "repository files",
                "environment detection",
                "health analysis",
            ],
        )

    def architecture(
        self, repository_id: str, repository_path: Path
    ) -> ArchitectureArtifact:
        graph = self.research.dependency_graph(repository_id, repository_path)
        lines = ["flowchart TD"]
        for node in graph.nodes[:80]:
            lines.append(f"    {self._safe_id(node.id)}[{node.label}]")
        for edge in graph.edges[:160]:
            lines.append(
                f"    {self._safe_id(edge.source)} --> {self._safe_id(edge.target)}"
            )
        return ArchitectureArtifact(
            repository_id=repository_id, content="\n".join(lines)
        )

    @staticmethod
    def _safe_id(value: str) -> str:
        return "node_" + "".join(
            character if character.isalnum() else "_" for character in value
        )
