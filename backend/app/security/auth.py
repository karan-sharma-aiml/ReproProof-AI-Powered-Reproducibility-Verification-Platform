from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import get_settings

from .models import APIKeyPrincipal, Permission, Principal, Role, TokenPair
from .ports import APIKeyStore, TokenProvider


class AuthenticationError(ValueError):
    pass


class JWTProvider(TokenProvider):
    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str | None = None,
        access_minutes: int | None = None,
        refresh_days: int | None = None,
    ) -> None:
        settings = get_settings()
        self.secret_key = secret_key or settings.JWT_SECRET_KEY
        self.algorithm = algorithm or settings.JWT_ALGORITHM
        self.access_minutes = access_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_days = refresh_days or settings.REFRESH_TOKEN_EXPIRE_DAYS
        self._revoked: set[str] = set()

    def _require_secret(self) -> None:
        if not self.secret_key:
            raise AuthenticationError("JWT_SECRET_KEY is not configured")
        if self.algorithm.startswith("HS") and len(self.secret_key.encode()) < 32:
            raise AuthenticationError(
                "JWT_SECRET_KEY must be at least 32 bytes for HMAC tokens"
            )

    def issue(self, subject: str, claims: dict[str, Any] | None = None) -> TokenPair:
        self._require_secret()
        now = datetime.now(timezone.utc)
        access = self._encode(
            subject, "access", now + timedelta(minutes=self.access_minutes), claims
        )
        refresh = self._encode(
            subject, "refresh", now + timedelta(days=self.refresh_days), claims
        )
        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=self.access_minutes * 60,
        )

    def _encode(
        self,
        subject: str,
        token_type: str,
        expires: datetime,
        claims: dict[str, Any] | None,
    ) -> str:
        payload = {
            "sub": subject,
            "type": token_type,
            "iat": datetime.now(timezone.utc),
            "exp": expires,
            "jti": secrets.token_urlsafe(16),
            **(claims or {}),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify(self, token: str, *, token_type: str = "access") -> Principal:
        self._require_secret()
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid or expired token") from exc
        if payload.get("type") != token_type or payload.get("jti") in self._revoked:
            raise AuthenticationError("Invalid token type or revoked token")
        return Principal(subject=str(payload["sub"]), auth_method="jwt", claims=payload)

    def revoke(self, token: str) -> None:
        payload = jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
            options={"verify_exp": False},
        )
        if payload.get("jti"):
            self._revoked.add(str(payload["jti"]))


class InMemoryAPIKeyStore:
    def __init__(self) -> None:
        self._keys: dict[str, tuple[str, APIKeyPrincipal]] = {}

    def add(self, api_key: str, principal: APIKeyPrincipal) -> None:
        digest = hashlib.sha256(api_key.encode()).hexdigest()
        self._keys[digest] = (principal.key_id, principal)

    def resolve(self, api_key: str) -> APIKeyPrincipal | None:
        digest = hashlib.sha256(api_key.encode()).hexdigest()
        entry = self._keys.get(digest)
        return entry[1] if entry else None


class AuthenticationService:
    def __init__(
        self,
        token_provider: TokenProvider | None = None,
        api_key_store: APIKeyStore | None = None,
    ) -> None:
        self.token_provider = token_provider or JWTProvider()
        self.api_key_store = api_key_store or InMemoryAPIKeyStore()

    def authenticate_bearer(self, token: str) -> Principal:
        return self.token_provider.verify(token)

    def authenticate_api_key(self, api_key: str) -> Principal:
        principal = self.api_key_store.resolve(api_key)
        if principal is None:
            raise AuthenticationError("Invalid API key")
        return Principal(
            subject=principal.subject,
            roles=principal.roles,
            permissions=principal.permissions,
            auth_method="api_key",
        )
