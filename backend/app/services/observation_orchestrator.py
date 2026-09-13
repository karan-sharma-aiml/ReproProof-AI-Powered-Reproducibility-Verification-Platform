"""Coordinate repository and project observation services."""

from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger
from app.models.observation_report import ObservationReport
from app.models.project_detection import ProjectDetection
from app.models.repository import RepositoryMetadata
from app.services.project_detector import ProjectDetector
from app.services.repository_inspector import RepositoryInspector

logger = get_logger("observation_orchestrator")


class ObservationOrchestrator:
    """Build one observation report without executing uploaded repository code."""

    HEALTH_PENALTIES = {
        "missing_readme": 10,
        "missing_requirements": 15,
        "missing_entry_point": 20,
        "empty_repository": 40,
        "missing_source_folder": 15,
    }
    ENTRY_FILE_NAMES = frozenset(
        {"main.py", "app.py", "manage.py", "cli.py", "__main__.py", "run.py"}
    )

    def __init__(
        self,
        repository_inspector: RepositoryInspector | None = None,
        project_detector: ProjectDetector | None = None,
    ) -> None:
        """Create an orchestrator with injectable observation dependencies."""
        self._repository_inspector = repository_inspector or RepositoryInspector()
        self._project_detector = project_detector or ProjectDetector()

    def observe(self, repo_path: Path) -> ObservationReport:
        """Inspect and classify a repository, then calculate readiness signals."""
        repository_path = Path(repo_path)
        logger.info("Starting observation for repository: %s", repository_path)

        repository = self._repository_inspector.inspect_repository(repository_path)
        project = self._project_detector.detect_project(repository_path)
        has_entry_point = (
            self._has_entry_point(repository_path)
            if project.is_python_project
            else True
        )
        warnings = self._build_warnings(repository, project, has_entry_point)
        recommendations = self._build_recommendations(
            repository, project, has_entry_point, warnings
        )
        health_score = self._calculate_health_score(repository, has_entry_point)
        execution_ready = self._is_execution_ready(
            repository, project, has_entry_point, warnings
        )

        report = ObservationReport(
            repository=repository,
            project=project,
            health_score=health_score,
            execution_ready=execution_ready,
            warnings=warnings,
            recommendations=recommendations,
        )
        logger.info(
            "Observation complete for %s: health=%d ready=%s warnings=%d",
            repository_path,
            report.health_score,
            report.execution_ready,
            len(report.warnings),
        )
        return report

    def _calculate_health_score(
        self, repository: RepositoryMetadata, has_entry_point: bool
    ) -> int:
        """Apply the documented health penalties to a perfect starting score."""
        score = 100
        important_files = set(repository.important_files)
        important_names = {Path(path).name for path in important_files}

        if "README.md" not in important_names:
            score -= self.HEALTH_PENALTIES["missing_readme"]
        if "requirements.txt" not in important_names:
            score -= self.HEALTH_PENALTIES["missing_requirements"]
        if not has_entry_point:
            score -= self.HEALTH_PENALTIES["missing_entry_point"]
        if repository.total_files == 0:
            score -= self.HEALTH_PENALTIES["empty_repository"]
        if not repository.source_directories:
            score -= self.HEALTH_PENALTIES["missing_source_folder"]

        return max(0, score)

    def _build_warnings(
        self,
        repository: RepositoryMetadata,
        project: ProjectDetection,
        has_entry_point: bool,
    ) -> list[str]:
        """Generate stable, human-readable warnings from observation facts."""
        important_names = {Path(path).name for path in repository.important_files}
        warnings: list[str] = []
        if "README.md" not in important_names:
            warnings.append("README.md is missing")
        if project.is_python_project and not self._has_dependency_manifest(
            important_names
        ):
            warnings.append("requirements.txt is missing")
        if project.is_python_project and not has_entry_point:
            warnings.append("No recognizable Python entry point was found")
        if repository.total_files == 0:
            warnings.append("Repository is empty")
        if not repository.source_directories:
            warnings.append("No recognized source folder was found")
        if project.project_type == "Unknown":
            warnings.append("Project type could not be determined")
        return warnings

    def _build_recommendations(
        self,
        repository: RepositoryMetadata,
        project: ProjectDetection,
        has_entry_point: bool,
        warnings: list[str],
    ) -> list[str]:
        """Generate actionable recommendations without making repository changes."""
        important_names = {Path(path).name for path in repository.important_files}
        recommendations: list[str] = []
        if "README.md" not in important_names:
            recommendations.append("Add a README.md describing setup and execution")
        if project.is_python_project and not self._has_dependency_manifest(
            important_names
        ):
            recommendations.append("Add a pinned requirements.txt dependency manifest")
        if project.is_python_project and not has_entry_point:
            recommendations.append("Add a clear Python entry point such as main.py")
        if not repository.source_directories and repository.total_files:
            recommendations.append("Organize application code in a source folder")
        if project.project_type == "Unknown":
            recommendations.append(
                "Document the project type and expected execution flow"
            )
        if not recommendations and not warnings:
            recommendations.append(
                "Repository structure is ready for deeper verification"
            )
        return recommendations

    def _is_execution_ready(
        self,
        repository: RepositoryMetadata,
        project: ProjectDetection,
        has_entry_point: bool,
        warnings: list[str],
    ) -> bool:
        """Require a valid Python project, required files, and no critical issues."""
        important_names = {Path(path).name for path in repository.important_files}
        required_files_exist = (
            "README.md" in important_names
            and self._has_dependency_manifest(important_names)
        )
        project_detected = project.project_type not in {"Unknown", ""}
        if not project.is_python_project:
            return bool(repository.total_files > 0 and project_detected)
        critical_warnings = {
            "Repository is empty",
            "No recognizable Python entry point was found",
            "Project type could not be determined",
        }
        return bool(
            repository.total_files > 0
            and project_detected
            and required_files_exist
            and has_entry_point
            and not critical_warnings.intersection(warnings)
        )

    @staticmethod
    def _has_dependency_manifest(important_names: set[str]) -> bool:
        return bool(
            important_names.intersection(
                {"requirements.txt", "pyproject.toml", "setup.py", "environment.yml"}
            )
        )

    def _has_entry_point(self, repository_path: Path) -> bool:
        """Find common entry files by name without reading or executing them."""
        try:
            return any(
                entry.is_file()
                and entry.name in self.ENTRY_FILE_NAMES
                and (
                    len(entry.relative_to(repository_path).parts) == 1
                    or any(
                        part.lower() in {"app", "src", "backend", "server", "api"}
                        for part in entry.relative_to(repository_path).parts[:-1]
                    )
                )
                and not any(
                    part.lower()
                    in {
                        "tests",
                        "test",
                        "docs",
                        "docs_src",
                        "examples",
                        "backups",
                        "uploads",
                        "reports",
                        ".venv",
                        "node_modules",
                    }
                    for part in entry.relative_to(repository_path).parts
                )
                for entry in repository_path.rglob("*")
            )
        except OSError as exc:
            logger.warning(
                "Could not inspect entry points in %s: %s", repository_path, exc
            )
            return False
