"""Tests for preview-only patch generation and validation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.services.patch_generator.models import PatchGenerationInput
from app.services.patch_generator.patch_service import PatchGenerationService


class PatchGeneratorTest(unittest.TestCase):
    def test_generates_pandas_unified_diff_and_valid_python(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            source = repository / "main.py"
            source.write_text(
                "import pandas as pd\ndf = df.append(row)\n", encoding="utf-8"
            )
            result = PatchGenerationService().generate(
                PatchGenerationInput(
                    execution_id="run-1",
                    repository_path=str(repository),
                    repository_tree=["main.py"],
                    problematic_file="main.py",
                    root_cause="Deprecated API",
                    error_message="pandas append is deprecated",
                    suggested_fix="Use pandas.concat",
                )
            )

        self.assertEqual(result.file_name, "main.py")
        self.assertIn("--- a/main.py", result.git_unified_diff)
        self.assertIn("+++ b/main.py", result.git_unified_diff)
        self.assertIn("pd.concat([df, row], ignore_index=True)", result.modified_file)
        self.assertEqual(result.changed_files, ["main.py"])
        self.assertGreater(result.patch_confidence, 0)

    def test_rejects_binary_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            target = repository / "data.bin"
            target.write_bytes(b"\x00\x01")
            with self.assertRaises(ValueError):
                PatchGenerationService().generate(
                    PatchGenerationInput(
                        execution_id="run-2",
                        repository_path=str(repository),
                        repository_tree=["data.bin"],
                        problematic_file="data.bin",
                        root_cause="Unknown",
                    )
                )

    def test_returns_preview_warning_when_fix_is_not_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            source = repository / "main.py"
            source.write_text("raise RuntimeError('failure')\n", encoding="utf-8")
            result = PatchGenerationService().generate(
                PatchGenerationInput(
                    execution_id="run-3",
                    repository_path=str(repository),
                    repository_tree=["main.py"],
                    problematic_file="main.py",
                    root_cause="RuntimeError",
                    error_message="RuntimeError: failure",
                )
            )

        self.assertEqual(result.git_unified_diff, "")
        self.assertEqual(result.changed_files, [])
        self.assertTrue(result.warnings)


if __name__ == "__main__":
    unittest.main()
