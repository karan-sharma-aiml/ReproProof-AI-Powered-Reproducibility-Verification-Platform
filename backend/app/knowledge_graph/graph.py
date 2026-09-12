from __future__ import annotations

import ast
import re
from collections import Counter, deque
from pathlib import Path

from app.memory.models import GraphEdge, GraphNode
from app.memory.stores import InMemoryKnowledgeGraphStore

from .models import (
    EntityType,
    GraphEntity,
    GraphRelationship,
    GraphSearchResult,
    GraphStatistics,
    KnowledgeGraph,
    NeighborResult,
    RelationshipType,
)


class KnowledgeGraphEngine:
    """Provider-neutral graph engine backed by the existing memory graph store."""

    def __init__(self, store: InMemoryKnowledgeGraphStore | None = None) -> None:
        self.store = store or InMemoryKnowledgeGraphStore()
        self._entities: dict[str, GraphEntity] = {}

    def upsert_entity(self, entity: GraphEntity) -> GraphEntity:
        self._entities[entity.id] = entity
        self.store.upsert_node(
            GraphNode(
                id=entity.id,
                label=entity.label,
                kind=entity.type.value,
                metadata=entity.properties,
            )
        )
        return entity

    def relate(self, relationship: GraphRelationship) -> GraphRelationship:
        if (
            relationship.source not in self._entities
            or relationship.target not in self._entities
        ):
            raise ValueError("Both relationship endpoints must exist")
        self.store.upsert_edge(
            GraphEdge(
                source=relationship.source,
                target=relationship.target,
                relation=relationship.type.value,
                weight=relationship.weight,
            )
        )
        return relationship

    def graph(self, entity_id: str | None = None) -> KnowledgeGraph:
        if entity_id is None:
            entities = list(self._entities.values())
            relationships = self._relationships()
        else:
            nodes, _ = self.store.graph(entity_id)
            ids = {node.id for node in nodes}
            entities = [
                entity for entity in self._entities.values() if entity.id in ids
            ]
            relationships = [
                item
                for item in self._relationships()
                if item.source in ids and item.target in ids
            ]
        return KnowledgeGraph(entities=entities, relationships=relationships)

    def search(
        self, query: str, *, entity_type: EntityType | None = None, limit: int = 20
    ) -> list[GraphSearchResult]:
        terms = self._terms(query)
        results: list[GraphSearchResult] = []
        for entity in self._entities.values():
            if entity_type and entity.type != entity_type:
                continue
            fields = {
                "label": entity.label,
                "type": entity.type.value,
                **{key: str(value) for key, value in entity.properties.items()},
            }
            matched = [
                name for name, value in fields.items() if terms & self._terms(value)
            ]
            if matched:
                score = min(
                    1.0,
                    (len(terms & self._terms(entity.label)) + len(matched))
                    / max(1, len(terms) + 1),
                )
                results.append(
                    GraphSearchResult(
                        entity=entity, score=score, matched_fields=matched
                    )
                )
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

    def neighbors(
        self, entity_id: str, *, depth: int = 1, limit: int = 50
    ) -> list[NeighborResult]:
        if entity_id not in self._entities:
            return []
        queue = deque([(entity_id, 0)])
        seen = {entity_id}
        result: list[NeighborResult] = []
        relationships = self._relationships()
        while queue and len(result) < limit:
            current, distance = queue.popleft()
            if distance >= depth:
                continue
            for relationship in relationships:
                if relationship.source == current:
                    neighbor, direction = relationship.target, "outgoing"
                elif relationship.target == current:
                    neighbor, direction = relationship.source, "incoming"
                else:
                    continue
                if neighbor not in self._entities:
                    continue
                result.append(
                    NeighborResult(
                        entity=self._entities[neighbor],
                        relationship=relationship,
                        direction=direction,
                        distance=distance + 1,
                    )
                )
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, distance + 1))
        return result[:limit]

    def statistics(self) -> GraphStatistics:
        relationships = self._relationships()
        by_type = Counter(entity.type.value for entity in self._entities.values())
        degrees = Counter(edge.source for edge in relationships)
        degrees.update(edge.target for edge in relationships)
        maximum = max(degrees.values(), default=1)
        return GraphStatistics(
            entities=len(self._entities),
            relationships=len(relationships),
            by_type=dict(by_type),
            centrality={
                entity_id: degrees.get(entity_id, 0) / maximum
                for entity_id in self._entities
            },
        )

    def _relationships(self) -> list[GraphRelationship]:
        _, edges = self.store.graph()
        relationships = []
        for edge in edges:
            try:
                relation = RelationshipType(edge.relation)
            except ValueError:
                continue
            relationships.append(
                GraphRelationship(
                    source=edge.source,
                    target=edge.target,
                    type=relation,
                    weight=edge.weight,
                )
            )
        return relationships

    @staticmethod
    def _terms(value: str) -> set[str]:
        return {
            term
            for term in re.findall(r"[a-zA-Z0-9_]{2,}", value.lower())
            if term not in {"the", "and", "for", "with", "from"}
        }


class GraphBuilder:
    def __init__(self, engine: KnowledgeGraphEngine | None = None) -> None:
        self.engine = engine or knowledge_graph

    def index_repository(self, repository_id: str, root: Path) -> KnowledgeGraph:
        repository = self.engine.upsert_entity(
            GraphEntity(
                id=f"repository:{repository_id}",
                type=EntityType.REPOSITORY,
                label=repository_id,
                properties={"path": str(root)},
            )
        )
        for path in sorted(root.rglob("*")):
            if not path.is_file() or any(
                part in {".git", ".next", "__pycache__", "node_modules"}
                for part in path.parts
            ):
                continue
            relative = path.relative_to(root).as_posix()
            file_id = f"file:{repository_id}:{relative}"
            file_entity = self.engine.upsert_entity(
                GraphEntity(
                    id=file_id,
                    type=EntityType.FILE,
                    label=path.name,
                    properties={"path": relative, "suffix": path.suffix.lower()},
                )
            )
            self.engine.relate(
                GraphRelationship(
                    source=repository.id, target=file_id, type=RelationshipType.CONTAINS
                )
            )
            if path.suffix == ".py":
                self._index_python(repository_id, file_entity, path)
        return self.engine.graph(repository.id)

    def _index_python(
        self, repository_id: str, file_entity: GraphEntity, path: Path
    ) -> None:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, SyntaxError):
            return
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = (
                    EntityType.CLASS
                    if isinstance(node, ast.ClassDef)
                    else EntityType.FUNCTION
                )
                entity = self.engine.upsert_entity(
                    GraphEntity(
                        id=f"{kind.value}:{repository_id}:{path.name}:{node.name}:{node.lineno}",
                        type=kind,
                        label=node.name,
                        properties={"file": file_entity.id, "line": node.lineno},
                    )
                )
                self.engine.relate(
                    GraphRelationship(
                        source=file_entity.id,
                        target=entity.id,
                        type=RelationshipType.CONTAINS,
                    )
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    dependency = self.engine.upsert_entity(
                        GraphEntity(
                            id=f"dependency:{alias.name}",
                            type=EntityType.DEPENDENCY,
                            label=alias.name,
                        )
                    )
                    self.engine.relate(
                        GraphRelationship(
                            source=file_entity.id,
                            target=dependency.id,
                            type=RelationshipType.IMPORTS,
                        )
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                dependency = self.engine.upsert_entity(
                    GraphEntity(
                        id=f"dependency:{node.module}",
                        type=EntityType.DEPENDENCY,
                        label=node.module,
                    )
                )
                self.engine.relate(
                    GraphRelationship(
                        source=file_entity.id,
                        target=dependency.id,
                        type=RelationshipType.IMPORTS,
                    )
                )


knowledge_graph = KnowledgeGraphEngine()
graph_builder = GraphBuilder(knowledge_graph)
