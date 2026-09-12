"""Normalize execution and repository evidence for troubleshooting."""

from __future__ import annotations

from pathlib import Path

from app.models.execution_result import ExecutionResult
from app.services.troubleshooter.models import ParsedExecution


class ExecutionEvidenceParser:
    """Build bounded, structured evidence without executing repository code."""

    MAX_TEXT_BYTES = 2_000_000

    def parse(
        self,
        execution_id: str,
        execution: ExecutionResult,
        repository_path: Path,
        repository_tree: list[str],
    ) -> ParsedExecution:
        root = Path(repository_path)
        requirements = self._read(root / "requirements.txt")
        execution_log = (
            self._read(Path(execution.log_path)) if execution.log_path else ""
        )
        combined = "\n".join(
            part for part in (execution.stderr, execution.stdout) if part
        )
        traceback = self._extract_traceback(combined)
        python_version = self._python_version(execution)
        return ParsedExecution(
            execution_id=execution_id,
            stdout=execution.stdout,
            stderr=execution.stderr,
            traceback=traceback,
            exit_code=execution.exit_code,
            execution_time=execution.execution_time,
            working_directory=execution.sandbox_path,
            python_version=python_version,
            repository_path=str(root.resolve()),
            repository_tree=repository_tree,
            requirements=requirements,
            execution_log=execution_log,
        )

    @classmethod
    def _read(cls, path: Path) -> str:
        try:
            if not path.is_file():
                return ""
            return path.read_bytes()[: cls.MAX_TEXT_BYTES].decode(
                "utf-8", errors="ignore"
            )
        except OSError:
            return ""

    @staticmethod
    def _extract_traceback(output: str) -> str:
        marker = "Traceback (most recent call last):"
        index = output.find(marker)
        return output[index:].strip() if index >= 0 else ""

    @staticmethod
    def _python_version(execution: ExecutionResult) -> str:
        for line in (execution.stdout + "\n" + execution.stderr).splitlines():
            if "python" in line.lower() and any(char.isdigit() for char in line):
                return line.strip()
        return "unknown"
