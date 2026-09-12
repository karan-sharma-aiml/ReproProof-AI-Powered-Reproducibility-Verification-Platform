from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.api.provider_routes import provider_health
from app.core.config import Settings
from app.integrations.composition import ai_gateway, provider_manager
from app.main import app
from app.providers.contracts import ChatRequest, ProviderKind
from app.providers.gemini import GeminiLLMProvider


def test_gemini_settings_and_payload() -> None:
    settings = Settings(
        GEMINI_API_KEY="key",
        GEMINI_MODEL="gemini-2.5-flash",
        GEMINI_TEMPERATURE=0.2,
        GEMINI_MAX_TOKENS=8192,
    )
    assert settings.GEMINI_MODEL == "gemini-2.5-flash"
    provider = GeminiLLMProvider(api_key="key", model=settings.GEMINI_MODEL)
    payload = provider._payload(
        ChatRequest(messages=[{"role": "user", "content": "hello"}])
    )
    assert payload["generationConfig"]["temperature"] == 0.2
    assert payload["generationConfig"]["maxOutputTokens"] == 8192


def test_configured_gemini_is_highest_priority() -> None:
    descriptor = next(
        item
        for item in provider_manager.discover(ProviderKind.LLM)
        if item.name == "gemini"
    )
    assert descriptor.priority < 20
    assert descriptor.default_provider is True


def test_gateway_uses_local_mock_without_credentials() -> None:
    response = asyncio.run(
        ai_gateway.chat(ChatRequest(messages=[{"role": "user", "content": "ping"}]))
    )
    assert response.provider == "local-mock"
    assert response.metadata["fallback_used"] is True


def test_provider_test_endpoint_returns_compatibility_fields() -> None:
    response = TestClient(app).post("/providers/test", params={"prompt": "ping"})
    assert response.status_code == 200
    payload = response.json()
    assert {
        "provider",
        "model",
        "tokens",
        "latency",
        "status",
        "fallback_used",
    } <= payload.keys()


def test_provider_health_exposes_gemini_diagnostics() -> None:
    health = asyncio.run(provider_health())
    gemini = next(item for item in health if item["provider"] == "gemini")
    assert {
        "provider_name",
        "configured",
        "healthy",
        "model",
        "latency_ms",
        "last_error",
        "api_reachable",
    } <= gemini.keys()
