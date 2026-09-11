"""Verify upload automatically extracts and analyzes a repository."""

from __future__ import annotations

import asyncio
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from app.core.config import Settings
from app.services.upload_service import handle_upload


class FakeUpload:
    filename = "demo.zip"
    content_type = "application/zip"

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    async def read(self) -> bytes:
        return self._payload


class UploadAnalysisIntegrationTest(unittest.TestCase):
    def test_upload_extracts_repository_and_returns_relative_path(self) -> None:
        archive_buffer = io.BytesIO()
        with ZipFile(archive_buffer, "w") as zip_file:
            zip_file.writestr("README.md", "# demo")
            zip_file.writestr("requirements.txt", "")
            zip_file.writestr("main.py", "print('ok')")
            zip_file.writestr("data.csv", "value\n1\n")

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            settings = Settings(
                UPLOAD_DIR=str(root / "uploads"),
                REPORTS_DIR=str(root / "reports"),
            )
            with patch(
                "app.services.upload_service.get_settings", return_value=settings
            ):
                result = asyncio.run(
                    handle_upload(FakeUpload(archive_buffer.getvalue()))
                )

            extracted = root / "uploads" / result.upload_id / "repository"
            self.assertEqual(result.repository_path, f"{result.upload_id}/repository")
            self.assertTrue((extracted / "main.py").is_file())
            self.assertTrue((extracted / "data.csv").is_file())


if __name__ == "__main__":
    unittest.main()
