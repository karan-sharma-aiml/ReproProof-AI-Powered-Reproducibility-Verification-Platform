from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.showcase.models import (
    DecisionNode,
    EnterpriseOverview,
    Recommendation,
    WorkflowNode,
)

DEMO_REPOSITORY_ID = "demo-reproproof"


def demo_overview() -> EnterpriseOverview:
    return EnterpriseOverview(
        repository_id=DEMO_REPOSITORY_ID,
        verdict="PASS",
        overall_score=87.4,
        confidence=0.91,
        scores={
            "repository": 92,
            "research_integrity": 88,
            "reproducibility": 85,
            "security": 90,
            "publication_readiness": 82,
            "maintainability": 87,
        },
        workflow=[
            WorkflowNode(
                id="repository", label="Repository", status="complete", confidence=0.98
            ),
            WorkflowNode(
                id="research", label="Research", status="complete", confidence=0.91
            ),
            WorkflowNode(
                id="security", label="Security", status="complete", confidence=0.94
            ),
            WorkflowNode(id="judge", label="Judge", status="complete", confidence=0.91),
        ],
        decision_tree=DecisionNode(
            label="Final verdict",
            value="PASS",
            children=[
                DecisionNode(label="Execution", value="Reproduced"),
                DecisionNode(label="Security", value="Low risk"),
                DecisionNode(label="Research", value="Publication ready"),
            ],
        ),
        recommendations=[
            Recommendation(
                title="Pin production dependencies",
                reason="Improve long-term environment stability.",
                priority="medium",
                source="Environment",
            ),
            Recommendation(
                title="Persist evaluation history",
                reason="Enable organization-level trend analysis.",
                priority="low",
                source="Platform",
            ),
        ],
        knowledge_graph={
            "nodes": [
                {
                    "id": "repository:demo",
                    "label": "ReproProof demo",
                    "kind": "repository",
                },
                {"id": "agent:judge", "label": "Judge Agent", "kind": "agent"},
            ],
            "edges": [
                {
                    "source": "agent:judge",
                    "target": "repository:demo",
                    "relation": "evaluates",
                }
            ],
        },
    )


def demo_report() -> dict[str, Any]:
    overview = demo_overview()
    return {
        "report_id": DEMO_REPOSITORY_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overview": overview.model_dump(),
        "summary": "A credential-free demonstration of repository analysis, multi-agent evaluation, security review, research readiness, and explainable scoring.",
    }
