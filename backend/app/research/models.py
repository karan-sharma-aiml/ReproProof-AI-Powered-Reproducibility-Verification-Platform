from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RiskItem(BaseModel):
    path: str
    category: str
    severity: str = "medium"
    score: float = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)


class RiskHeatmap(BaseModel):
    repository_id: str
    overall_risk: float = Field(ge=0, le=100)
    items: list[RiskItem] = Field(default_factory=list)
    categories: dict[str, float] = Field(default_factory=dict)


class DependencyNode(BaseModel):
    id: str
    label: str
    kind: str
    hotspot_score: float = Field(ge=0, le=100, default=0)


class DependencyEdge(BaseModel):
    source: str
    target: str
    kind: str = "imports"


class DependencyGraph(BaseModel):
    repository_id: str
    nodes: list[DependencyNode] = Field(default_factory=list)
    edges: list[DependencyEdge] = Field(default_factory=list)
    circular_dependencies: list[list[str]] = Field(default_factory=list)
    architecture_violations: list[str] = Field(default_factory=list)


class ConfidenceAssessment(BaseModel):
    decision: str
    confidence: float = Field(ge=0, le=1)
    uncertainty: float = Field(ge=0, le=1)
    reasoning_quality: float = Field(ge=0, le=1)
    evidence_quality: float = Field(ge=0, le=1)
    risk_factor: float = Field(ge=0, le=1)
    explanation: str
    calibrated: bool = False


class HealthScore(BaseModel):
    repository_id: str
    overall: float = Field(ge=0, le=100)
    subscores: dict[str, float] = Field(default_factory=dict)
    suggestions: list[str] = Field(default_factory=list)
    historical_key: str


class TimelineEvent(BaseModel):
    event_type: str
    timestamp: datetime
    source: str
    details: dict[str, Any] = Field(default_factory=dict)


class Timeline(BaseModel):
    repository_id: str
    events: list[TimelineEvent] = Field(default_factory=list)


class DatasetQualityReport(BaseModel):
    name: str
    format: str
    rows: int = 0
    columns: int = 0
    missing_values: dict[str, int] = Field(default_factory=dict)
    duplicate_rows: int = 0
    outlier_columns: list[str] = Field(default_factory=list)
    quality_score: float = Field(ge=0, le=100)
    warnings: list[str] = Field(default_factory=list)


class EnvironmentSpec(BaseModel):
    languages: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    compatibility_notes: list[str] = Field(default_factory=list)


class DockerBuildRequest(BaseModel):
    target: str = Field(pattern="^(backend|frontend|combined)$")


class DockerBuildResult(BaseModel):
    target: str
    dockerfile: str
    security_controls: list[str] = Field(default_factory=list)


class ExecutionMetadata(BaseModel):
    stdout: str = ""
    stderr: str = ""
    runtime_seconds: float = 0
    memory_bytes: int | None = None
    cpu_seconds: float | None = None
    timeout_seconds: float | None = None
    exit_code: int | None = None
    resource_usage: dict[str, Any] = Field(default_factory=dict)
    sandbox_logs: list[str] = Field(default_factory=list)


class ScoreReport(BaseModel):
    name: str
    overall: float = Field(ge=0, le=100)
    subscores: dict[str, float] = Field(default_factory=dict)
    improvement_plan: list[str] = Field(default_factory=list)


class ExplainabilityReport(BaseModel):
    why: str
    how: str
    evidence: list[str] = Field(default_factory=list)
    confidence: ConfidenceAssessment
    alternatives: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class DocumentSection(BaseModel):
    heading: str
    text: str
    level: int = Field(ge=1, le=6, default=1)


class DocumentObject(BaseModel):
    name: str
    document_type: str
    pages: int | None = None
    text: str = ""
    sections: list[DocumentSection] = Field(default_factory=list)
    tables: list[list[list[str]]] = Field(default_factory=list)
    figures: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class ResearchAssistantResult(BaseModel):
    question: str
    answer: str
    provider: str
    evidence: list[str] = Field(default_factory=list)


class BenchmarkReport(BaseModel):
    repository_id: str
    measurements: dict[str, float] = Field(default_factory=dict)
    history_key: str


class DatasetValidationRequest(BaseModel):
    path: str


class Citation(BaseModel):
    key: str
    raw_text: str
    cited_in_sections: list[str] = Field(default_factory=list)


class CitationGraph(BaseModel):
    document_name: str
    nodes: list[str] = Field(default_factory=list)
    edges: list[dict[str, str]] = Field(default_factory=list)
    unresolved_citations: list[str] = Field(default_factory=list)


class MethodologyFinding(BaseModel):
    section: str
    method: str
    evidence: str
    confidence: float = Field(ge=0, le=1)


class PaperAnalysis(BaseModel):
    document: DocumentObject
    citations: list[Citation] = Field(default_factory=list)
    citation_graph: CitationGraph
    methodology: list[MethodologyFinding] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    summary: str = ""


class ProviderAnalysis(BaseModel):
    capability: str
    result: dict[str, Any] = Field(default_factory=dict)
    provider: str
    evidence: list[str] = Field(default_factory=list)


class PaperAnalysisRequest(BaseModel):
    path: str


class ResearchQuestionRequest(BaseModel):
    question: str
    context: dict[str, Any] = Field(default_factory=dict)
