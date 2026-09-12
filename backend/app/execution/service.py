from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger

from .docker import DockerSandboxBuilder
from .models import (
    BenchmarkResult,
    ExecutionJob,
    ExecutionRecord,
    JobStatus,
    ReproducibilityResult,
)
from .ports import ExecutionCache, JobHistory, SandboxRuntime
from .repositories import InMemoryExecutionCache, InMemoryJobHistory

logger = get_logger("execution.enterprise")


class ExecutionQueue:
    """Bounded async queue for controlled job admission."""

    def __init__(self, max_size: int = 32) -> None:
        self._queue: asyncio.Queue[ExecutionJob] = asyncio.Queue(maxsize=max_size)

    async def submit(self, job: ExecutionJob) -> None:
        await self._queue.put(job)

    async def next(self) -> ExecutionJob:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()


class EnterpriseExecutionEngine:
    """Coordinates cache, queue, sandbox runtime, history, benchmarks, and verification."""

    def __init__(
        self,
        runtime: SandboxRuntime | None = None,
        cache: ExecutionCache | None = None,
        history: JobHistory | None = None,
        queue: ExecutionQueue | None = None,
    ) -> None:
        self.runtime = runtime
        self.cache = cache or InMemoryExecutionCache()
        self.history = history or InMemoryJobHistory()
        self.queue = queue or ExecutionQueue()
        self.docker_builder = DockerSandboxBuilder()

    def cache_key(self, job: ExecutionJob) -> str:
        payload = job.model_dump(mode="json", exclude={"job_id", "created_at"})
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    async def execute(self, job: ExecutionJob) -> ExecutionRecord:
        key = self.cache_key(job)
        cached = self.cache.get(key)
        if cached is not None:
            record = cached.model_copy(
                update={
                    "job_id": job.job_id,
                    "repository_id": job.repository_id,
                    "status": JobStatus.CACHED,
                    "queued_at": job.created_at,
                    "cache_key": key,
                }
            )
            self.history.append(record)
            return record
        if self.runtime is None:
            raise RuntimeError(
                "A SandboxRuntime is required; direct host execution is disabled"
            )
        record = await self.runtime.run(job)
        record = record.model_copy(update={"cache_key": key})
        self.cache.put(key, record)
        self.history.append(record)
        logger.info(
            "execution_recorded job_id=%s status=%s",
            job.job_id,
            record.status.value,
        )
        return record

    async def submit_and_execute(self, job: ExecutionJob) -> ExecutionRecord:
        """Admit one job through the bounded queue, then execute and acknowledge it."""
        await self.queue.submit(job)
        queued_job = await self.queue.next()
        try:
            return await self.execute(queued_job)
        finally:
            self.queue.task_done()

    async def run_parallel(self, jobs: list[ExecutionJob]) -> list[ExecutionRecord]:
        return list(await asyncio.gather(*(self.execute(job) for job in jobs)))

    async def benchmark(
        self, job: ExecutionJob, iterations: int = 3
    ) -> BenchmarkResult:
        if iterations < 1:
            raise ValueError("iterations must be positive")
        records = [
            await self.execute(
                job.model_copy(update={"job_id": f"{job.job_id}-{index}"})
            )
            for index in range(iterations)
        ]
        runtimes = [record.runtime_seconds for record in records]
        successful = sum(
            record.status in {JobStatus.COMPLETED, JobStatus.CACHED}
            for record in records
        )
        mean_runtime = sum(runtimes) / len(runtimes) if runtimes else 0
        return BenchmarkResult(
            repository_id=job.repository_id,
            iterations=iterations,
            successful_iterations=successful,
            runtimes_seconds=runtimes,
            mean_runtime_seconds=mean_runtime,
            min_runtime_seconds=min(runtimes, default=0),
            max_runtime_seconds=max(runtimes, default=0),
            history_key=f"benchmark:{job.repository_id}",
        )

    async def verify_reproducibility(
        self, job: ExecutionJob, runs: int = 2
    ) -> ReproducibilityResult:
        if runs < 1:
            raise ValueError("runs must be positive")
        records = [
            await self.execute(
                job.model_copy(update={"job_id": f"{job.job_id}-repro-{index}"})
            )
            for index in range(runs)
        ]
        digests = [
            hashlib.sha256(
                f"{record.stdout}\0{record.stderr}\0{record.exit_code}".encode()
            ).hexdigest()
            for record in records
        ]
        reproducible = len(set(digests)) == 1 and all(
            record.status in {JobStatus.COMPLETED, JobStatus.CACHED}
            for record in records
        )
        return ReproducibilityResult(
            repository_id=job.repository_id,
            reproducible=reproducible,
            runs=runs,
            output_digests=digests,
            differences=(
                [] if reproducible else ["Execution outputs differ or one run failed"]
            ),
            environment_hash=job.environment_hash,
        )
