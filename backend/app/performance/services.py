from __future__ import annotations

import asyncio
import os
import shutil
import time
from collections.abc import Awaitable, Callable, Iterable
from typing import Any, TypeVar
from uuid import uuid4

from app.observability.metrics.service import observability_metrics
from app.observability.health.service import observability_health

from .cache import cache_manager
from .models import (
    BenchmarkResult,
    CacheStatistics,
    LatencySummary,
    PerformanceOverview,
    QueueStatus,
    ResourceSnapshot,
)
from .tasks import PriorityTaskQueue, WorkerManager

T = TypeVar("T")


class PerformanceOptimizer:
    async def batch(
        self,
        items: Iterable[T],
        operation: Callable[[T], Awaitable[Any]],
        batch_size: int = 25,
    ) -> list[Any]:
        values = list(items)
        results: list[Any] = []
        for index in range(0, len(values), batch_size):
            results.extend(
                await asyncio.gather(
                    *(operation(item) for item in values[index : index + batch_size])
                )
            )
        return results

    async def incremental(
        self,
        items: Iterable[T],
        operation: Callable[[T], Awaitable[Any]],
        changed: set[str] | None = None,
    ) -> list[Any]:
        selected = [item for item in items if changed is None or str(item) in changed]
        return await self.batch(selected, operation)

    def allocate(self, workload: int, available_workers: int) -> int:
        return max(1, min(max(1, workload), max(1, available_workers)))


class ResourceMonitor:
    def snapshot(
        self,
        queue_size: int = 0,
        cache_entries: int = 0,
        active_agents: int = 0,
        running_workflows: int = 0,
    ) -> ResourceSnapshot:
        memory = observability_metrics.dashboard()
        return ResourceSnapshot(
            cpu_seconds=memory.cpu_seconds,
            memory_bytes=memory.memory_bytes,
            disk_bytes=shutil.disk_usage(os.getcwd()).used,
            active_agents=active_agents,
            running_workflows=running_workflows,
            queue_size=queue_size,
            cache_entries=cache_entries,
            provider_latency_seconds=(
                sum(memory.provider_latency_seconds)
                / len(memory.provider_latency_seconds)
                if memory.provider_latency_seconds
                else 0
            ),
        )


class BenchmarkEngine:
    def __init__(self) -> None:
        self._history: list[BenchmarkResult] = []

    async def run(
        self,
        category: str,
        operation: Callable[[], Awaitable[Any]] | None = None,
        iterations: int = 1,
    ) -> BenchmarkResult:
        iterations = max(1, min(iterations, 1000))
        operation = operation or (lambda: asyncio.sleep(0))
        started = time.perf_counter()
        for _ in range(iterations):
            await operation()
        elapsed = time.perf_counter() - started
        result = BenchmarkResult(
            benchmark_id=f"bench-{uuid4().hex[:12]}",
            category=category,
            operation=category,
            iterations=iterations,
            total_seconds=elapsed,
            average_seconds=elapsed / iterations,
            throughput_per_second=iterations / elapsed if elapsed else 0,
        )
        self._history.append(result)
        return result

    def history(self) -> list[BenchmarkResult]:
        return list(reversed(self._history))


class PerformanceService:
    def __init__(
        self,
        queue: PriorityTaskQueue | None = None,
        workers: WorkerManager | None = None,
        benchmarks: BenchmarkEngine | None = None,
    ) -> None:
        self.queue = queue or PriorityTaskQueue()
        self.workers = workers or WorkerManager(self.queue)
        self.benchmarks = benchmarks or BenchmarkEngine()
        self.monitor = ResourceMonitor()
        self.optimizer = PerformanceOptimizer()

    def overview(self) -> PerformanceOverview:
        cache: CacheStatistics = cache_manager.cache.statistics()
        queue: QueueStatus = self.queue.status().model_copy(
            update={"workers": self.workers.count}
        )
        resources = self.monitor.snapshot(
            queue_size=queue.queued, cache_entries=cache.entries
        )
        metrics = observability_metrics.dashboard()
        latency = LatencySummary(
            request_seconds=metrics.api_latency_seconds,
            ai_provider_seconds=sum(metrics.provider_latency_seconds),
            rag_seconds=0,
            repository_seconds=metrics.repository_scan_seconds,
            queue_seconds=metrics.queue_processing_seconds,
            throughput_per_second=metrics.http_requests
            / max(metrics.api_latency_seconds, 1),
            bottlenecks=[
                "cache_miss_ratio" if cache.hit_ratio < 0.5 and cache.misses else "none"
            ],
        )
        return PerformanceOverview(
            cache=cache,
            queue=queue,
            resources=resources,
            latency=latency,
            benchmarks=self.benchmarks.history(),
        )


performance_service = PerformanceService()
