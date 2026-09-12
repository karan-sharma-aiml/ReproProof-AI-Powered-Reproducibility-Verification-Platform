from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def normalize_identifier(value: str, *, fallback: str = "entity") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    return cleaned or fallback


def ensure_directory(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def is_truthy(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() not in {"", "false", "0", "no", "off"}
    return True
