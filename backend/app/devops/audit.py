from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


class AuditLogger:
    """Structured audit events suitable for forwarding to a durable sink."""

    def __init__(self, name: str = "reproproof.audit") -> None:
        self.logger = logging.getLogger(name)

    def record(
        self,
        action: str,
        actor: str = "system",
        *,
        request_id: str = "",
        **details: Any,
    ) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "actor": actor,
            "request_id": request_id,
            "details": details,
        }
        self.logger.info(json.dumps(event, default=str, sort_keys=True))


audit_logger = AuditLogger()
