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
        framework = report.project.framework.lower()
        project_type = report.project.project_type.lower()
        if framework == "fastapi":
            return "FastAPI"
        if framework == "flask":
            return "Flask"
        if framework == "django":
            return "Django"
        if framework == "jupyter notebook" or "notebook" in project_type:
            return "Notebook"
        if project_type == "cli application" or framework in {"typer", "click", "cli"}:
            return "CLI"
        if project_type in {"research project", "machine learning project"}:
            return "Research Pipeline"
        return "Python Script"

    def _dependency_file(self, report: ObservationReport) -> str:
        available = {
            Path(path).name.lower(): path for path in report.repository.important_files
        }
        for filename in self.DEPENDENCY_FILE_ORDER:
            if filename in available:
                return available[filename]
        return ""

    def _environment_strategy(self, execution_type: str) -> str:
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
        commands = ["python -m venv .venv"]
        if dependency_file == "requirements.txt":
            commands.append("pip install -r requirements.txt")
        elif dependency_file in {"pyproject.toml", "setup.py"}:
            commands.append("pip install -e .")
        elif dependency_file == "environment.yml":
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
        source_directories = {
            Path(path).as_posix() for path in report.repository.source_directories
        }
        if execution_type == "FastAPI" and "app" in source_directories:
            return "app/main.py"
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
        return Path(entry_point).with_suffix("").as_posix().replace("/", ".")

    @staticmethod
    def _unique(items: list[str]) -> list[str]:
        return list(dict.fromkeys(item for item in items if item))
