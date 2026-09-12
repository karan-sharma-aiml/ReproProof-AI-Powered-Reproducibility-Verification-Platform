"""Filesystem-only inspection of an extracted research repository."""

from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger
from app.models.repository import RepositoryMetadata

logger = get_logger("repository_inspector")


class RepositoryInspector:
    """Collect safe, structural metadata without executing repository code."""

    IMPORTANT_FILES = frozenset(
        {
            "README.md",
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "environment.yml",
            "Dockerfile",
            "Makefile",
            "LICENSE",
            "LICENSE.txt",
            "COPYING",
            "main.py",
            "app.py",
            "train.py",
            "run.py",
            "server.py",
            "cli.py",
            "runtime.txt",
            ".python-version",
            "setup.cfg",
            "docker-compose.yml",
            "compose.yaml",
        }
    )
    SOURCE_DIRECTORIES = frozenset(
        {
            "src",
            "app",
            "backend",
            "frontend",
            "server",
            "client",
            "api",
            "core",
            "models",
            "services",
            "tests",
            "scripts",
            "configs",
            "notebooks",
            "docs",
            "examples",
        }
    )
    DATASET_EXTENSIONS = frozenset({".csv", ".json", ".xlsx", ".parquet"})
    ENTRY_FILES = frozenset(
        {"main.py", "app.py", "train.py", "run.py", "manage.py", "server.py", "cli.py"}
    )

    def inspect_repository(
        self, repo_path: Path, repository_id: str = ""
    ) -> RepositoryMetadata:
        """Inspect ``repo_path`` and return metadata suitable for JSON output.

        The walk only reads directory entries and file names. It never opens,
        imports, or executes repository content. Unreadable entries are skipped
        and logged so a single permission issue does not discard the report.

        Raises:
            ValueError: If ``repo_path`` does not exist or is not a directory.
        """
        repository_path = Path(repo_path)
        if not repository_path.exists():
            logger.error("Repository path does not exist: %s", repository_path)
            raise ValueError(f"Repository path does not exist: {repository_path}")
        if not repository_path.is_dir():
            logger.error("Repository path is not a directory: %s", repository_path)
            raise ValueError(f"Repository path is not a directory: {repository_path}")

        metadata = {
            "repository_name": repository_path.name,
            "total_files": 0,
            "total_folders": 0,
            "python_files": 0,
            "notebooks": 0,
            "important_files": [],
            "source_directories": [],
            "detected_languages": [],
            "repository_id": repository_id,
            "repository_path": str(repository_path.resolve()),
            "tree": [],
            "datasets": [],
            "detected_frameworks": [],
            "health_score": 100,
            "warnings": [],
            "package_managers": [],
            "ci_cd": [],
            "environment_files": [],
            "licenses": [],
            "test_frameworks": [],
            "dependency_packages": [],
            "docker_configured": False,
            "readme_quality": 0,
        }

        try:
            entries = repository_path.rglob("*")
            for entry in entries:
                try:
                    relative_path = entry.relative_to(repository_path).as_posix()
                    metadata["tree"].append(relative_path)
                    if entry.is_dir():
                        metadata["total_folders"] += 1
                        if entry.name in self.SOURCE_DIRECTORIES:
                            metadata["source_directories"].append(relative_path)
                    elif entry.is_file():
                        metadata["total_files"] += 1
                        if entry.name in self.IMPORTANT_FILES:
                            metadata["important_files"].append(relative_path)
                        if entry.suffix.lower() in self.DATASET_EXTENSIONS:
                            metadata["datasets"].append(relative_path)
                        if entry.suffix.lower() == ".py":
                            metadata["python_files"] += 1
                        elif entry.suffix.lower() == ".ipynb":
                            metadata["notebooks"] += 1
                except OSError as exc:
                    logger.warning("Skipping inaccessible entry %s: %s", entry, exc)
        except OSError as exc:
            logger.error("Could not walk repository %s: %s", repository_path, exc)
            raise ValueError(
                f"Could not inspect repository: {repository_path}"
            ) from exc

        metadata["important_files"].sort()
        metadata["source_directories"].sort()
        metadata["tree"].sort()
        metadata["datasets"].sort()
        if metadata["python_files"]:
            metadata["detected_languages"].append("Python")
        if metadata["notebooks"]:
            metadata["detected_languages"].append("Jupyter Notebook")

        important_names = {Path(path).name for path in metadata["important_files"]}
        all_names = {Path(path).name.lower() for path in metadata["tree"]}
        metadata["package_managers"] = [
            name
            for marker, name in (
                ("requirements.txt", "pip"),
                ("pyproject.toml", "poetry/uv"),
                ("setup.py", "setuptools"),
                ("package.json", "npm"),
                ("package-lock.json", "npm lockfile"),
                ("yarn.lock", "yarn"),
                ("pnpm-lock.yaml", "pnpm"),
                ("environment.yml", "conda"),
            )
            if marker.lower() in all_names
        ]
        metadata["ci_cd"] = [
            label
            for marker, label in (
                (".github/workflows", "GitHub Actions"),
                (".gitlab-ci.yml", "GitLab CI"),
                ("jenkinsfile", "Jenkins"),
                ("azure-pipelines.yml", "Azure Pipelines"),
            )
            if marker.lower() in {path.lower() for path in metadata["tree"]}
        ]
        metadata["environment_files"] = sorted(
            path
            for path in metadata["tree"]
            if Path(path).name.lower().startswith(".env")
        )
        metadata["licenses"] = sorted(
            path
            for path in metadata["important_files"]
            if Path(path).name.lower() in {"license", "license.txt", "copying"}
        )
        metadata["docker_configured"] = any(
            Path(path).name.lower()
            in {"dockerfile", "docker-compose.yml", "compose.yaml"}
            for path in metadata["tree"]
        )
        test_names = " ".join(metadata["tree"]).lower()
        metadata["test_frameworks"] = [
            framework
            for marker, framework in (
                ("pytest", "pytest"),
                ("unittest", "unittest"),
                ("jest", "Jest"),
                ("vitest", "Vitest"),
                ("playwright", "Playwright"),
                ("cypress", "Cypress"),
            )
            if marker in test_names
        ]
        dependency_files = [
            path
            for path in metadata["important_files"]
            if Path(path).name.lower() in {"requirements.txt", "pyproject.toml"}
        ]
        for dependency_file in dependency_files:
            try:
                text = (repository_path / dependency_file).read_text(
                    encoding="utf-8", errors="ignore"
                )
                metadata["dependency_packages"].extend(
                    line.split("==", 1)[0].split(">=", 1)[0].strip()
                    for line in text.splitlines()
                    if line.strip() and not line.lstrip().startswith(("#", "[", "-"))
                )
            except OSError:
                continue
        metadata["dependency_packages"] = sorted(set(metadata["dependency_packages"]))[
            :100
        ]
        readme_path = next(
            (
                repository_path / path
                for path in metadata["important_files"]
                if Path(path).name.lower() == "readme.md"
            ),
            None,
        )
        if readme_path and readme_path.exists():
            readme_text = readme_path.read_text(encoding="utf-8", errors="ignore")
            metadata["readme_quality"] = min(
                100,
                35
                + sum(
                    bool(marker in readme_text.lower())
                    for marker in ("install", "usage", "example", "result", "license")
                )
                * 13,
            )
        if "README.md" not in important_names:
            metadata["health_score"] -= 10
            metadata["warnings"].append("README.md is missing")
        if "requirements.txt" not in important_names:
            metadata["health_score"] -= 15
            metadata["warnings"].append("requirements.txt is missing")
        if metadata["total_files"] == 0:
            metadata["health_score"] -= 40
            metadata["warnings"].append("Repository is empty")
        if not metadata["source_directories"]:
            metadata["health_score"] -= 15
            metadata["warnings"].append("No recognized source folder was found")
        if not any(Path(path).name in self.ENTRY_FILES for path in metadata["tree"]):
            metadata["health_score"] -= 20
            metadata["warnings"].append("No recognizable Python entry point was found")
        metadata["health_score"] = max(0, metadata["health_score"])

        result = RepositoryMetadata.model_validate(metadata)
        logger.info(
            "Inspected repository %s: files=%d folders=%d python=%d notebooks=%d",
            repository_path,
            result.total_files,
            result.total_folders,
            result.python_files,
            result.notebooks,
        )
        return result
