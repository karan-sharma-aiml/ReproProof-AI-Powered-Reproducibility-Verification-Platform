from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class ProfileSample:
    name: str
    duration_seconds: float
    cpu_seconds: float


class Profiler:
    @contextmanager
    def measure(self, name: str) -> Iterator[list[ProfileSample]]:
        started = time.perf_counter()
        cpu_started = time.process_time()
        result: list[ProfileSample] = []
        try:
            yield result
        finally:
            result.append(
                ProfileSample(
                    name,
                    time.perf_counter() - started,
                    time.process_time() - cpu_started,
                )
            )
