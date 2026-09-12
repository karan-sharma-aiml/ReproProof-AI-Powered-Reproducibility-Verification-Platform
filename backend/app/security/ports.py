from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from .models import APIKeyPrincipal, Principal, TokenPair


class OAuth2Provider(ABC):
    @abstractmethod
    async def authenticate(
        self, authorization_code: str, redirect_uri: str
    ) -> Principal: ...


class ServiceAuthenticator(ABC):
    @abstractmethod
    async def authenticate_service(self, credential: str) -> Principal: ...


class APIKeyStore(Protocol):
    def resolve(self, api_key: str) -> APIKeyPrincipal | None: ...


class TokenProvider(ABC):
    @abstractmethod
    def issue(
        self, subject: str, claims: dict[str, Any] | None = None
    ) -> TokenPair: ...

    @abstractmethod
    def verify(self, token: str, *, token_type: str = "access") -> Principal: ...
