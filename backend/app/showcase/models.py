from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
    id: str
    label: str
    status: Literal["complete", "active", "pending"]
    confidence: float = Field(ge=0, le=1)


class DecisionNode(BaseModel):
    label: str
    value: str
    children: list["DecisionNode"] = Field(default_factory=list)


class Recommendation(BaseModel):
    title: str
    reason: str
    priority: Literal["high", "medium", "low"]
    source: str


class ArchitectureArtifact(BaseModel):
    repository_id: str
    format: str = "mermaid"
    content: str


class EnterpriseOverview(BaseModel):
    repository_id: str
    verdict: str
    overall_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    scores: dict[str, float]
    workflow: list[WorkflowNode]
    decision_tree: DecisionNode
    recommendations: list[Recommendation]
    knowledge_graph: dict[str, Any]


class ReadmeArtifact(BaseModel):
    repository_id: str
    content: str
    generated_from: list[str]
