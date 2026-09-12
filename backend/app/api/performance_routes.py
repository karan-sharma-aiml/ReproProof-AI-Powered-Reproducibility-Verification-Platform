from __future__ import annotations

from fastapi import APIRouter, Query

from app.performance import cache_manager, performance_service
from app.performance.models import (
    BenchmarkResult,
    CacheStatistics,
    LatencySummary,
    PerformanceOverview,
    QueueStatus,
    ResourceSnapshot,
    TaskRecord,
)

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/cache", response_model=CacheStatistics)
def cache() -> CacheStatistics:
    return cache_manager.cache.statistics()


@router.get("/cache/statistics", response_model=CacheStatistics)
def cache_statistics() -> CacheStatistics:
    return cache_manager.cache.statistics()


@router.post("/cache/clear")
async def clear_cache() -> dict[str, object]:
    await cache_manager.cache.clear()
    return {"cleared": True}


@router.get("/metrics", response_model=PerformanceOverview)
def metrics() -> PerformanceOverview:
    return performance_service.overview()


@router.get("/resources", response_model=ResourceSnapshot)
def resources() -> ResourceSnapshot:
    overview = performance_service.overview()
    return overview.resources


@router.get("/queues", response_model=QueueStatus)
def queues() -> QueueStatus:
    return performance_service.overview().queue


@router.get("/latency", response_model=LatencySummary)
def latency() -> LatencySummary:
    return performance_service.overview().latency


@router.get("/benchmark", response_model=list[BenchmarkResult])
def benchmark_history() -> list[BenchmarkResult]:
    return performance_service.benchmarks.history()


@router.post("/benchmark/run", response_model=BenchmarkResult)
async def run_benchmark(
    category: str = Query("platform", min_length=1),
    iterations: int = Query(1, ge=1, le=1000),
) -> BenchmarkResult:
    return await performance_service.benchmarks.run(category, iterations=iterations)


@router.get("/workers")
def workers() -> dict[str, object]:
    return {
        "active_workers": performance_service.workers.count,
        "queue": performance_service.queue.status().model_dump(),
    }


@router.get("/tasks", response_model=list[TaskRecord])
def tasks() -> list[TaskRecord]:
    return performance_service.queue.records()
