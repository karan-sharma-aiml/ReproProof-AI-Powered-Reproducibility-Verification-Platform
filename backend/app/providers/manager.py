from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Any

from .contracts import (
    ChatRequest,
    EmbeddingProvider,
    LLMProvider,
    OCRProvider,
    ProviderCapability,
    ProviderHealth,
    ProviderKind,
    VectorProvider,
)


@dataclass(frozen=True)
class ProviderDescriptor:
    name: str
    kind: ProviderKind
    capabilities: frozenset[ProviderCapability]
    priority: int = 100
    cost_per_1k_tokens: float = 0.0
    configured: bool = False
    default_provider: bool = False
    default_model: str | None = None


class AIProviderManager:
    """Registry and routing policy; SDK concerns remain inside adapters."""

    def __init__(self, default_provider: str | None = None) -> None:
        self._providers: dict[tuple[ProviderKind, str], object] = {}
        self.default_provider = default_provider or "gemini"

    def register(self, provider: object, kind: ProviderKind) -> None:
        name = getattr(provider, "name")
        self._providers[(kind, name)] = provider

    def discover(self, kind: ProviderKind | None = None) -> list[ProviderDescriptor]:
        descriptors: list[ProviderDescriptor] = []
        for (registered_kind, name), provider in self._providers.items():
            if kind is not None and registered_kind != kind:
                continue
            descriptors.append(
                ProviderDescriptor(
                    name=name,
                    kind=registered_kind,
                    capabilities=getattr(provider, "capabilities", frozenset()),
                    priority=getattr(provider, "priority", 100),
                    cost_per_1k_tokens=getattr(provider, "cost_per_1k_tokens", 0.0),
                    configured=bool(getattr(provider, "configured", False)),
                    default_provider=registered_kind == ProviderKind.LLM
                    and name == self.default_provider,
                    default_model=getattr(provider, "default_model", None),
                )
            )
        return sorted(
            descriptors,
            key=lambda item: (item.priority, item.cost_per_1k_tokens, item.name),
        )

    def get(self, kind: ProviderKind, name: str) -> object | None:
        return self._providers.get((kind, name))

    def select(
        self, kind: ProviderKind, required: set[ProviderCapability] | None = None
    ) -> object | None:
        required = required or set()
        candidates = [
            provider
            for (provider_kind, _), provider in self._providers.items()
            if provider_kind == kind
            and getattr(provider, "configured", True)
            and required <= set(getattr(provider, "capabilities", frozenset()))
        ]
        return min(
            candidates,
            key=lambda item: (
                0 if getattr(item, "name", "") == self.default_provider else 1,
                getattr(item, "priority", 100),
                getattr(item, "cost_per_1k_tokens", 0.0),
            ),
            default=None,
        )

    async def health(self) -> list[ProviderHealth]:
        result: list[ProviderHealth] = []
        for (kind, _), provider in self._providers.items():
            health_method = getattr(provider, "health", None)
            if health_method is None:
                health = ProviderHealth(
                    provider=getattr(provider, "name", "unknown"),
                    healthy=True,
                    configured=bool(getattr(provider, "configured", False)),
                    reason="health_check_not_implemented",
                )
            else:
                health = await health_method()
            result.append(
                replace(
                    health,
                    default_provider=kind == ProviderKind.LLM
                    and health.provider == self.default_provider,
                )
            )
        return result

    def startup_status(self) -> dict[str, object]:
        provider = self.get(ProviderKind.LLM, self.default_provider)
        return {
            "default_provider": self.default_provider,
            "configured": bool(getattr(provider, "configured", False)),
        }

    def capabilities(self, kind: ProviderKind | None = None) -> dict[str, list[str]]:
        return {
            item.name: [capability.value for capability in item.capabilities]
            for item in self.discover(kind)
        }
