from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncIterator

from app.core.config import get_settings
from app.research.ports import LLMProvider as ResearchLLMProvider

from app.providers.contracts import (
    ChatRequest,
    ChatResponse,
    LLMProvider,
    ProviderCapability,
    ProviderKind,
)
from app.providers.manager import AIProviderManager


class NamedLLMProvider(LLMProvider):
    def __init__(
        self,
        name: str,
        *,
        configured: bool = False,
        priority: int = 100,
        cost_per_1k_tokens: float = 0.0,
        capabilities: frozenset[ProviderCapability] | None = None,
    ) -> None:
        self.name = name
        self.configured = configured
        self.priority = priority
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.default_model = f"{name}-default"
        self.capabilities = capabilities or frozenset(
            {
                ProviderCapability.CHAT,
                ProviderCapability.STREAMING,
                ProviderCapability.STRUCTURED_OUTPUT,
                ProviderCapability.TOOL_CALLING,
            }
        )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        prompt = request.messages[-1].get("content", "") if request.messages else ""
        content = f"Provider adapter {self.name} is available through the gateway. Prompt: {prompt}"[
            :2000
        ]
        if request.response_format == "json":
            content = '{"provider":"' + self.name + '","status":"adapter_ready"}'
        return ChatResponse(
            self.name,
            request.model or f"{self.name}-default",
            content,
            metadata={"configured": self.configured},
        )

    async def health(self):
        from app.providers.contracts import ProviderHealth

        return ProviderHealth(
            self.name,
            True,
            self.configured,
            "configured" if self.configured else "credentials_not_configured",
            0,
            self.configured,
            (self.default_model,),
        )


class AIGateway(ResearchLLMProvider):
    """Unified gateway used by provider-aware application services."""

    name = "ai-gateway"

    def __init__(self, manager: AIProviderManager, fallback: LLMProvider) -> None:
        self.manager = manager
        self.fallback = fallback

    def _provider(self, request: ChatRequest) -> LLMProvider:
        return (
            self.manager.select(
                ProviderKind.LLM,
                set(request.tools and [ProviderCapability.TOOL_CALLING] or []),
            )
            or self.fallback
        )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        provider = self._provider(request)
        settings = get_settings()
        started = time.perf_counter()
        last_error = ""
        provider_is_fallback = getattr(provider, "name", "") == self.fallback.name
        timeout = (
            request.timeout_seconds
            if request.timeout_seconds != 30
            else settings.LLM_TIMEOUT
        )
        for attempt in range(max(1, settings.LLM_MAX_RETRIES + 1)):
            try:
                response = await asyncio.wait_for(
                    provider.chat(request), timeout=timeout
                )
                return ChatResponse(
                    response.provider,
                    response.model,
                    response.content,
                    response.usage,
                    response.tool_calls,
                    {
                        **response.metadata,
                        "fallback_used": provider_is_fallback,
                        "status": "fallback" if provider_is_fallback else "success",
                        "latency_ms": (time.perf_counter() - started) * 1000,
                    },
                )
            except Exception as exc:
                last_error = str(exc)
                if attempt == settings.LLM_MAX_RETRIES:
                    break
        fallback = await self.fallback.chat(request)
        return ChatResponse(
            fallback.provider,
            fallback.model,
            fallback.content,
            fallback.usage,
            fallback.tool_calls,
            {
                **fallback.metadata,
                "fallback_provider": fallback.provider,
                "requested_provider": getattr(provider, "name", "unknown"),
                "fallback_used": True,
                "status": "fallback",
                "last_error": last_error,
                "latency_ms": (time.perf_counter() - started) * 1000,
            },
        )

    async def complete(
        self, prompt: str, *, context: dict[str, Any] | None = None
    ) -> str:
        response = await self.chat(
            ChatRequest(
                messages=[{"role": "user", "content": prompt}], response_format=None
            )
        )
        return response.content

    async def stream(self, request: ChatRequest) -> AsyncIterator[str]:
        provider = self._provider(request)
        try:
            async for chunk in provider.stream(request):
                yield chunk
            return
        except Exception:
            response = await self.chat(request)
            for token in response.content.split():
                yield token + " "

    def routing_status(self) -> dict[str, object]:
        selected = self.manager.select(ProviderKind.LLM)
        return {
            "current_provider": getattr(selected, "name", self.fallback.name),
            "current_model": getattr(
                selected, "default_model", get_settings().DEFAULT_MODEL
            ),
            "fallback_provider": self.fallback.name,
            "default_provider": self.manager.default_provider,
        }
