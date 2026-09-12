from __future__ import annotations

import asyncio
import heapq
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from uuid import uuid4

from .models import JobStatus, QueueStatus, TaskRecord

TaskHandler = Callable[[dict[str, object], Callable[[float], None]], Awaitable[object]]


@dataclass(order=True)
class _QueuedTask:
    priority: int
    sequence: int
    task_id: str = field(compare=False)
    name: str = field(compare=False)
    payload: dict[str, object] = field(compare=False)
    not_before: float = field(compare=False, default=0)


class PriorityTaskQueue:
    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max_size
        self._items: list[_QueuedTask] = []
        self._records: dict[str, TaskRecord] = {}
        self._handlers: dict[str, TaskHandler] = {}
        self._condition = asyncio.Condition()
        self._sequence = 0
        self._running = 0
        self._completed = 0
        self._failed = 0
        self._cancelled = 0

    def register(self, name: str, handler: TaskHandler) -> None:
        self._handlers[name] = handler

    async def submit(
        self,
        name: str,
        payload: dict[str, object],
        *,
        priority: int = 100,
        delay_seconds: float = 0,
        max_attempts: int = 1,
    ) -> str:
        if name not in self._handlers:
            raise KeyError(f"No task handler registered: {name}")
        if len(self._items) >= self.max_size:
            raise RuntimeError("Task queue is full")
        task_id = f"task-{uuid4().hex[:12]}"
        self._sequence += 1
        record = TaskRecord(task_id=task_id, name=name, priority=priority)
        record.__pydantic_extra__ = {"max_attempts": max_attempts}  # type: ignore[attr-defined]
        self._records[task_id] = record
        async with self._condition:
            heapq.heappush(
                self._items,
                _QueuedTask(
                    priority,
                    self._sequence,
                    task_id,
                    name,
                    payload,
                    time.monotonic() + delay_seconds,
                ),
            )
            self._condition.notify()
        return task_id

    async def next(self) -> _QueuedTask:
        async with self._condition:
            while True:
                while not self._items:
                    await self._condition.wait()
                item = self._items[0]
                wait = item.not_before - time.monotonic()
                if wait > 0:
                    await asyncio.sleep(wait)
                    continue
                return heapq.heappop(self._items)

    async def run_worker(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                item = await asyncio.wait_for(self.next(), timeout=0.25)
            except asyncio.TimeoutError:
                continue
            if self._records[item.task_id].status == JobStatus.CANCELLED:
                self._cancelled += 1
                continue
            record = self._records[item.task_id].model_copy(
                update={
                    "status": JobStatus.RUNNING,
                    "attempts": self._records[item.task_id].attempts + 1,
                }
            )
            self._records[item.task_id] = record
            self._running += 1
            try:
                await self._handlers[item.name](
                    item.payload,
                    lambda progress: self._set_progress(item.task_id, progress),
                )
                self._records[item.task_id] = record.model_copy(
                    update={"status": JobStatus.COMPLETED, "progress": 1}
                )
                self._completed += 1
            except asyncio.CancelledError:
                self._records[item.task_id] = record.model_copy(
                    update={"status": JobStatus.CANCELLED}
                )
                self._cancelled += 1
            except Exception as exc:
                self._records[item.task_id] = record.model_copy(
                    update={"status": JobStatus.FAILED, "error": str(exc)}
                )
                self._failed += 1
            finally:
                self._running -= 1

    def _set_progress(self, task_id: str, progress: float) -> None:
        record = self._records[task_id]
        self._records[task_id] = record.model_copy(
            update={"progress": max(0, min(1, progress))}
        )

    def cancel(self, task_id: str) -> bool:
        record = self._records.get(task_id)
        if record is None or record.status in {
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        }:
            return False
        self._records[task_id] = record.model_copy(
            update={"status": JobStatus.CANCELLED}
        )
        return True

    def record(self, task_id: str) -> TaskRecord | None:
        return self._records.get(task_id)

    def records(self) -> list[TaskRecord]:
        return list(self._records.values())

    def status(self) -> QueueStatus:
        queued = sum(
            record.status == JobStatus.QUEUED for record in self._records.values()
        )
        return QueueStatus(
            queued=queued,
            running=self._running,
            completed=self._completed,
            failed=self._failed,
            cancelled=self._cancelled,
            delayed=sum(item.not_before > time.monotonic() for item in self._items),
        )


class WorkerManager:
    def __init__(self, queue: PriorityTaskQueue | None = None) -> None:
        self.queue = queue or PriorityTaskQueue()
        self._stop = asyncio.Event()
        self._workers: list[asyncio.Task[None]] = []

    async def start(self, count: int = 1) -> None:
        if count < 1:
            raise ValueError("worker count must be positive")
        self._stop.clear()
        self._workers = [
            asyncio.create_task(self.queue.run_worker(self._stop)) for _ in range(count)
        ]

    async def stop(self) -> None:
        self._stop.set()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    @property
    def count(self) -> int:
        return len(self._workers)
