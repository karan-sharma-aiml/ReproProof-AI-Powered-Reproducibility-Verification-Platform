"""Smoke tests for ReproProofAgent."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.models.execution_plan import ExecutionPlan
from app.models.observation_report import ObservationReport
from app.models.project_detection import ProjectDetection
from app.models.repository import RepositoryMetadata
from app.services.reproproof_agent import ReproProofAgent


def make_report(execution_ready: bool) -> ObservationReport:
    return ObservationReport(
        repository=RepositoryMetadata(
            repository_name="sample",
            total_files=3,
            total_folders=1,
            python_files=1,
            notebooks=0,
            important_files=["README.md", "requirements.txt"],
            source_directories=["app"],
            detected_languages=["Python"],
        ),
        project=ProjectDetection(
            project_type="Web API",
            framework="fastapi",
            detection_confidence=70,
            reason="fastapi is declared in a project dependency file",
        ),
        health_score=100 if execution_ready else 60,
        execution_ready=execution_ready,
        warnings=(
            [] if execution_ready else ["No recognizable Python entry point was found"]
        ),
        recommendations=[],
    )


class FakeObservationCoordinator:
    def __init__(self, report: ObservationReport) -> None:
        self.report = report
        self.received_path: Path | None = None

    def observe(self, repo_path: Path) -> ObservationReport:
        self.received_path = repo_path
        return self.report


class FakePlanGenerator:
    def __init__(self) -> None:
        self.received_report: ObservationReport | None = None

    def create_plan(self, report: ObservationReport) -> ExecutionPlan:
        self.received_report = report
        return ExecutionPlan(
            python_version="3.11",
            environment_strategy="Python virtual environment (.venv)",
            dependency_file="requirements.txt",
            entry_point="main.py",
            execution_type="FastAPI",
            commands=["uvicorn main:app"],
            risks=[],
            assumptions=["Plan is text only"],
        )


class ReproProofAgentSmokeTest(unittest.TestCase):
    def test_returns_ready_execute_result_and_injects_dependencies(self) -> None:
        coordinator = FakeObservationCoordinator(make_report(True))
        planner = FakePlanGenerator()
        agent = ReproProofAgent(coordinator, planner)

        with tempfile.TemporaryDirectory() as temporary_directory:
            repository_path = Path(temporary_directory)
            result = agent.run(repository_path)

        self.assertEqual(result.status, "READY")
        self.assertEqual(result.next_action, "EXECUTE")
        self.assertEqual(result.goal, "Verify repository")
        self.assertEqual(coordinator.received_path, repository_path)
        self.assertIs(planner.received_report, result.observation)
        self.assertEqual(result.blocking_reasons, [])

    def test_stops_with_structured_explanation_when_not_ready(self) -> None:
        result = ReproProofAgent(
            FakeObservationCoordinator(make_report(False)),
            FakePlanGenerator(),
        ).run(Path("repository"))

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.next_action, "STOP")
        self.assertIn(
            "No recognizable Python entry point was found", result.explanation
        )
        self.assertEqual(
            result.blocking_reasons,
            ["No recognizable Python entry point was found"],
        )


if __name__ == "__main__":
    unittest.main()
