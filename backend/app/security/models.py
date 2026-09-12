from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Role(StrEnum):
    ADMIN = "Admin"
    RESEARCHER = "Researcher"
    REVIEWER = "Reviewer"
    JUDGE = "Judge"
    VIEWER = "Viewer"


class Permission(StrEnum):
    READ = "read"
    UPLOAD = "upload"
    EXECUTE = "execute"
    REVIEW = "review"
    JUDGE = "judge"
    EXPORT = "export"
    ADMIN = "admin"


class Principal(BaseModel):
    subject: str
    roles: list[Role] = Field(default_factory=list)
    permissions: list[Permission] = Field(default_factory=list)
    auth_method: str
    claims: dict[str, Any] = Field(default_factory=dict)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class APIKeyPrincipal(BaseModel):
    key_id: str
    subject: str
    roles: list[Role] = Field(default_factory=list)
    permissions: list[Permission] = Field(default_factory=list)


class AuditEvent(BaseModel):
    action: str
    actor: str
    request_id: str = ""
    timestamp: datetime
    success: bool = True
    details: dict[str, Any] = Field(default_factory=dict)
