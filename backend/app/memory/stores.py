from __future__ import annotations

from threading import RLock

from .models import GraphEdge, GraphNode, MemoryRecord


class InMemoryMemoryStore:
    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._lock = RLock()

    def append(self, record: MemoryRecord) -> None:
        with self._lock:
            self._records[record.id] = record

    def list(
        self, namespace: str | None = None, subject_id: str | None = None
    ) -> list[MemoryRecord]:
        with self._lock:
            records = list(self._records.values())
        if namespace is not None:
            records = [
                record for record in records if record.namespace.value == namespace
            ]
        if subject_id is not None:
            records = [record for record in records if record.subject_id == subject_id]
        return sorted(records, key=lambda record: record.created_at, reverse=True)

    def get(self, record_id: str) -> MemoryRecord | None:
        with self._lock:
            return self._records.get(record_id)


class InMemoryKnowledgeGraphStore:
    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[tuple[str, str, str], GraphEdge] = {}
        self._lock = RLock()

    def upsert_node(self, node: GraphNode) -> None:
        with self._lock:
            self._nodes[node.id] = node

    def upsert_edge(self, edge: GraphEdge) -> None:
        with self._lock:
            self._edges[(edge.source, edge.target, edge.relation)] = edge

    def graph(
        self, subject_id: str | None = None
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        with self._lock:
            nodes = list(self._nodes.values())
            edges = list(self._edges.values())
        if subject_id is not None:
            connected = (
                {subject_id}
                | {edge.target for edge in edges if edge.source == subject_id}
                | {edge.source for edge in edges if edge.target == subject_id}
            )
            nodes = [node for node in nodes if node.id in connected]
            edges = [
                edge
                for edge in edges
                if edge.source in connected and edge.target in connected
            ]
        return nodes, edges
