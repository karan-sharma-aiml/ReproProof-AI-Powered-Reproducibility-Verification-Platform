from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
from zipfile import ZipInfo

from app.utils.file_utils import ALLOWED_CONTENT_TYPES, ALLOWED_EXTENSIONS


class SecurityValidator:
    @staticmethod
    def repository_url(value: str) -> str:
        parsed = urlparse(value.strip())
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise ValueError("Repository URL must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password:
            raise ValueError("Repository URL cannot contain credentials")
        return value.strip()

    @staticmethod
    def filename(value: str) -> str:
        safe = Path(value).name
        safe = re.sub(r"[^\w.\-]", "_", safe)
        if not safe or safe in {".", ".."}:
            raise ValueError("Filename is empty or unsafe")
        return safe

    @staticmethod
    def content_type(content_type: str | None) -> None:
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError("Unsupported content type")

    @staticmethod
    def upload_filename(value: str) -> None:
        if Path(value).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValueError("Only ZIP uploads are accepted")

    @staticmethod
    def archive_member(member: ZipInfo, target: Path) -> None:
        relative = PurePosixPath(member.filename.replace("\\", "/"))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Archive contains a path traversal member")
        (target / Path(*relative.parts)).resolve().relative_to(target.resolve())
