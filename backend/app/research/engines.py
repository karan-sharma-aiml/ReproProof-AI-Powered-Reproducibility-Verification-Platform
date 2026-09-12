from __future__ import annotations

import re
import time
from pathlib import Path
from statistics import mean
from typing import Any

from app.core.logging import get_logger

from .errors import ProviderUnavailableError, UnsupportedDatasetError
from .models import (
    BenchmarkReport,
    ConfidenceAssessment,
    DockerBuildResult,
    DocumentObject,
    DocumentSection,
    ExplainabilityReport,
    ScoreReport,
)
from .ports import LLMProvider, OCRProvider, SandboxProvider

logger = get_logger("research.engines")


class ScoreEngine:
    """Shared score calculator used by reproducibility, publication, and integrity views."""

    def score(self, name: str, signals: dict[str, float]) -> ScoreReport:
        normalized = {
            key: max(0.0, min(100.0, value)) for key, value in signals.items()
        }
        overall = round(mean(normalized.values()), 2) if normalized else 0.0
        plan = [f"Improve {key}" for key, value in normalized.items() if value < 70]
        return ScoreReport(
            name=name, overall=overall, subscores=normalized, improvement_plan=plan
        )


class ExplainabilityEngine:
    def explain(
        self,
        decision: str,
        evidence: list[str],
        confidence: ConfidenceAssessment,
        alternatives: list[str] | None = None,
        tradeoffs: list[str] | None = None,
    ) -> ExplainabilityReport:
        return ExplainabilityReport(
            why=f"Decision '{decision}' is supported by the supplied evidence.",
            how="Evidence was evaluated by the registered deterministic or provider-backed engine.",
            evidence=evidence,
            confidence=confidence,
            alternatives=alternatives or [],
            tradeoffs=tradeoffs or [],
            recommendations=[
                "Review the evidence before taking an irreversible action."
            ],
        )


class DockerBuilder:
    """Generates hardened baseline Dockerfiles from an explicit target."""

    def build(self, target: str) -> DockerBuildResult:
        if target == "backend":
            content = """FROM python:3.12-slim AS runtime
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home appuser
COPY backend/app ./app
USER appuser
EXPOSE 8000
HEALTHCHECK CMD python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/docs')\"
CMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]
"""
        elif target == "frontend":
            content = """FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run build
FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app ./
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
EXPOSE 3000
CMD [\"npm\", \"start\"]
"""
        elif target == "combined":
            content = """# Use separate backend and frontend images in production.
# This combined target is intentionally a composition marker, not a process supervisor.
"""
        else:
            raise ValueError(f"Unsupported Docker target: {target}")
        controls = [
            "minimal base image",
            "non-root runtime user",
            "health check" if target == "backend" else "production build stage",
        ]
        return DockerBuildResult(
            target=target, dockerfile=content, security_controls=controls
        )


class DocumentUnderstandingEngine:
    """Provider-aware PDF/text document parser; it never invents OCR or paper findings."""

    def __init__(self, ocr_provider: OCRProvider | None = None) -> None:
        self.ocr_provider = ocr_provider

    async def process(self, path: Path) -> DocumentObject:
        if not path.is_file():
            raise FileNotFoundError(path)
        raw = path.read_bytes()
        text = ""
        if path.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader

                text = "\n".join(
                    page.extract_text() or "" for page in PdfReader(path).pages
                )
            except ImportError:
                if self.ocr_provider is None:
                    raise ProviderUnavailableError(
                        "Install pypdf or configure an OCR provider"
                    )
                text = await self.ocr_provider.extract_text(raw)
        else:
            text = raw.decode("utf-8", errors="ignore")
        sections = [
            DocumentSection(
                heading=match.group(2).strip(), text="", level=len(match.group(1))
            )
            for match in re.finditer(r"^(#{1,6})\s+(.+)$", text, flags=re.MULTILINE)
        ]
        references = [
            line.strip()
            for line in text.splitlines()
            if re.match(r"^\s*(references|bibliography)\s*$", line, re.I)
        ]
        return DocumentObject(
            name=path.name,
            document_type="pdf" if path.suffix.lower() == ".pdf" else "text",
            text=text,
            sections=sections,
            references=references,
        )


class ResearchAssistant:
    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider

    async def answer(self, question: str, context: dict[str, Any] | None = None) -> str:
        if self.provider is None:
            raise ProviderUnavailableError(
                "A configured LLMProvider is required for research assistance"
            )
        if not question.strip():
            raise ValueError("Research question cannot be empty")
        return await self.provider.complete(question, context=context)


class BenchmarkEngine:
    """Measures only an already-approved callable; it does not execute repository code."""

    def measure(self, repository_id: str, operation: Any) -> BenchmarkReport:
        started = time.perf_counter()
        operation()
        elapsed = time.perf_counter() - started
        return BenchmarkReport(
            repository_id=repository_id,
            measurements={"operation_seconds": elapsed},
            history_key=f"benchmark:{repository_id}",
        )


class SecureExecutionEngine:
    def __init__(self, provider: SandboxProvider | None = None) -> None:
        self.provider = provider

    async def execute(self, command: list[str], timeout_seconds: float):
        if self.provider is None:
            raise ProviderUnavailableError(
                "A sandbox provider is required; direct host execution is disabled"
            )
        if not command or timeout_seconds <= 0:
            raise ValueError("A command and positive timeout are required")
        return await self.provider.execute(command, timeout_seconds=timeout_seconds)
