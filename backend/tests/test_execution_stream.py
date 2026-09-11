"""Integration coverage for the live execution SSE endpoint."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.api.routes import stream_execution
from app.core.config import Settings


class ExecutionStreamIntegrationTest(unittest.TestCase):
    def test_streams_real_execution_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            uploads = root / "uploads"
            repository = uploads / "demo" / "repository"
            repository.mkdir(parents=True)
            (repository / "README.md").write_text("# Demo\n")
            (repository / "requirements.txt").write_text("# empty\n")
            (repository / "main.py").write_text("print('live-output')\n")
            settings = Settings(
                UPLOAD_DIR=str(uploads),
                REPORTS_DIR=str(root / "reports"),
            )

            async def consume() -> list[dict[str, object]]:
                with patch("app.api.routes.get_settings", return_value=settings):
                    response = await stream_execution("demo")
                    events: list[dict[str, object]] = []
                    async for chunk in response.body_iterator:
                        line = chunk.decode() if isinstance(chunk, bytes) else chunk
                        if line.startswith("data: "):
                            events.append(json.loads(line[6:].strip()))
                    return events

            events = asyncio.run(consume())

        stages = [event["stage"] for event in events]
        self.assertIn("REPOSITORY_ANALYSIS_COMPLETE", stages)
        self.assertIn("EXECUTION_PLAN_GENERATED", stages)
        self.assertIn("COPY_COMPLETED", stages)
        self.assertIn("EXECUTION_FINISHED", stages)
        self.assertIn("CLEANUP_COMPLETED", stages)
        self.assertTrue(any(event["stage"] == "STDOUT" for event in events))
        self.assertEqual(events[-1]["stage"], "VERIFICATION_READY")


if __name__ == "__main__":
    unittest.main()
