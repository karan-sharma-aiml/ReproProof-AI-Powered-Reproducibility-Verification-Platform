"""Smoke tests for SandboxExecutionEngine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import os

from app.models.execution_plan import ExecutionPlan
from app.services.execution_event_publisher import ExecutionEventPublisher
from app.services.sandbox_execution_engine import SandboxExecutionEngine


def plan_for(*commands: str) -> ExecutionPlan:
    return ExecutionPlan(
        python_version="3.11",
        environment_strategy="Python virtual environment (.venv)",
        dependency_file="",
        entry_point="main.py",
        execution_type="Python Script",
        commands=list(commands),
        risks=[],
        assumptions=[],
    )


class SandboxExecutionEngineSmokeTest(unittest.TestCase):
    def test_executes_inside_temporary_copy_and_captures_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            (repository / "marker.txt").write_text("original")
            result = SandboxExecutionEngine().execute(
                repository,
                plan_for("py --version"),
            )
            original_content = (repository / "marker.txt").read_text()

        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.timed_out)
        self.assertGreaterEqual(result.execution_time, 0)
        self.assertTrue(result.stdout or result.stderr)
        self.assertEqual(original_content, "original")

    def test_rejects_inline_code_and_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            with self.assertRaises(ValueError):
                SandboxExecutionEngine().execute(
                    repository,
                    plan_for("py -c print('unsafe')"),
                )
            with self.assertRaises(ValueError):
                SandboxExecutionEngine().execute(
                    repository,
                    plan_for("py ../outside.py"),
                )

    def test_stops_on_nonzero_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = SandboxExecutionEngine().execute(
                Path(temporary_directory),
                plan_for("py --definitely-invalid-option"),
            )

        self.assertFalse(result.success)
        self.assertNotEqual(result.exit_code, 0)
        self.assertFalse(result.timed_out)

    def test_handles_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            (repository / "sleep.py").write_text("import time\ntime.sleep(2)\n")
            result = SandboxExecutionEngine(timeout_seconds=0.1).execute(
                repository,
                plan_for("py sleep.py"),
            )

        self.assertFalse(result.success)
        self.assertTrue(result.timed_out)
        self.assertEqual(result.status, "TIMEOUT")
        self.assertIn("Cleaning sandbox...", result.logs)

    def test_installs_empty_requirements_manifest_inside_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            (repository / "requirements.txt").write_text("# local test manifest\n")
            result = SandboxExecutionEngine().execute(
                repository,
                plan_for("py --version"),
            )

        self.assertTrue(result.success)
        self.assertTrue(result.installed_dependencies)
        self.assertIn("Dependencies installed successfully.", result.logs)

    def test_sandbox_isolated_and_cleaned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "repository"
            sandbox_root = Path(temporary_directory) / "sandbox"
            repository.mkdir()
            (repository / "marker.txt").write_text("original")
            result = SandboxExecutionEngine(sandbox_root=sandbox_root).execute(
                repository,
                plan_for("py --version"),
            )

            self.assertFalse(Path(result.sandbox_path).exists())
            self.assertEqual((repository / "marker.txt").read_text(), "original")

    def test_publishes_progress_events_and_persists_log(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "repository"
            reports = Path(temporary_directory) / "reports"
            repository.mkdir()
            publisher = ExecutionEventPublisher()
            events = []
            publisher.subscribe(events.append)
            result = SandboxExecutionEngine(
                reports_root=reports,
                event_publisher=publisher,
            ).execute(repository, plan_for("py --version"))
            log_exists = Path(result.log_path).is_file()

        self.assertTrue(result.success)
        stages = [event.stage for event in events]
        self.assertIn("COPY_STARTED", stages)
        self.assertIn("EXECUTION_STARTED", stages)
        self.assertIn("EXECUTION_FINISHED", stages)
        self.assertIn("CLEANUP_COMPLETED", stages)
        self.assertTrue(log_exists)

    def test_rejects_unsupported_executable_and_shell_injection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            with self.assertRaises(ValueError):
                SandboxExecutionEngine().execute(repository, plan_for("node main.js"))
            with self.assertRaises(ValueError):
                SandboxExecutionEngine().execute(
                    repository, plan_for("py main.py; whoami")
                )

    def test_resolves_nested_repository_entrypoint_from_own_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "repository"
            repository.mkdir()
            nested = repository / "research-demo"
            nested.mkdir()
            (nested / "requirements.txt").write_text("\n")
            (nested / "main.py").write_text("print('nested-ok')\n")

            result = SandboxExecutionEngine().execute(
                repository,
                plan_for("py main.py"),
            )

        self.assertTrue(result.success, msg=result.stderr)
        self.assertEqual(result.status, "COMPLETED")
        self.assertIn("nested-ok", result.stdout)

    def test_verifies_long_running_uvicorn_before_graceful_termination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "repository"
            repository.mkdir()
            (repository / "app.py").write_text(
                "from fastapi import FastAPI\n"
                "app = FastAPI()\n"
                "@app.get('/health')\n"
                "def health(): return {'status': 'ok'}\n"
            )
            result = SandboxExecutionEngine(timeout_seconds=2).execute(
                repository,
                plan_for("uvicorn app:app"),
            )

        self.assertTrue(result.success, msg=result.stderr)
        self.assertFalse(result.timed_out)
        self.assertEqual(result.status, "EXECUTION_COMPLETE")
        self.assertIn("Health check response", result.stdout)

    def test_rejects_symbolic_links_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            target = repository / "target.txt"
            target.write_text("target")
            link = repository / "link.txt"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links are unavailable in this environment")
            with self.assertRaises(ValueError):
                SandboxExecutionEngine().execute(repository, plan_for("py --version"))


if __name__ == "__main__":
    unittest.main()
