"""Extract uploaded archives and build phase-one repository metadata."""

from __future__ import annotations

import stat
import zipfile
from pathlib import Path, PurePosixPath

from app.core.logging import get_logger
from app.models.project_detection import ProjectDetection
from app.models.repository import RepositoryMetadata
from app.services.project_detector import ProjectDetector
from app.services.repository_inspector import RepositoryInspector

logger = get_logger("repository_analysis_service")


class RepositoryAnalysisService:
    """Own archive extraction and composition of existing analysis services."""

    def __init__(
        self,
        inspector: RepositoryInspector | None = None,
        detector: ProjectDetector | None = None,
    ) -> None:
        self._inspector = inspector or RepositoryInspector()
        self._detector = detector or ProjectDetector()

    def extract_repository(self, archive_path: Path, repository_id: str) -> Path:
        """Extract an upload into ``uploads/{id}/repository`` safely."""
        archive = Path(archive_path).resolve()
        target = archive.parent / repository_id / "repository"
        target.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(archive) as archive_file:
                for member in archive_file.infolist():
                    self._validate_member(member, target)
                archive_file.extractall(target)
        except (OSError, zipfile.BadZipFile, ValueError) as exc:
            logger.exception("Failed to extract repository %s", archive)
            raise ValueError(f"Could not extract uploaded repository: {exc}") from exc
        logger.info("Extracted repository %s to %s", repository_id, target)
        return target

    def analyze_repository(
        self, repository_path: Path, repository_id: str = ""
    ) -> RepositoryMetadata:
        """Build enriched metadata using RepositoryInspector and ProjectDetector."""
        metadata = self._inspector.inspect_repository(repository_path, repository_id)
        project = self._detector.detect_project(repository_path)
        frameworks = self._detect_frameworks(repository_path)
        display_framework = self._display_framework(project.framework)
        if display_framework and display_framework not in frameworks:
            frameworks.insert(0, display_framework)
        if metadata.notebooks and "Jupyter Notebook" not in frameworks:
            frameworks.append("Jupyter Notebook")
        if (
            metadata.python_files
            and (
                "tests" in metadata.source_directories
                or "docs" in metadata.source_directories
            )
            and "Research Project" not in frameworks
        ):
            frameworks.append("Research Project")
        result = metadata.model_copy(
            update={
                "detected_frameworks": frameworks,
                "repository_path": (
                    f"{repository_id}/repository"
                    if repository_id
                    else metadata.repository_path
                ),
            }
        )
        logger.info(
            "Analyzed repository %s: files=%d datasets=%d health=%d",
            repository_path,
            result.total_files,
            len(result.datasets),
            result.health_score,
        )
        return result

    def extract_and_analyze(
        self, archive_path: Path, repository_id: str
    ) -> RepositoryMetadata:
        repository_path = self.extract_repository(archive_path, repository_id)
        return self.analyze_repository(repository_path, repository_id)

    @staticmethod
    def _validate_member(member: zipfile.ZipInfo, target: Path) -> None:
        filename = member.filename.replace("\\", "/")
        relative = PurePosixPath(filename)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe archive member: {member.filename}")
        mode = (member.external_attr >> 16) & 0xFFFF
        if stat.S_ISLNK(mode):
            raise ValueError(
                f"Symlink archive member is not allowed: {member.filename}"
            )
        destination = (target / Path(*relative.parts)).resolve()
        destination.relative_to(target.resolve())

    def _detect_frameworks(self, repository_path: Path) -> list[str]:
        text = "\n".join(
            self._read_text(path)
            for path in repository_path.rglob("*")
            if path.is_file()
            and (
                path.name.lower() in self._detector.CONFIG_FILES
                or path.suffix.lower() == ".py"
            )
        ).lower()
        aliases = {
            "FastAPI": ("fastapi",),
            "Flask": ("flask",),
            "Django": ("django",),
            "Streamlit": ("streamlit",),
            "Gradio": ("gradio",),
            "PyTorch": ("torch", "pytorch"),
            "TensorFlow": ("tensorflow",),
            "Scikit Learn": ("scikit-learn", "sklearn"),
            "CLI": ("typer", "click", "argparse"),
        }
        return [
            name
            for name, names in aliases.items()
            if any(alias in text for alias in names)
        ]

    @staticmethod
    def _display_framework(framework: str) -> str:
        names = {
            "fastapi": "FastAPI",
            "flask": "Flask",
            "django": "Django",
            "streamlit": "Streamlit",
            "gradio": "Gradio",
            "pytorch": "PyTorch",
            "tensorflow": "TensorFlow",
            "scikit-learn": "Scikit Learn",
            "jupyter notebook": "Jupyter Notebook",
        }
        return names.get(framework.lower(), framework)

    @staticmethod
    def _read_text(path: Path) -> str:
        try:
            return path.read_bytes()[:1_048_576].decode("utf-8", errors="ignore")
        except OSError:
            return ""
