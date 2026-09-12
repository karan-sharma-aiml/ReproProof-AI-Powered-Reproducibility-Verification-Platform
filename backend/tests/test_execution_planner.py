"""Smoke tests for ExecutionPlanner."""

from __future__ import annotations

import unittest

from app.models.observation_report import ObservationReport
from app.models.project_detection import ProjectDetection
from app.models.repository import RepositoryMetadata
from app.services.execution_planner import ExecutionPlanner


def fastapi_report(ready: bool = True) -> ObservationReport:
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
        health_score=100 if ready else 60,
        execution_ready=ready,
        warnings=[] if ready else ["README.md is missing"],
        recommendations=[],
    )


class ExecutionPlannerSmokeTest(unittest.TestCase):
    def test_generates_fastapi_plan_without_execution(self) -> None:
        plan = ExecutionPlanner().create_plan(fastapi_report())

        self.assertEqual(plan.execution_type, "FastAPI")
        self.assertEqual(plan.entry_point, "app/main.py")
        self.assertEqual(plan.dependency_file, "requirements.txt")
        self.assertIn("uvicorn app.main:app", plan.commands)
        self.assertIn("python -m venv .venv", plan.commands)

    def test_supports_injected_entry_point_policy(self) -> None:
        planner = ExecutionPlanner(
            entry_point_resolver=lambda report, execution_type: "service.py"
        )

        plan = planner.create_plan(fastapi_report())

        self.assertEqual(plan.entry_point, "service.py")
        self.assertIn("uvicorn service:app", plan.commands)

    def test_non_ready_report_keeps_commands_and_surfaces_risk(self) -> None:
        plan = ExecutionPlanner().create_plan(fastapi_report(ready=False))

        self.assertIn("pip install -r requirements.txt", plan.commands)
        self.assertIn("uvicorn app.main:app", plan.commands)
        self.assertIn("Observation report is not execution-ready", plan.risks)


if __name__ == "__main__":
    unittest.main()
