"""Generate deterministic, non-executing plans from observation reports."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.core.logging import get_logger
from app.models.execution_plan import ExecutionPlan
from app.models.observation_report import ObservationReport

logger = get_logger("execution_planner")


class EntryPointResolver(Protocol):
    """Resolve a conventional entry point from report-only observations."""

    def __call__(self, report: ObservationReport, execution_type: str) -> str:
        """Return an entry point path or notebook name."""


class ExecutionPlanner:
    """Create reviewable shell-command plans without running repository code."""

    PYTHON_VERSION = "3.11"
    DEPENDENCY_FILE_ORDER = (
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "environment.yml",
    )

    def __init__(
        self,
        entry_point_resolver: EntryPointResolver | None = None,
        python_version: str = PYTHON_VERSION,
    ) -> None:
        """Create a planner with injectable entry-point policy and version policy."""
        self._entry_point_resolver = (
            entry_point_resolver or self._default_entry_point_resolver
        )
        self._python_version = python_version

    def create_plan(self, report: ObservationReport) -> ExecutionPlan:
        """Build an execution plan from observations only."""
        execution_type = self._execution_type(report)
        dependency_file = self._dependency_file(report)
        entry_point = self._entry_point_resolver(report, execution_type)
        commands = self._commands(report, execution_type, dependency_file, entry_point)
        risks = self._risks(report, dependency_file, entry_point)
        assumptions = self._assumptions(
            report, dependency_file, entry_point, execution_type
        )

        plan = ExecutionPlan(
            python_version=self._python_version,
            environment_strategy=self._environment_strategy(execution_type),
            dependency_file=dependency_file,
            entry_point=entry_point,
            execution_type=execution_type,
            commands=commands,
            risks=risks,
            assumptions=assumptions,
        )
        logger.info(
            "Created execution plan: type=%s entry=%s dependency=%s",
            plan.execution_type,
            plan.entry_point,
            plan.dependency_file or "none",
        )
        return plan

    def _execution_type(self, report: ObservationReport) -> str:
        if not report.project.is_python_project:
            return report.project.project_type
        framework = report.project.framework.lower()
        if report.project.project_type == "Monorepo":
            framework = report.project.backend.lower().split(" ", 1)[0] or framework
        project_type = report.project.project_type.lower()
        if framework == "fastapi":
            return "FastAPI"
        if framework == "flask":
            return "Flask"
        if framework == "django":
            return "Django"
        if framework == "jupyter notebook" or "notebook" in project_type:
            return "Notebook"
        if not self._has_entry_point_file(report):
            return "Python Package"
        if project_type == "cli application" or framework in {"typer", "click", "cli"}:
            return "CLI"
        if project_type in {"research project", "machine learning project"}:
            return "Research Pipeline"
        if not report.repository.source_directories and not self._has_entry_point_file(
            report
        ):
            return "Python Package"
        return "Python Script"

    def _dependency_file(self, report: ObservationReport) -> str:
        target = report.project.execution_target.rstrip("/")
        paths = [
            path
            for path in report.repository.important_files
            if not any(
                part in {"uploads", "backups", "reports", ".next", "node_modules"}
                for part in Path(path).parts
            )
        ]
        if target:
            targeted = [
                path for path in paths if Path(path).as_posix().startswith(f"{target}/")
            ]
            paths = targeted or paths
        available = {Path(path).name.lower(): path for path in paths}
        for filename in self.DEPENDENCY_FILE_ORDER:
            if filename in available:
                return available[filename]
        return ""

    def _environment_strategy(self, execution_type: str) -> str:
        if execution_type in {
            "Next.js",
            "React/Vite Project",
            "React Project",
            "Node.js Project",
        }:
            return "Execution skipped (non-Python project)"
        if execution_type == "Notebook":
            return "Python virtual environment with a Jupyter kernel"
        return "Python virtual environment (.venv)"

    def _commands(
        self,
        report: ObservationReport,
        execution_type: str,
        dependency_file: str,
        entry_point: str,
    ) -> list[str]:
        if (
            not report.project.is_python_project
            or not entry_point
            or entry_point == "."
        ):
            return []
        if execution_type in {
            "Next.js",
            "React/Vite Project",
            "React Project",
            "Node.js Project",
            "Python Package",
        }:
            return []
        commands = ["python -m venv .venv"]
        dependency_name = Path(dependency_file).name
        if dependency_name == "requirements.txt":
            commands.append("pip install -r requirements.txt")
        elif dependency_name in {"pyproject.toml", "setup.py"}:
            commands.append("pip install -e .")
        elif dependency_name == "environment.yml":
            commands.append("conda env update -f environment.yml")

        module = self._module_name(entry_point)
        if execution_type == "FastAPI":
            commands.append(f"uvicorn {module}:app")
        elif execution_type == "Flask":
            commands.append(f"flask --app {module} run")
        elif execution_type == "Django":
            commands.append(f"python {entry_point} runserver")
        elif execution_type == "Notebook":
            commands.append("jupyter notebook")
        else:
            commands.append(f"python {entry_point}")

        return commands

    @staticmethod
    def _has_entry_point_file(report: ObservationReport) -> bool:
        return any(
            Path(path).name.lower()
            in {"main.py", "app.py", "manage.py", "run.py", "server.py", "cli.py"}
            and (
                len(Path(path).parts) == 1
                or any(
                    part.lower() in {"app", "src", "backend", "server", "api"}
                    for part in Path(path).parts[:-1]
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
                }
                for part in Path(path).parts[:-1]
            )
            for path in report.repository.important_files
        )

    def _risks(
        self,
        report: ObservationReport,
        dependency_file: str,
        entry_point: str,
    ) -> list[str]:
        risks = list(report.warnings)
        if not dependency_file:
            risks.append(
                "No dependency file was detected; the environment may be incomplete"
            )
        if not entry_point:
            risks.append("No deterministic entry point could be inferred")
        if not report.execution_ready:
            risks.append("Observation report is not execution-ready")
        return self._unique(risks)

    def _assumptions(
        self,
        report: ObservationReport,
        dependency_file: str,
        entry_point: str,
        execution_type: str,
    ) -> list[str]:
        assumptions = [
            f"Python {self._python_version} is available on the host",
            "Commands are proposals only and have not been executed",
            "Uploaded source code will not be imported or executed by the planner",
        ]
        if not report.project.is_python_project:
            return ["Execution skipped (non-Python project)"]
        if execution_type == "Python Package":
            return [
                "Repository is a Python package without a runnable application entry point"
            ]
        if entry_point:
            assumptions.append(
                f"{entry_point} is the conventional entry point for {execution_type}"
            )
        if dependency_file:
            assumptions.append(
                f"{dependency_file} contains the project's install instructions"
            )
        if report.project.project_type == "Unknown":
            assumptions.append("Project type could not be confirmed from observations")
        return assumptions

    def _default_entry_point_resolver(
        self, report: ObservationReport, execution_type: str
    ) -> str:
        if not report.project.is_python_project:
            return ""
        if execution_type == "Python Package":
            return ""
        source_directories = {
            Path(path).as_posix() for path in report.repository.source_directories
        }
        target = report.project.execution_target.rstrip("/")
        if target:
            target_root = Path(target)
            target_sources = {
                Path(path).relative_to(target_root).as_posix()
                for path in source_directories
                if Path(path).as_posix().startswith(f"{target_root.as_posix()}/")
            }
            source_directories = target_sources or source_directories
        if execution_type == "FastAPI" and "app" in source_directories:
            return "app/main.py"
        if execution_type == "FastAPI" and "app.py" in {
            Path(path).name.lower() for path in report.repository.important_files
        }:
            return "app.py"
        if execution_type == "Django":
            return "manage.py"
        if execution_type == "Flask":
            return "app.py"
        if execution_type == "Notebook":
            return "notebook"
        if execution_type == "Research Pipeline":
            if report.project.framework.lower() in {
                "pytorch",
                "tensorflow",
                "scikit-learn",
            }:
                return "train.py"
            return "run.py"
        return "main.py"

    @staticmethod
    def _module_name(entry_point: str) -> str:
        if not entry_point or entry_point == ".":
            return ""
        return Path(entry_point).with_suffix("").as_posix().replace("/", ".")

    @staticmethod
    def _unique(items: list[str]) -> list[str]:
        return list(dict.fromkeys(item for item in items if item))
