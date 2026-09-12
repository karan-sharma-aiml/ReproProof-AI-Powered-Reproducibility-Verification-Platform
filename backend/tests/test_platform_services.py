"""Tests for Phase 4 platform services."""

from __future__ import annotations

import unittest

from app.models.execution_result import ExecutionResult
from app.models.repository import RepositoryMetadata
from app.models.repository_ai_analysis import RepositoryAIAnalysis
from app.services.platform.analytics_service import AnalyticsService
from app.services.platform.health_score_service import HealthScoreService
from app.services.platform.progress_service import ProgressBroker


class PlatformServicesTest(unittest.TestCase):
    def test_health_score_and_analytics_are_explainable(self) -> None:
        repository = RepositoryMetadata(
            repository_name="demo",
            repository_id="demo",
            total_files=3,
            total_folders=1,
            python_files=1,
            notebooks=0,
            important_files=["README.md", "requirements.txt", "main.py", "Dockerfile"],
            source_directories=["tests"],
            detected_languages=["Python"],
            detected_frameworks=["FastAPI"],
            health_score=90,
        )
        analysis = RepositoryAIAnalysis(
            repository_id="demo",
            repository_name="demo",
            execution_probability=90,
            reproducibility_score=90,
            risk_score=10,
            summary="clean",
        )
        execution = ExecutionResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            execution_time=1.5,
            timed_out=False,
        )
        score = HealthScoreService().calculate(repository, analysis, execution)
        analytics = AnalyticsService().summarize([])
        self.assertGreater(score.score, 70)
        self.assertEqual(analytics.total_runs, 0)

    def test_progress_broker_fans_out_typed_events(self) -> None:
        broker = ProgressBroker()
        subscriber = broker.subscribe("run-1")
        event = broker.publish("run-1", "AI_ANALYSIS", "RUNNING", 50, "Analyzing")
        self.assertEqual(subscriber.get_nowait(), event)
        self.assertEqual(event.progress, 50)
        broker.unsubscribe("run-1", subscriber)


if __name__ == "__main__":
    unittest.main()
