"""Extract numeric research metrics from captured execution artifacts."""

from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

from app.core.logging import get_logger
from app.models.execution_result import ExecutionResult

logger = get_logger("metric_extraction_service")


class MetricExtractionService:
    """Parse only captured output/files; never rerun or import repository code."""

    METRIC_ALIASES = {
        "accuracy": "accuracy",
        "acc": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1_score",
        "f1_score": "f1_score",
        "loss": "loss",
        "mse": "mse",
        "rmse": "rmse",
        "mae": "mae",
        "roc_auc": "roc_auc",
        "auc": "roc_auc",
        "map": "map",
        "bleu": "bleu",
        "rouge": "rouge",
    }
    NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"

    def extract(self, result: ExecutionResult) -> dict[str, float]:
        """Extract metrics from stdout, stderr, persisted logs, and structured text."""
        sources = [result.stdout, result.stderr]
        if result.log_path:
            path = Path(result.log_path)
            if path.is_file():
                try:
                    sources.append(path.read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    logger.warning("Could not read execution log: %s", path)
        metrics: dict[str, float] = {}
        for source in sources:
            metrics.update(self._extract_json(source))
            metrics.update(self._extract_csv(source))
            metrics.update(self._extract_text(source))
        logger.info("Extracted %d metrics from execution result", len(metrics))
        return metrics

    def _extract_text(self, source: str) -> dict[str, float]:
        found: dict[str, float] = {}
        pattern = re.compile(
            rf"(?im)(?:^|[{{,\s])['\"]?([a-zA-Z][\w .-]*)['\"]?\s*(?:=|:)\s*({self.NUMBER})\s*%?"
        )
        for match in pattern.finditer(source):
            key = self._normalize(match.group(1))
            if key:
                found[key] = float(match.group(2))
        return found

    def _extract_json(self, source: str) -> dict[str, float]:
        found: dict[str, float] = {}
        for line in source.splitlines():
            candidate = line.strip()
            if not (candidate.startswith("{") and candidate.endswith("}")):
                continue
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                for key, value in payload.items():
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        normalized = self._normalize(str(key))
                        if normalized:
                            found[normalized] = float(value)
        return found

    def _extract_csv(self, source: str) -> dict[str, float]:
        found: dict[str, float] = {}
        for line in source.splitlines():
            stripped = line.strip()
            if not stripped or "," not in stripped:
                continue
            try:
                row = next(csv.reader([stripped], skipinitialspace=True))
            except (csv.Error, TypeError):
                continue
            if len(row) != 2:
                continue
            key, value = row
            if not isinstance(key, str) or not isinstance(value, str):
                continue
            key = key.strip()
            value = value.strip()
            if not key or not value:
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            normalized = self._normalize(key)
            if normalized:
                found[normalized] = number
        return found

    def _normalize(self, key: str) -> str | None:
        normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
        return self.METRIC_ALIASES.get(
            normalized,
            (
                normalized
                if normalized
                in {"custom_numeric", "rmse", "roc_auc", "map", "bleu", "rouge"}
                else None
            ),
        )
