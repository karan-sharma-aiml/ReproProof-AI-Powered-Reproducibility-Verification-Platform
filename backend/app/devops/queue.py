from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from uuid import uuid4

TaskHandler = Callable[[dict[str, object]], Awaitable[object]]


class BackgroundQueue:
    """Small async queue with explicit worker lifecycle for local deployments."""

    def __init__(self, max_size: int = 128) -> None:
        self._queue: asyncio.Queue[tuple[str, str, dict[str, object]]] = asyncio.Queue(
            maxsize=max_size
        )
        self._handlers: dict[str, TaskHandler] = {}
        self._workers: list[asyncio.Task[None]] = []

    def register(self, task_name: str, handler: TaskHandler) -> None:
        self._handlers[task_name] = handler

    async def enqueue(self, task_name: str, payload: dict[str, object]) -> str:
        if task_name not in self._handlers:
            raise KeyError(f"No background task registered: {task_name}")
        task_id = uuid4().hex
        await self._queue.put((task_id, task_name, payload))
        return task_id

    async def start(self, workers: int = 1) -> None:
        if workers < 1:
            raise ValueError("workers must be positive")
        self._workers.extend(
            asyncio.create_task(self._worker()) for _ in range(workers)
        )

    async def stop(self) -> None:
        for worker in self._workers:
            worker.cancel()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def _worker(self) -> None:
        while True:
            _, task_name, payload = await self._queue.get()
            try:
                await self._handlers[task_name](payload)
            finally:
                self._queue.task_done()
