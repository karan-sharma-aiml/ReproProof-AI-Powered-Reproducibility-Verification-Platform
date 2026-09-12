"""Repository health scoring derived from existing observations."""

from __future__ import annotations

from app.models.execution_result import ExecutionResult
from app.models.repository import RepositoryMetadata
from app.models.repository_ai_analysis import RepositoryAIAnalysis
from app.services.platform.models import HealthScoreResult


class HealthScoreService:
    """Calculate an explainable 0-100 repository health score."""

    def calculate(
        self,
        repository: RepositoryMetadata,
        analysis: RepositoryAIAnalysis,
        execution: ExecutionResult | None = None,
        patch_success: bool = False,
        retry_success: bool = False,
    ) -> HealthScoreResult:
        dimensions = {
            "dependencies": (
                100
                if repository.important_files
                and any(
                    item.endswith(
                        (
                            "requirements.txt",
                            "pyproject.toml",
                            "setup.py",
                            "environment.yml",
                        )
                    )
                    for item in repository.important_files
                )
                else 30
            ),
            "security": max(0, 100 - analysis.risk_score),
            "reproducibility": analysis.reproducibility_score,
            "documentation": (
                100
                if any(
                    item.lower().endswith("readme.md")
                    for item in repository.important_files
                )
                else 30
            ),
            "environment": (
                100
                if any(
                    Path(item).name in {".python-version", "runtime.txt", "Dockerfile"}
                    for item in repository.important_files
                )
                else 45
            ),
            "tests": (
                100
                if any(
                    Path(item).name == "tests" for item in repository.source_directories
                )
                else 40
            ),
            "execution": 100 if execution and execution.success else 20,
            "patch_success": 100 if patch_success else (50 if retry_success else 20),
        }
        weights = {
            "dependencies": 15,
            "security": 10,
            "reproducibility": 20,
            "documentation": 10,
            "environment": 10,
            "tests": 10,
            "execution": 20,
            "patch_success": 5,
        }
        score = round(
            sum(dimensions[name] * weight for name, weight in weights.items())
            / sum(weights.values())
        )
        recommendations: list[str] = []
        if dimensions["dependencies"] < 70:
            recommendations.append("Add a pinned dependency manifest.")
        if dimensions["documentation"] < 70:
            recommendations.append(
                "Document installation, usage, datasets, and expected results."
            )
        if dimensions["environment"] < 70:
            recommendations.append(
                "Declare the supported runtime or container environment."
            )
        if dimensions["tests"] < 70:
            recommendations.append("Add repeatable tests for the research workflow.")
        return HealthScoreResult(
            repository_id=repository.repository_id,
            score=score,
            recommendations=recommendations,
            dimensions=dimensions,
        )


from pathlib import Path
