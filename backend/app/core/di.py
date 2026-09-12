from __future__ import annotations

from collections.abc import Callable
from typing import Any


class ServiceContainer:
    """Minimal dependency injection container for enterprise service wiring."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], Any]] = {}

    def register(self, name: str, factory: Callable[[], Any]) -> None:
        self._factories[name] = factory

    def resolve(self, name: str) -> Any:
        if name not in self._factories:
            raise KeyError(f"No service registered for '{name}'")
        return self._factories[name]()

    def get(self, name: str, default: Any | None = None) -> Any:
        return self._factories.get(name, lambda: default)()


container = ServiceContainer()
