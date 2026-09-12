from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import AsyncIterator
from typing import Any

from app.core.config import get_settings

from .contracts import (
    ChatRequest,
    ChatResponse,
    LLMProvider,
    ProviderCapability,
    ProviderHealth,
    Usage,
)


class GeminiLLMProvider(LLMProvider):
    """Google Gemini REST adapter with no mandatory SDK dependency."""

    name = "gemini"
    priority = 10
    capabilities = frozenset(
        {
            ProviderCapability.CHAT,
            ProviderCapability.STREAMING,
            ProviderCapability.STRUCTURED_OUTPUT,
            ProviderCapability.TOOL_CALLING,
            ProviderCapability.VISION,
        }
    )

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.default_model = model or settings.GEMINI_MODEL or settings.DEFAULT_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT
        self.max_retries = (
            max_retries if max_retries is not None else settings.LLM_MAX_RETRIES
        )
        self.configured = bool(self.api_key.strip())
        self._models: tuple[str, ...] = ()
        self.last_error = ""

    def _url(self, model: str, method: str = "generateContent") -> str:
        query = urllib.parse.urlencode({"key": self.api_key})
        return f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:{method}?{query}"

    @staticmethod
    def _contents(messages: Any) -> list[dict[str, Any]]:
        contents = []
        for message in messages:
            role = "model" if message.get("role") == "assistant" else "user"
            content = message.get("content", "")
            parts = [{"text": content}] if isinstance(content, str) else content
            contents.append({"role": role, "parts": parts})
        return contents

    def _payload(self, request: ChatRequest) -> dict[str, Any]:
        settings = get_settings()
        temperature = (
            request.temperature
            if request.temperature != 0.0
            else settings.GEMINI_TEMPERATURE
        )
        payload: dict[str, Any] = {
            "contents": self._contents(request.messages),
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": request.max_tokens or settings.GEMINI_MAX_TOKENS,
            },
        }
        if request.response_format == "json":
            payload["generationConfig"]["responseMimeType"] = "application/json"
        if request.tools:
            payload["tools"] = [{"function_declarations": list(request.tools)}]
        return payload

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if not self.configured:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        model = request.model or self.default_model
        payload = self._payload(request)
        last_error: Exception | None = None
        for attempt in range(max(1, self.max_retries + 1)):
            started = time.perf_counter()
            try:
                timeout = (
                    request.timeout_seconds
                    if request.timeout_seconds != 30
                    else self.timeout
                )
                body = await asyncio.wait_for(
                    asyncio.to_thread(self._request, model, payload, timeout),
                    timeout=timeout,
                )
                self.last_error = ""
                return self._response(
                    model, body, (time.perf_counter() - started) * 1000
                )
            except Exception as exc:
                last_error = exc
                self.last_error = str(exc)
                if attempt < self.max_retries:
                    await asyncio.sleep(min(2.0, 0.1 * (2**attempt)))
        raise last_error or RuntimeError("Gemini request failed")

    async def stream(self, request: ChatRequest) -> AsyncIterator[str]:
        if not self.configured:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        model = request.model or self.default_model
        body = await asyncio.to_thread(
            self._request,
            model,
            self._payload(request),
            request.timeout_seconds,
            "streamGenerateContent",
        )
        for item in self._stream_items(body):
            text = self._text(item)
            if text:
                yield text

    def _request(
        self,
        model: str,
        payload: dict[str, Any],
        timeout: float,
        method: str = "generateContent",
    ) -> dict[str, Any] | list[dict[str, Any]]:
        request = urllib.request.Request(
            self._url(model, method),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
        if method == "streamGenerateContent":
            return [
                json.loads(line.removeprefix("data: ").strip())
                for line in raw.splitlines()
                if line.strip() and not line.startswith(":")
            ]
        return json.loads(raw)

    def _response(
        self, model: str, body: dict[str, Any], latency_ms: float
    ) -> ChatResponse:
        candidate = (body.get("candidates") or [{}])[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        text = "".join(part.get("text", "") for part in parts)
        tool_calls = [part["functionCall"] for part in parts if "functionCall" in part]
        usage = body.get("usageMetadata", {})
        prompt = int(usage.get("promptTokenCount", 0))
        completion = int(usage.get("candidatesTokenCount", 0))
        return ChatResponse(
            self.name,
            model,
            text,
            Usage(prompt, completion, prompt + completion),
            tool_calls=tool_calls,
            metadata={
                "latency_ms": latency_ms,
                "finish_reason": candidate.get("finishReason"),
            },
        )

    @staticmethod
    def _text(item: dict[str, Any]) -> str:
        content = (item.get("candidates") or [{}])[0].get("content", {})
        return "".join(part.get("text", "") for part in content.get("parts", []))

    @staticmethod
    def _stream_items(
        body: dict[str, Any] | list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return body if isinstance(body, list) else [body]

    async def health(self) -> ProviderHealth:
        if not self.configured:
            self.last_error = "GEMINI_API_KEY is not configured"
            return ProviderHealth(
                self.name,
                False,
                False,
                "GEMINI_API_KEY is not configured",
                default_provider=True,
                model=self.default_model,
                last_error=self.last_error,
            )
        started = time.perf_counter()
        try:
            models = await asyncio.to_thread(self._list_models)
            self._models = tuple(models)
            self.last_error = ""
            return ProviderHealth(
                self.name,
                True,
                True,
                "connected",
                (time.perf_counter() - started) * 1000,
                True,
                self._models,
                True,
                self.default_model,
                "",
                True,
            )
        except Exception as exc:
            self.last_error = str(exc)
            return ProviderHealth(
                self.name,
                False,
                True,
                f"connection_failed: {exc}",
                (time.perf_counter() - started) * 1000,
                False,
                self._models,
                True,
                self.default_model,
                self.last_error,
                False,
            )

    def _list_models(self) -> list[str]:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models?"
            + urllib.parse.urlencode({"key": self.api_key})
        )
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [
            item.get("name", "").removeprefix("models/")
            for item in payload.get("models", [])
            if "generateContent" in item.get("supportedGenerationMethods", [])
        ]
