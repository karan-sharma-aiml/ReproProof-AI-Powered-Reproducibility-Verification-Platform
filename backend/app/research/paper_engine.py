from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

from .engines import DocumentUnderstandingEngine
from .errors import ProviderUnavailableError
from .models import (
    Citation,
    CitationGraph,
    MethodologyFinding,
    PaperAnalysis,
    ProviderAnalysis,
)
from .ports import LLMProvider, NoveltyProvider, ResearchAnalysisProvider

logger = get_logger("research.paper")


class PaperUnderstandingEngine:
    """Builds a structured paper model from extracted text and observable evidence."""

    _method_terms = (
        "methodology",
        "methods",
        "approach",
        "algorithm",
        "architecture",
        "experimental setup",
        "implementation",
        "training procedure",
    )

    def __init__(
        self, document_engine: DocumentUnderstandingEngine | None = None
    ) -> None:
        self.document_engine = document_engine or DocumentUnderstandingEngine()

    async def analyze(self, path: Path) -> PaperAnalysis:
        document = await self.document_engine.process(path)
        sections = self._section_bodies(document.text, document.sections)
        methodology = self._methodology(document.text, sections)
        citations = self._citations(document.text)
        graph = CitationGraph(
            document_name=document.name,
            nodes=[document.name, *[citation.key for citation in citations]],
            edges=[
                {"source": document.name, "target": citation.key, "kind": "cites"}
                for citation in citations
            ],
            unresolved_citations=[
                citation.key for citation in citations if not citation.raw_text
            ],
        )
        claims = self._claims(document.text)
        summary = self._summary(document.text, sections)
        return PaperAnalysis(
            document=document,
            citations=citations,
            citation_graph=graph,
            methodology=methodology,
            claims=claims,
            summary=summary,
        )

    def _methodology(self, text: str, sections: list[Any]) -> list[MethodologyFinding]:
        findings: list[MethodologyFinding] = []
        for section in sections:
            content = section.text or ""
            if any(term in section.heading.lower() for term in self._method_terms):
                findings.append(
                    MethodologyFinding(
                        section=section.heading,
                        method=section.heading,
                        evidence=content[:500],
                        confidence=0.8,
                    )
                )
        if not findings:
            for match in re.finditer(
                r"([^.!?]*(?:we use|we propose|we train|we evaluate|dataset|baseline)[^.!?]*[.!?])",
                text,
                re.I,
            ):
                sentence = match.group(1).strip()
                findings.append(
                    MethodologyFinding(
                        section="inferred methodology",
                        method="method statement",
                        evidence=sentence,
                        confidence=0.55,
                    )
                )
        return findings[:30]

    def _section_bodies(self, text: str, sections: list[Any]) -> list[Any]:
        headings = list(re.finditer(r"^(#{1,6})\s+(.+)$", text, flags=re.MULTILINE))
        if not headings:
            return sections
        enriched = []
        for index, heading in enumerate(headings):
            end = (
                headings[index + 1].start() if index + 1 < len(headings) else len(text)
            )
            enriched.append(
                sections[index].model_copy(
                    update={"text": text[heading.end() : end].strip()}
                )
            )
        return enriched

    def _citations(self, text: str) -> list[Citation]:
        citations: list[Citation] = []
        for match in re.finditer(r"\[([^\]]{1,80})\]|\(([^()]{2,80}\d{4})\)", text):
            raw = match.group(0)
            key = (match.group(1) or match.group(2) or raw).strip()
            if key not in {citation.key for citation in citations}:
                citations.append(Citation(key=key, raw_text=raw))
        return citations

    def _claims(self, text: str) -> list[str]:
        return [
            match.group(1).strip()
            for match in re.finditer(
                r"\b(?:we|this work|our method)\s+([^.!?]{20,240}[.!?])", text, re.I
            )
        ][:30]

    def _summary(self, text: str, sections: list[Any]) -> str:
        if sections:
            return " ".join((section.text or "") for section in sections[:3]).strip()[
                :1200
            ]
        return " ".join(text.split())[:1200]


class CitationGraphEngine:
    def build(self, analysis: PaperAnalysis) -> CitationGraph:
        return analysis.citation_graph


class ProviderResearchEngine:
    """Routes advanced research capabilities through an injected provider."""

    capabilities = (
        "research_gap_detection",
        "novelty_detection",
        "claim_verification",
        "benchmark_comparison",
        "research_recommendations",
        "future_work",
        "literature_review",
        "auto_reviewer",
    )

    def __init__(self, provider: ResearchAnalysisProvider | None = None) -> None:
        self.provider = provider

    async def run(
        self,
        capability: str,
        analysis: PaperAnalysis,
        context: dict[str, Any] | None = None,
    ) -> ProviderAnalysis:
        if capability not in self.capabilities:
            raise ValueError(f"Unsupported research capability: {capability}")
        if self.provider is None:
            raise ProviderUnavailableError(
                f"A ResearchAnalysisProvider is required for {capability}"
            )
        result = await self.provider.analyze(
            capability, {"analysis": analysis.model_dump(), "context": context or {}}
        )
        return ProviderAnalysis(
            capability=capability,
            result=result,
            provider=self.provider.name,
            evidence=[analysis.document.name],
        )


class ResearchAssistant:
    """Provider-backed assistant with explicit capability routing."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider

    async def ask(self, question: str, analysis: PaperAnalysis | None = None) -> str:
        if not question.strip():
            raise ValueError("Research question cannot be empty")
        if self.provider is None:
            raise ProviderUnavailableError(
                "A configured LLMProvider is required for the research assistant"
            )
        context = analysis.model_dump() if analysis else {}
        return await self.provider.complete(question, context=context)
