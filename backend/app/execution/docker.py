from __future__ import annotations

from pathlib import Path

from .models import DockerSandboxSpec, ExecutionJob


class DockerSandboxBuilder:
    """Builds constrained Docker invocations; it never invokes Docker itself."""

    def __init__(self, image: str = "python:3.12-slim") -> None:
        self.image = image

    def build(self, job: ExecutionJob) -> DockerSandboxSpec:
        repository = Path(job.repository_path).resolve()
        args = [
            "--rm",
            "--cpus",
            str(job.limits.cpu_count),
            "--memory",
            str(job.limits.memory_bytes),
            "--pids-limit",
            str(job.limits.pids_limit),
            "--network",
            "bridge" if job.limits.network_enabled else "none",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--user",
            "65532:65532",
            "--workdir",
            "/workspace",
            "--volume",
            f"{repository}:/workspace:ro",
            self.image,
            *job.command,
        ]
        return DockerSandboxSpec(
            image=self.image,
            command=["docker", "run"],
            args=args,
            limits=job.limits,
            network_mode="bridge" if job.limits.network_enabled else "none",
        )
