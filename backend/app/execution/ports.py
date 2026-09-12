from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import ExecutionJob, ExecutionRecord


class SandboxRuntime(ABC):
    """Port for Docker, Firecracker, Kubernetes, or Cloud Run execution providers."""

    @abstractmethod
    async def run(self, job: ExecutionJob) -> ExecutionRecord: ...


class ExecutionCache(Protocol):
    def get(self, key: str) -> ExecutionRecord | None: ...
    def put(self, key: str, record: ExecutionRecord) -> None: ...


class JobHistory(Protocol):
    def append(self, record: ExecutionRecord) -> None: ...
    def get(self, job_id: str) -> ExecutionRecord | None: ...
    def list(self, repository_id: str | None = None) -> list[ExecutionRecord]: ...
