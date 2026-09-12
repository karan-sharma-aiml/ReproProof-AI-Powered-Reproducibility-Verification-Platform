from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.05
    max_delay_seconds: float = 2.0
    jitter: float = 0.1

    def delay(self, attempt: int) -> float:
        base = min(
            self.max_delay_seconds, self.base_delay_seconds * (2 ** max(0, attempt - 1))
        )
        return max(0, base + random.uniform(-self.jitter, self.jitter) * base)


class CircuitBreaker:
    def __init__(
        self, failure_threshold: int = 3, recovery_seconds: float = 30
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.opened_at = 0.0

    def allow(self) -> bool:
        if (
            self.state == CircuitState.OPEN
            and time.monotonic() - self.opened_at >= self.recovery_seconds
        ):
            self.state = CircuitState.HALF_OPEN
        return self.state != CircuitState.OPEN

    def success(self) -> None:
        self.failures = 0
        self.state = CircuitState.CLOSED

    def failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.monotonic()


class Bulkhead:
    def __init__(self, limit: int = 16) -> None:
        self.semaphore = asyncio.Semaphore(limit)

    async def run(self, operation: Callable[[], Awaitable[T]]) -> T:
        async with self.semaphore:
            return await operation()


async def resilient_call(
    operation: Callable[[], Awaitable[T]],
    *,
    policy: RetryPolicy | None = None,
    breaker: CircuitBreaker | None = None,
    timeout_seconds: float = 30,
) -> T:
    policy = policy or RetryPolicy()
    breaker = breaker or CircuitBreaker()
    if not breaker.allow():
        raise RuntimeError("circuit breaker is open")
    last_error: Exception | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            result = await asyncio.wait_for(operation(), timeout=timeout_seconds)
            breaker.success()
            return result
        except Exception as exc:
            last_error = exc
            breaker.failure()
            if attempt < policy.max_attempts:
                await asyncio.sleep(policy.delay(attempt))
    raise last_error or RuntimeError("operation failed")
