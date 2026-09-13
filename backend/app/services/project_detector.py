"""Filesystem-only detection of repository project characteristics."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.core.logging import get_logger
from app.models.project_detection import ProjectDetection
from app.services.confidence_engine import ConfidenceEngine

logger = get_logger("project_detector")


@dataclass(frozen=True)
class _Signal:
    """A scored observation supporting one detected framework."""

    framework: str
    project_type: str
    weight: int
    reason: str


class ProjectDetector:
    """Determine a repository's likely project type without execution."""

    MAX_TEXT_BYTES = 1_048_576
    SOURCE_EXTENSIONS = frozenset({".py", ".pyi"})
    CONFIG_FILES = frozenset(
        {
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "environment.yml",
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
        }
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
        filenames: set[str] = set()
        directory_names: set[str] = set()
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
                    directory_names.add(entry.name.lower())
                    has_tests |= entry.name.lower() == "tests"
                    has_docs |= entry.name.lower() == "docs"
                    continue
                if not entry.is_file():
                    continue

                filename = entry.name.lower()
                filenames.add(filename)
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

        node_signals = self._node_signals(filenames, directory_names, dependency_text)
        components = self._detect_components(repository_path)
        python_component = components["backend"]
        frontend_component = components["frontend"]
        if python_component and frontend_component:
            backend_framework = python_component["framework"] or "Python"
            result = ProjectDetection(
                project_type="Monorepo",
                framework=f"{backend_framework} + {frontend_component}",
                detection_confidence=ConfidenceEngine.detection_confidence(95),
                reason=(
                    f"Detected {frontend_component} frontend and {backend_framework} "
                    "Python backend in separate repository directories"
                ),
                is_python_project=True,
                frontend=frontend_component,
                backend=f"{backend_framework} (Python)",
                execution_target=python_component["path"],
                confidence_factors=[
                    f"Frontend detected at {frontend_component.lower()} project path",
                    f"Python backend detected at {python_component['path']}",
                    "Backend execution target selected instead of skipping",
                ],
            )
            logger.info(
                "Detected monorepo: frontend=%s backend=%s target=%s",
                frontend_component,
                backend_framework,
                python_component["path"],
            )
            return result
        if node_signals:
            signals = node_signals

        if not signals:
            result = ProjectDetection(
                project_type="Unknown",
                framework="",
                detection_confidence=ConfidenceEngine.detection_confidence(0),
                reason="No recognizable project signals were found",
                is_python_project=False,
            )
        else:
            best = max(signals, key=lambda signal: (signal.weight, signal.framework))
            result = ProjectDetection(
                project_type=best.project_type,
                framework=best.framework,
                detection_confidence=ConfidenceEngine.detection_confidence(best.weight),
                reason=best.reason,
                is_python_project=best.framework
                not in {"next.js", "react/vite", "react", "node.js"},
                execution_target=python_component["path"] if python_component else "",
            )

        logger.info(
            "Detected project %s: type=%s framework=%s detection_confidence=%d",
            repository_path,
            result.project_type,
            result.framework or "none",
            result.detection_confidence,
        )
        return result

    def _detect_components(
        self, repository_path: Path
    ) -> dict[str, dict[str, str] | str]:
        """Detect independent frontend and Python backend slices in a monorepo."""
        backend: dict[str, str] = {}
        frontend = ""
        candidates = [repository_path]
        try:
            candidates.extend(
                path
                for path in repository_path.rglob("*")
                if path.is_dir()
                and not any(
                    part.startswith(".") or part in {"node_modules", ".venv"}
                    for part in path.relative_to(repository_path).parts
                )
            )
        except OSError:
            return {"backend": backend, "frontend": frontend}

        for candidate in sorted(
            candidates, key=lambda path: (len(path.parts), str(path))
        ):
            try:
                direct_files = {
                    path.name.lower(): path
                    for path in candidate.iterdir()
                    if path.is_file()
                }
                python_files = [
                    path for path in candidate.rglob("*.py") if path.is_file()
                ]
                dependency_file = next(
                    (
                        direct_files[name]
                        for name in (
                            "requirements.txt",
                            "pyproject.toml",
                            "setup.py",
                            "environment.yml",
                        )
                        if name in direct_files
                    ),
                    None,
                )
                if not backend and python_files and dependency_file:
                    text = self._read_text(dependency_file)
                    imports = set()
                    for source in python_files:
                        imports.update(self._extract_imports(self._read_text(source)))
                    framework = next(
                        (
                            name
                            for name, aliases in self.DEPENDENCY_ALIASES.items()
                            if any(
                                self._contains_package(text, alias) or alias in imports
                                for alias in aliases
                            )
                        ),
                        "Python",
                    )
                    backend = {
                        "path": (
                            "."
                            if candidate == repository_path
                            else candidate.relative_to(repository_path).as_posix()
                        ),
                        "framework": (
                            framework if framework in self.PROJECT_TYPES else "Python"
                        ),
                    }
                package_json = direct_files.get("package.json")
                next_config = any(
                    name in direct_files
                    for name in ("next.config.js", "next.config.ts", "next.config.mjs")
                )
                package_text = self._read_text(package_json) if package_json else ""
                if not frontend and (
                    next_config or self._contains_package(package_text, "next")
                ):
                    frontend = "Next.js"
            except OSError:
                continue
        return {"backend": backend, "frontend": frontend}

    @staticmethod
    def _node_signals(
        filenames: set[str], directory_names: set[str], dependency_text: str
    ) -> list[_Signal]:
        """Classify JavaScript repositories from conventional markers."""
        has_package = "package.json" in filenames
        has_next_config = any(
            name in filenames for name in {"next.config.js", "next.config.ts"}
        )
        has_next_dependency = ProjectDetector._contains_package(dependency_text, "next")
        has_react_dependency = ProjectDetector._contains_package(
            dependency_text, "react"
        )
        has_vite = any(
            name in filenames for name in {"vite.config.js", "vite.config.ts"}
        )
        has_app_or_pages = bool({"app", "pages"}.intersection(directory_names))

        if (
            has_next_config
            or has_next_dependency
            or (has_package and has_app_or_pages and has_react_dependency)
        ):
            return [_Signal("next.js", "Next.js", 90, "Found Next.js signals")]
        if has_vite and has_react_dependency:
            return [
                _Signal(
                    "react/vite",
                    "React/Vite Project",
                    85,
                    "Found Vite configuration with React signals",
                )
            ]
        if has_react_dependency:
            return [_Signal("react", "React Project", 80, "Found React signals")]
        if has_package:
            return [_Signal("node.js", "Node.js Project", 65, "Found package.json")]
        return []

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
