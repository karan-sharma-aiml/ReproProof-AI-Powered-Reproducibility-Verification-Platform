from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger

from .models import EnvironmentReport

logger = get_logger("execution.environment")


class EnvironmentDetector:
    """Detects environment metadata without installing or executing project code."""

    ignored = {".git", "node_modules", ".next", "__pycache__"}

    def detect(self, repository_path: Path) -> EnvironmentReport:
        root = repository_path.resolve()
        if not root.is_dir():
            raise ValueError(f"Repository path is not a directory: {root}")
        files = [
            path
            for path in root.rglob("*")
            if path.is_file() and not self.ignored.intersection(path.parts)
        ]
        names = {path.name.lower() for path in files}
        languages = []
        if any(path.suffix == ".py" for path in files):
            languages.append("Python")
        if any(path.suffix in {".js", ".ts", ".tsx"} for path in files):
            languages.append("Node")
        if any(path.suffix == ".java" for path in files):
            languages.append("Java")
        if any(path.suffix == ".rs" for path in files):
            languages.append("Rust")
        virtual_environments = [
            str(path.relative_to(root))
            for path in files
            if path.name in {"pyvenv.cfg", "Pipfile", "poetry.lock", "environment.yml"}
        ]
        package_managers = []
        for marker, manager in (
            ("requirements.txt", "pip"),
            ("pyproject.toml", "poetry/uv"),
            ("package-lock.json", "npm"),
            ("yarn.lock", "yarn"),
            ("Dockerfile", "docker"),
            ("environment.yml", "conda"),
        ):
            if marker.lower() in names:
                package_managers.append(manager)
        dependency_files = [
            str(path.relative_to(root))
            for path in files
            if path.name.lower()
            in {
                "requirements.txt",
                "pyproject.toml",
                "package.json",
                "package-lock.json",
                "yarn.lock",
                "environment.yml",
                "poetry.lock",
            }
        ]
        runtime_files = [
            str(path.relative_to(root))
            for path in files
            if path.name.lower()
            in {"runtime.txt", ".python-version", ".nvmrc", "dockerfile"}
        ]
        return EnvironmentReport(
            repository_path=str(root),
            languages=languages,
            virtual_environments=virtual_environments,
            package_managers=package_managers,
            dependency_files=dependency_files,
            runtime_files=runtime_files,
        )
