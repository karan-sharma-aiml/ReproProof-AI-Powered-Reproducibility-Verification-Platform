from __future__ import annotations

from fastapi import APIRouter

from app.integrations.composition import ai_gateway, provider_manager
from app.providers.contracts import ChatRequest, ProviderKind

router = APIRouter(prefix="/providers", tags=["ai providers"])


@router.get("")
def providers(kind: ProviderKind | None = None) -> list[dict[str, object]]:
    return [descriptor.__dict__ for descriptor in provider_manager.discover(kind)]


@router.get("/health")
async def provider_health() -> list[dict[str, object]]:
    result = []
    for health in await provider_manager.health():
        payload = dict(health.__dict__)
        payload.update(
            provider_name=health.provider,
            model=health.model
            or (health.available_models[0] if health.available_models else ""),
            api_reachable=health.api_reachable or health.connected,
            last_error=health.last_error or ("" if health.healthy else health.reason),
        )
        result.append(payload)
    return result


@router.get("/status")
def provider_status() -> dict[str, object]:
    return ai_gateway.routing_status()


@router.get("/models")
def models() -> dict[str, list[str]]:
    return {
        kind.value: [item.name for item in provider_manager.discover(kind)]
        for kind in ProviderKind
    }


@router.get("/capabilities")
def capabilities() -> dict[str, list[str]]:
    return provider_manager.capabilities()


@router.post("/test")
async def test_provider(prompt: str = "health check") -> dict[str, object]:
    try:
        response = await ai_gateway.chat(
            ChatRequest(messages=[{"role": "user", "content": prompt}])
        )
        metadata = response.metadata
        return {
            "provider": response.provider,
            "model": response.model,
            "content": response.content,
            "tokens": response.usage.total_tokens,
            "latency": metadata.get("latency_ms", 0),
            "latency_ms": metadata.get("latency_ms", 0),
            "status": metadata.get("status", "success"),
            "fallback_used": bool(metadata.get("fallback_used", False)),
            "usage": response.usage.__dict__,
            "metadata": metadata,
        }
    except Exception as exc:
        return {
            "provider": "local-mock",
            "model": "mock-model",
            "content": "Provider test failed; local fallback is unavailable.",
            "tokens": 0,
            "latency": 0,
            "latency_ms": 0,
            "status": "failed",
            "fallback_used": True,
            "error": str(exc),
        }
