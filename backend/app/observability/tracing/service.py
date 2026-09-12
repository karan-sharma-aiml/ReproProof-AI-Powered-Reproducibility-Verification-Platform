from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4
from collections import deque
from threading import Lock

from ..models import TraceRecord


@dataclass(frozen=True)
class TraceContext:
    trace_id: str = field(default_factory=lambda: uuid4().hex)
    correlation_id: str = field(default_factory=lambda: uuid4().hex)
    parent_span_id: str | None = None


@dataclass
class Span:
    name: str
    context: TraceContext
    span_id: str = field(default_factory=lambda: uuid4().hex)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    attributes: dict[str, object] = field(default_factory=dict)
    status: str = "ok"

    def finish(self) -> None:
        self.ended_at = datetime.now(timezone.utc)


_current: ContextVar[TraceContext | None] = ContextVar(
    "observability_trace_context", default=None
)


class Tracer:
    """Provider-neutral trace context and nested span foundation."""

    def __init__(self, max_records: int = 1000) -> None:
        self._records: deque[TraceRecord] = deque(maxlen=max_records)
        self._lock = Lock()

    def start(self, name: str, attributes: dict[str, object] | None = None) -> Span:
        current = _current.get()
        context = current or TraceContext()
        span = Span(name=name, context=context, attributes=attributes or {})
        _current.set(
            TraceContext(context.trace_id, context.correlation_id, span.span_id)
        )
        return span

    def finish(self, span: Span) -> None:
        span.finish()
        ended_at = span.ended_at or datetime.now(timezone.utc)
        record = TraceRecord(
            trace_id=span.context.trace_id,
            span_id=span.span_id,
            name=span.name,
            duration_ms=(ended_at - span.started_at).total_seconds() * 1000,
            status=span.status,
            started_at=span.started_at,
            ended_at=ended_at,
            metadata=dict(span.attributes),
        )
        with self._lock:
            self._records.append(record)
        _current.set(span.context)

    def context(self) -> TraceContext:
        return _current.get() or TraceContext()

    def recent(self, limit: int = 100) -> list[TraceRecord]:
        with self._lock:
            return list(self._records)[-max(1, min(limit, 1000)) :]


tracer = Tracer()
