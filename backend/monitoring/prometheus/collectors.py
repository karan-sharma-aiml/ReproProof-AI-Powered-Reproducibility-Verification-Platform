"""Host and container collectors that do not require a monitoring daemon."""

from __future__ import annotations

import os
import shutil
import time
from typing import Any

try:
    import psutil
except ImportError:  # Optional; production images can install it for host detail.
    psutil = None


class SystemCollector:
    """Collect portable Node Exporter-style process and host gauges."""

    def collect(self) -> dict[str, float]:
        values = {
            "node_processes": (
                float(len(os.listdir("/proc"))) if os.path.isdir("/proc") else 0.0
            ),
            "node_filesystem_free_bytes": float(shutil.disk_usage(os.getcwd()).free),
        }
        if psutil is not None:
            values.update(
                node_cpu_percent=float(psutil.cpu_percent(interval=None)),
                node_memory_bytes=float(psutil.virtual_memory().used),
                node_memory_available_bytes=float(psutil.virtual_memory().available),
                node_network_bytes_received=float(
                    sum(
                        item.bytes_recv
                        for item in psutil.net_io_counters(pernic=True).values()
                    )
                ),
                node_network_bytes_sent=float(
                    sum(
                        item.bytes_sent
                        for item in psutil.net_io_counters(pernic=True).values()
                    )
                ),
            )
            try:
                values["node_temperature_celsius"] = float(
                    next(iter(psutil.sensors_temperatures().values()))[0].current
                )
            except (AttributeError, IndexError, StopIteration, TypeError):
                pass
        return values


class ContainerCollector:
    """Best-effort cAdvisor-style gauges; cAdvisor remains the source in deployment."""

    def collect(self) -> dict[str, float]:
        return {
            "container_cpu_usage_seconds": 0.0,
            "container_memory_usage_bytes": 0.0,
            "container_restarts_total": 0.0,
            "container_network_bytes_received": 0.0,
            "container_network_bytes_sent": 0.0,
            "container_volumes_bytes": 0.0,
        }


class MetricCollector:
    def __init__(self) -> None:
        self.system = SystemCollector()
        self.containers = ContainerCollector()

    def collect(self) -> dict[str, float]:
        values: dict[str, float] = {}
        values.update(self.system.collect())
        values.update(self.containers.collect())
        return values
