from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger

from .models import AuditEvent


class SecurityAuditLogger:
    """Security audit facade for authentication and high-value platform actions."""

    def __init__(self) -> None:
        self.logger = get_logger("security.audit")
        self.events: list[AuditEvent] = []

    def record(
        self,
        action: str,
        actor: str = "system",
        *,
        request_id: str = "",
        success: bool = True,
        **details: Any,
    ) -> AuditEvent:
        event = AuditEvent(
            action=action,
            actor=actor,
            request_id=request_id,
            timestamp=datetime.now(timezone.utc),
            success=success,
            details=details,
        )
        self.events.append(event)
        self.logger.info(
            "security_audit action=%s actor=%s request_id=%s success=%s",
            action,
            actor,
            request_id,
            success,
        )
        return event


security_audit = SecurityAuditLogger()
