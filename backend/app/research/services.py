from __future__ import annotations

import ast
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from app.core.logging import get_logger

from .errors import RepositoryNotFoundError, UnsupportedDatasetError
from .models import (
    DatasetQualityReport,
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    EnvironmentSpec,
    HealthScore,
    RiskHeatmap,
    RiskItem,
    Timeline,
    TimelineEvent,
)

logger = get_logger("research.intelligence")


class ResearchIntelligenceService:
    """Deterministic repository intelligence built from observable local evidence."""

    ignored = {".git", ".venv", "node_modules", "__pycache__", ".next"}

    def _root(self, repository_path: Path) -> Path:
        root = repository_path.resolve()
        if not root.exists() or not root.is_dir():
            raise RepositoryNotFoundError(str(repository_path))
        return root

    def _files(self, root: Path) -> list[Path]:
        return [
            p
            for p in root.rglob("*")
            if p.is_file() and not self.ignored.intersection(p.parts)
        ]

    def risk_heatmap(self, repository_id: str, repository_path: Path) -> RiskHeatmap:
        root = self._root(repository_path)
        items: list[RiskItem] = []
        category_scores: dict[str, list[float]] = defaultdict(list)
        files = self._files(root)
        for path in files:
            relative = path.relative_to(root).as_posix()
            suffix = path.suffix.lower()
            try:
                size = path.stat().st_size
            except OSError:
                continue
            signals: list[tuple[str, float, str]] = []
            if size > 500_000:
                signals.append(("maintainability", 60, "large source artifact"))
            if suffix in {".env", ".pem", ".key"}:
                signals.append(("security", 95, "sensitive-looking file extension"))
            if suffix in {".py", ".js", ".ts", ".tsx", ".java", ".rs"}:
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    if "TODO" in text or "FIXME" in text:
                        signals.append(
                            ("technical_debt", 45, "unresolved TODO/FIXME marker")
                        )
                    if "password" in text.lower() or "api_key" in text.lower():
                        signals.append(
                            ("security", 80, "credential-like identifier in source")
                        )
                except OSError:
                    pass
            for category, score, evidence in signals:
                items.append(
                    RiskItem(
                        path=relative,
                        category=category,
                        score=score,
                        evidence=[evidence],
                    )
                )
                category_scores[category].append(score)
        categories = {
            key: round(statistics.mean(values), 2)
            for key, values in category_scores.items()
        }
        overall = (
            round(statistics.mean([item.score for item in items]), 2) if items else 0
        )
        logger.info(
            "risk_heatmap_generated repository_id=%s items=%d",
            repository_id,
            len(items),
        )
        return RiskHeatmap(
            repository_id=repository_id,
            overall_risk=overall,
            items=items,
            categories=categories,
        )

    def dependency_graph(
        self, repository_id: str, repository_path: Path
    ) -> DependencyGraph:
        root = self._root(repository_path)
        nodes: dict[str, DependencyNode] = {}
        edges: list[DependencyEdge] = []
        adjacency: dict[str, set[str]] = defaultdict(set)
        for path in self._files(root):
            if path.suffix != ".py":
                continue
            source = path.relative_to(root).as_posix()
            nodes[source] = DependencyNode(id=source, label=source, kind="module")
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports = [node.module]
                else:
                    continue
                for imported in imports:
                    target = imported.replace(".", "/") + ".py"
                    candidate = next(
                        (item for item in nodes if item.endswith(target)), None
                    )
                    if candidate and candidate != source:
                        edges.append(DependencyEdge(source=source, target=candidate))
                        adjacency[source].add(candidate)
        cycles = self._cycles(adjacency)
        for node in nodes.values():
            node.hotspot_score = round(
                min(
                    100, sum(node.id in targets for targets in adjacency.values()) * 10
                ),
                2,
            )
        return DependencyGraph(
            repository_id=repository_id,
            nodes=list(nodes.values()),
            edges=edges,
            circular_dependencies=cycles,
        )

    def _cycles(self, adjacency: dict[str, set[str]]) -> list[list[str]]:
        found: set[tuple[str, ...]] = set()

        def visit(start: str, current: str, trail: list[str]) -> None:
            for target in adjacency.get(current, set()):
                if target == start and len(trail) > 1:
                    cycle = tuple(sorted(trail))
                    found.add(cycle)
                elif target not in trail:
                    visit(start, target, trail + [target])

        for node in adjacency:
            visit(node, node, [node])
        return [list(cycle) for cycle in sorted(found)]

    def health_score(self, repository_id: str, repository_path: Path) -> HealthScore:
        root = self._root(repository_path)
        files = self._files(root)
        names = {file.name.lower() for file in files}
        source_count = sum(
            file.suffix in {".py", ".js", ".ts", ".tsx", ".java", ".rs"}
            for file in files
        )
        test_count = sum("test" in file.name.lower() for file in files)
        subscores = {
            "architecture": (
                70 if (root / "app").exists() or (root / "src").exists() else 45
            ),
            "testing": min(100, test_count / max(source_count, 1) * 200),
            "security": 40 if any(name in names for name in {".env", "id_rsa"}) else 85,
            "maintainability": 80 if source_count else 25,
            "documentation": (
                85 if {"readme.md", "contributing.md"}.intersection(names) else 35
            ),
            "scalability": (
                70
                if any(
                    (root / name).exists()
                    for name in ("dockerfile", "pyproject.toml", "package.json")
                )
                else 45
            ),
        }
        overall = round(statistics.mean(subscores.values()), 2)
        suggestions = [
            f"Improve {key}" for key, value in subscores.items() if value < 60
        ]
        return HealthScore(
            repository_id=repository_id,
            overall=overall,
            subscores=subscores,
            suggestions=suggestions,
            historical_key=f"health:{repository_id}",
        )

    def environment(self, repository_path: Path) -> EnvironmentSpec:
        root = self._root(repository_path)
        files = self._files(root)
        names = [file.relative_to(root).as_posix() for file in files]
        languages = sorted(
            {
                (
                    "Python"
                    if file.suffix == ".py"
                    else (
                        "Node"
                        if file.suffix in {".js", ".ts", ".tsx"}
                        else (
                            "Rust"
                            if file.suffix == ".rs"
                            else "Java" if file.suffix == ".java" else ""
                        )
                    )
                )
                for file in files
            }
            - {""}
        )
        managers = []
        for marker, manager in (
            ("requirements.txt", "pip"),
            ("pyproject.toml", "poetry/uv"),
            ("package-lock.json", "npm"),
            ("yarn.lock", "yarn"),
            ("Dockerfile", "docker"),
            ("environment.yml", "conda"),
        ):
            if (root / marker).exists():
                managers.append(manager)
        return EnvironmentSpec(
            languages=languages,
            package_managers=managers,
            files=names,
            compatibility_notes=[],
        )

    def timeline(self, repository_id: str, repository_path: Path) -> Timeline:
        root = self._root(repository_path)
        events = [
            TimelineEvent(
                event_type="analysis",
                timestamp=datetime.now(timezone.utc),
                source="repository",
                details={"files": len(self._files(root))},
            )
        ]
        return Timeline(repository_id=repository_id, events=events)

    def dataset_report(self, dataset_path: Path) -> DatasetQualityReport:
        if dataset_path.suffix.lower() != ".csv":
            raise UnsupportedDatasetError(
                "CSV inspection is currently enabled; add a parser adapter for this format"
            )
        import csv

        with dataset_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        columns = list(rows[0]) if rows else []
        missing = {
            column: sum(not row.get(column, "").strip() for row in rows)
            for column in columns
        }
        duplicates = len(rows) - len({tuple(sorted(row.items())) for row in rows})
        quality = max(
            0,
            100
            - sum(missing.values()) / max(len(rows) * max(len(columns), 1), 1) * 100
            - duplicates / max(len(rows), 1) * 100,
        )
        return DatasetQualityReport(
            name=dataset_path.name,
            format="csv",
            rows=len(rows),
            columns=len(columns),
            missing_values=missing,
            duplicate_rows=duplicates,
            quality_score=round(quality, 2),
            warnings=[],
        )
