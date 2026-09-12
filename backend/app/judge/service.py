from __future__ import annotations

import ast
from pathlib import Path
from statistics import mean

from app.core.logging import get_logger
from app.research.paper_engine import PaperUnderstandingEngine
from app.research.services import ResearchIntelligenceService

from .models import JudgeReport, JudgeRequest, ScoreExplanation, Verdict

logger = get_logger("judge.engine")


class JudgeEngine:
    """Composes existing evidence into a transparent final evaluation."""

    weights = {
        "repository_score": 0.12,
        "code_quality": 0.10,
        "architecture_score": 0.10,
        "research_integrity": 0.12,
        "publication_readiness": 0.08,
        "reproducibility": 0.14,
        "security": 0.10,
        "maintainability": 0.08,
        "novelty": 0.05,
        "dataset_quality": 0.05,
        "execution_success": 0.06,
    }

    def __init__(
        self, research_service: ResearchIntelligenceService | None = None
    ) -> None:
        self.research_service = research_service or ResearchIntelligenceService()

    async def evaluate(
        self, request: JudgeRequest, repository_path: Path
    ) -> JudgeReport:
        root = repository_path.resolve()
        if not root.is_dir():
            raise ValueError(f"Repository path is not a directory: {root}")
        health = self.research_service.health_score(request.repository_id, root)
        risks = self.research_service.risk_heatmap(request.repository_id, root)
        environment = self.research_service.environment(root)
        files = self.research_service._files(root)
        source_files = [
            path
            for path in files
            if path.suffix in {".py", ".js", ".ts", ".tsx", ".java", ".rs"}
        ]
        test_files = [path for path in files if "test" in path.name.lower()]
        readme = any(path.name.lower() == "readme.md" for path in files)
        license_file = any(
            path.name.lower() in {"license", "license.txt", "copying"} for path in files
        )
        syntax_errors = self._syntax_errors(source_files)
        score_map: dict[str, ScoreExplanation] = {}
        score_map["repository_score"] = self._score(
            "repository_score",
            health.overall,
            [
                f"{len(files)} observable files",
                f"Detected languages: {', '.join(environment.languages) or 'none'}",
            ],
            health.suggestions,
        )
        score_map["code_quality"] = self._score(
            "code_quality",
            max(0, 100 - syntax_errors * 25),
            [
                f"{len(source_files)} source files",
                f"{syntax_errors} Python syntax errors",
            ],
            ["Fix parse errors before evaluation"] if syntax_errors else [],
        )
        score_map["architecture_score"] = self._score(
            "architecture_score",
            health.subscores.get("architecture", 0),
            [
                (
                    "Application/source boundary detected"
                    if health.subscores.get("architecture", 0) >= 70
                    else "No conventional app/src boundary detected"
                )
            ],
            [],
        )
        score_map["research_integrity"] = self._score(
            "research_integrity",
            self._research_integrity(readme, license_file, request.research_paper_path),
            [
                "README present" if readme else "README absent",
                "License present" if license_file else "License absent",
            ],
            [],
        )
        score_map["publication_readiness"] = self._score(
            "publication_readiness",
            mean(
                [
                    score_map["research_integrity"].score,
                    health.subscores.get("documentation", 0),
                    100 if license_file else 30,
                ]
            ),
            ["Documentation, integrity, and licensing signals combined"],
            [],
        )
        score_map["reproducibility"] = self._score(
            "reproducibility",
            mean(
                [
                    health.subscores.get("reproducibility", 0),
                    health.subscores.get("environment", 0),
                    health.subscores.get("dependencies", 0),
                ]
            ),
            [
                "Existing reproducibility signal",
                "Environment declaration signal",
                "Dependency manifest signal",
            ],
            [],
        )
        score_map["security"] = self._score(
            "security",
            max(0, 100 - risks.categories.get("security", 0)),
            [
                f"{len([item for item in risks.items if item.category == 'security'])} security risk items"
            ],
            [],
        )
        score_map["maintainability"] = self._score(
            "maintainability",
            health.subscores.get("maintainability", 0),
            [f"{len(source_files)} source files assessed"],
            [],
        )
        score_map["novelty"] = self._score(
            "novelty",
            50,
            [
                "Novelty provider not configured; no external corpus comparison was performed"
            ],
            ["Configure a novelty provider for evidence-based novelty assessment"],
        )
        score_map["dataset_quality"] = self._dataset_score(request.dataset_path, root)
        score_map["execution_success"] = self._execution_score(
            request.execution_success, request.execution_confidence
        )
        overall = round(
            sum(self.weights[name] * score_map[name].score for name in self.weights), 2
        )
        evidence_count = sum(bool(item.evidence) for item in score_map.values())
        confidence = round(
            evidence_count
            / len(score_map)
            * mean(item.confidence for item in score_map.values()),
            2,
        )
        verdict = self._verdict(overall, score_map)
        recommendations = [
            limitation for item in score_map.values() for limitation in item.limitations
        ]
        return JudgeReport(
            repository_id=request.repository_id,
            verdict=verdict,
            overall_score=overall,
            confidence=confidence,
            scores=score_map,
            recommendations=list(dict.fromkeys(recommendations)),
            evidence_summary=[
                f"{name}: {item.score:.0f}/100" for name, item in score_map.items()
            ],
        )

    def _score(
        self, name: str, score: float, evidence: list[str], limitations: list[str]
    ) -> ScoreExplanation:
        bounded = round(max(0, min(100, score)), 2)
        confidence = 0.85 if evidence and not limitations else 0.55
        return ScoreExplanation(
            name=name,
            score=bounded,
            evidence=evidence,
            rationale=f"{name} is calculated from {len(evidence)} observable evidence signal(s).",
            confidence=confidence,
            limitations=limitations,
        )

    def _dataset_score(self, dataset_path: str | None, root: Path) -> ScoreExplanation:
        if not dataset_path:
            return self._score(
                "dataset_quality",
                50,
                ["No dataset supplied"],
                ["Dataset quality is unverified"],
            )
        candidate = Path(dataset_path).resolve()
        if root not in candidate.parents:
            return self._score(
                "dataset_quality",
                0,
                ["Dataset path is outside repository"],
                ["Supply a dataset inside the evaluated repository"],
            )
        report = self.research_service.dataset_report(candidate)
        return self._score(
            "dataset_quality",
            report.quality_score,
            [
                f"{report.rows} rows and {report.columns} columns",
                f"{report.duplicate_rows} duplicate rows",
            ],
            report.warnings,
        )

    def _execution_score(
        self, success: bool | None, confidence: float | None
    ) -> ScoreExplanation:
        if success is None:
            return self._score(
                "execution_success",
                50,
                ["No execution result supplied"],
                ["Run the project in an approved sandbox"],
            )
        return self._score(
            "execution_success",
            100 if success else 0,
            [f"Execution success: {success}"],
            [] if success else ["Investigate the failed execution"],
        )

    @staticmethod
    def _research_integrity(
        readme: bool, license_file: bool, paper_path: str | None
    ) -> float:
        return mean(
            [
                100 if readme else 30,
                100 if license_file else 40,
                100 if paper_path else 50,
            ]
        )

    @staticmethod
    def _syntax_errors(files: list[Path]) -> int:
        errors = 0
        for path in files:
            if path.suffix == ".py":
                try:
                    ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
                except (OSError, SyntaxError):
                    errors += 1
        return errors

    @staticmethod
    def _verdict(overall: float, scores: dict[str, ScoreExplanation]) -> Verdict:
        critical = (
            scores["security"].score < 30 or scores["execution_success"].score < 30
        )
        if critical or overall < 45:
            return Verdict.REJECT
        if overall < 60:
            return Verdict.NEEDS_IMPROVEMENT
        if overall < 80:
            return Verdict.WEAK_PASS
        return Verdict.PASS
