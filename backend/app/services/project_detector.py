"""Filesystem-only detection of Python project characteristics."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.core.logging import get_logger
from app.models.project_detection import ProjectDetection

logger = get_logger("project_detector")


@dataclass(frozen=True)
class _Signal:
    """A scored observation supporting one detected framework."""

    framework: str
    project_type: str
    weight: int
    reason: str


class ProjectDetector:
    """Determine a repository's likely Python project type without execution."""

    MAX_TEXT_BYTES = 1_048_576
    SOURCE_EXTENSIONS = frozenset({".py", ".pyi"})
    CONFIG_FILES = frozenset(
        {"requirements.txt", "pyproject.toml", "setup.py", "environment.yml"}
    )
    ENTRY_FILES = frozenset(
        {"main.py", "app.py", "manage.py", "cli.py", "__main__.py", "run.py"}
    )
    DEPENDENCY_ALIASES = {
        "fastapi": ("fastapi",),
        "flask": ("flask",),
        "django": ("django",),
        "streamlit": ("streamlit",),
        "gradio": ("gradio",),
        "typer": ("typer",),
        "click": ("click",),
        "pytorch": ("torch", "pytorch"),
        "tensorflow": ("tensorflow",),
        "scikit-learn": ("scikit-learn", "sklearn"),
        "jupyter": ("jupyter", "jupyterlab", "notebook", "ipykernel"),
    }
    PROJECT_TYPES = {
        "fastapi": "Web API",
        "flask": "Web Application",
        "django": "Web Application",
        "streamlit": "Data Application",
        "gradio": "Data Application",
        "typer": "CLI Application",
        "click": "CLI Application",
        "pytorch": "Machine Learning Project",
        "tensorflow": "Machine Learning Project",
        "scikit-learn": "Machine Learning Project",
        "jupyter": "Notebook Project",
    }

    def detect_project(self, repo_path: Path) -> ProjectDetection:
        """Analyze ``repo_path`` and return its most likely project type.

        Only file names and bounded text from known repository files are read.
        Python modules are parsed for import statements but are never imported
        or executed. Invalid repository paths fail clearly; inaccessible files
        are skipped with a warning.

        Raises:
            ValueError: If ``repo_path`` does not exist or is not a directory.
        """
        repository_path = Path(repo_path)
        if not repository_path.exists():
            logger.error("Project path does not exist: %s", repository_path)
            raise ValueError(f"Project path does not exist: {repository_path}")
        if not repository_path.is_dir():
            logger.error("Project path is not a directory: %s", repository_path)
            raise ValueError(f"Project path is not a directory: {repository_path}")

        signals: list[_Signal] = []
        dependency_text = ""
        readme_text = ""
        python_imports: set[str] = set()
        python_files = 0
        notebook_files = 0
        entry_files: list[str] = []
        has_tests = False
        has_docs = False

        try:
            entries = list(repository_path.rglob("*"))
        except OSError as exc:
            logger.error("Could not walk project %s: %s", repository_path, exc)
            raise ValueError(f"Could not inspect project: {repository_path}") from exc

        for entry in entries:
            try:
                if entry.is_dir():
                    has_tests |= entry.name.lower() == "tests"
                    has_docs |= entry.name.lower() == "docs"
                    continue
                if not entry.is_file():
                    continue

                filename = entry.name.lower()
                if entry.suffix.lower() == ".ipynb":
                    notebook_files += 1
                if entry.name in self.ENTRY_FILES:
                    entry_files.append(entry.relative_to(repository_path).as_posix())

                if filename == "readme.md":
                    readme_text += self._read_text(entry)
                if filename in self.CONFIG_FILES:
                    dependency_text += self._read_text(entry)
                if entry.suffix.lower() in self.SOURCE_EXTENSIONS:
                    python_files += 1
                    python_imports.update(self._extract_imports(self._read_text(entry)))
            except (OSError, ValueError) as exc:
                logger.warning("Skipping inaccessible project entry %s: %s", entry, exc)

        searchable_text = "\n".join((dependency_text, readme_text)).lower()
        for framework, aliases in self.DEPENDENCY_ALIASES.items():
            dependency_hits = [
                alias
                for alias in aliases
                if self._contains_package(dependency_text, alias)
            ]
            import_hits = [alias for alias in aliases if alias in python_imports]
            readme_hits = [
                alias for alias in aliases if self._contains_package(readme_text, alias)
            ]
            if dependency_hits:
                signals.append(
                    _Signal(
                        framework,
                        self.PROJECT_TYPES[framework],
                        70,
                        f"{dependency_hits[0]} is declared in a project dependency file",
                    )
                )
            if import_hits:
                signals.append(
                    _Signal(
                        framework,
                        self.PROJECT_TYPES[framework],
                        55,
                        f"Python imports include {import_hits[0]}",
                    )
                )
            if readme_hits and not dependency_hits:
                signals.append(
                    _Signal(
                        framework,
                        self.PROJECT_TYPES[framework],
                        25,
                        f"README references {readme_hits[0]}",
                    )
                )

        if notebook_files:
            signals.append(
                _Signal(
                    "Jupyter Notebook",
                    "Notebook Project",
                    min(65, 35 + notebook_files * 5),
                    f"Found {notebook_files} Jupyter notebook(s)",
                )
            )
        if entry_files and ("typer" in searchable_text or "click" in searchable_text):
            signals.append(
                _Signal(
                    "CLI",
                    "CLI Application",
                    20,
                    f"Found CLI entry file(s): {', '.join(sorted(entry_files))}",
                )
            )
        if python_files and (has_tests or has_docs) and not signals:
            signals.append(
                _Signal(
                    "",
                    "Research Project",
                    45,
                    "Found Python source files with research-oriented tests or documentation",
                )
            )
        if not signals and python_files:
            signals.append(
                _Signal(
                    "",
                    "Python Project",
                    35,
                    f"Found {python_files} Python source file(s)",
                )
            )

        if not signals:
            result = ProjectDetection(
                project_type="Unknown",
                framework="",
                confidence=0,
                reason="No recognizable Python project signals were found",
            )
        else:
            best = max(signals, key=lambda signal: (signal.weight, signal.framework))
            result = ProjectDetection(
                project_type=best.project_type,
                framework=best.framework,
                confidence=best.weight,
                reason=best.reason,
            )

        logger.info(
            "Detected project %s: type=%s framework=%s confidence=%d",
            repository_path,
            result.project_type,
            result.framework or "none",
            result.confidence,
        )
        return result

    def _read_text(self, path: Path) -> str:
        """Read a bounded amount of text while tolerating non-UTF-8 files."""
        try:
            return path.read_bytes()[: self.MAX_TEXT_BYTES].decode(
                "utf-8", errors="ignore"
            )
        except OSError as exc:
            logger.warning("Could not read project file %s: %s", path, exc)
            return ""

    @staticmethod
    def _extract_imports(source: str) -> set[str]:
        """Extract top-level module names from import statements."""
        imports: set[str] = set()
        for match in re.finditer(
            r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", source, re.MULTILINE
        ):
            imports.add(match.group(1).split(".", 1)[0].lower().replace("_", "-"))
        return imports

    @staticmethod
    def _contains_package(text: str, package: str) -> bool:
        """Match a package name without matching a longer package token."""
        normalized = package.lower().replace("_", "-")
        return bool(
            re.search(
                rf"(?<![a-z0-9_-]){re.escape(normalized)}(?![a-z0-9_-])",
                text.lower().replace("_", "-"),
            )
        )
