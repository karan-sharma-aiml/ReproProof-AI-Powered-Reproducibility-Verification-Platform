"""Evidence-driven research and repository intelligence bounded context."""

from .models import (
    ConfidenceAssessment,
    DependencyGraph,
    HealthScore,
    RiskHeatmap,
    Timeline,
)
from .ports import LLMProvider, NoveltyProvider, OCRProvider, SandboxProvider
from .engines import (
    BenchmarkEngine,
    DockerBuilder,
    DocumentUnderstandingEngine,
    ExplainabilityEngine,
    ResearchAssistant,
    ScoreEngine,
    SecureExecutionEngine,
)
from .services import ResearchIntelligenceService
from .paper_engine import (
    CitationGraphEngine,
    PaperUnderstandingEngine,
    ProviderResearchEngine,
)

__all__ = [
    "ConfidenceAssessment",
    "DependencyGraph",
    "HealthScore",
    "RiskHeatmap",
    "Timeline",
    "LLMProvider",
    "NoveltyProvider",
    "OCRProvider",
    "SandboxProvider",
    "ResearchIntelligenceService",
    "CitationGraphEngine",
    "PaperUnderstandingEngine",
    "ProviderResearchEngine",
    "BenchmarkEngine",
    "DockerBuilder",
    "DocumentUnderstandingEngine",
    "ExplainabilityEngine",
    "ResearchAssistant",
    "ScoreEngine",
    "SecureExecutionEngine",
]
