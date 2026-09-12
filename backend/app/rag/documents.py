from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from .models import DocumentChunk, DocumentSource


class DocumentIntelligence:
    """Dependency-light extraction for supported enterprise document types."""

    def extract(
        self,
        uri: str,
        content: str | None = None,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[DocumentSource, list[DocumentChunk]]:
        path = Path(uri)
        suffix = path.suffix.lower()
        raw = (
            content
            if content is not None
            else path.read_text(encoding="utf-8", errors="ignore")
        )
        document_type = suffix.lstrip(".") or "text"
        extracted: dict[str, Any] = {
            **(metadata or {}),
            "sections": self._sections(raw),
            "references": self._references(raw),
            "citations": self._citations(raw),
        }
        if suffix == ".json":
            try:
                value = json.loads(raw)
                extracted["json_keys"] = (
                    list(value.keys()) if isinstance(value, dict) else []
                )
            except (json.JSONDecodeError, AttributeError):
                extracted["json_keys"] = []
        elif suffix == ".csv":
            rows = list(csv.reader(io.StringIO(raw)))
            extracted["columns"] = rows[0] if rows else []
            extracted["row_count"] = max(0, len(rows) - 1)
        elif suffix == ".docx" and content is None:
            raw, extracted["sections"] = self._docx_text(path)
        source = DocumentSource(
            uri=uri,
            title=title or path.name,
            document_type=document_type,
            metadata=extracted,
        )
        return source, self._chunk(source, raw)

    @staticmethod
    def _docx_text(path: Path) -> tuple[str, list[str]]:
        try:
            with zipfile.ZipFile(path) as archive:
                xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
            text = " ".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml))
            return text, DocumentIntelligence._sections(text)
        except (OSError, KeyError, zipfile.BadZipFile):
            return "", []

    @staticmethod
    def _sections(text: str) -> list[str]:
        return [
            match.group(2).strip()
            for match in re.finditer(r"^(#{1,6})\s+(.+)$", text, re.MULTILINE)
        ]

    @staticmethod
    def _references(text: str) -> list[str]:
        return [
            line.strip()
            for line in text.splitlines()
            if re.match(r"^\s*(references|bibliography)\s*$", line, re.I)
        ]

    @staticmethod
    def _citations(text: str) -> list[str]:
        return sorted(
            {
                match.group(1) or match.group(2)
                for match in re.finditer(r"\[([^\]]+)\]|\(([^()]+\d{4})\)", text)
            }
        )

    @staticmethod
    def _chunk(
        source: DocumentSource, text: str, size: int = 900
    ) -> list[DocumentChunk]:
        words = text.split()
        return [
            DocumentChunk(
                source_id=source.id,
                text=" ".join(words[index : index + size]),
                index=index // size,
                metadata={"title": source.title},
            )
            for index in range(0, len(words), size)
        ] or [
            DocumentChunk(
                source_id=source.id, text="", index=0, metadata={"title": source.title}
            )
        ]
