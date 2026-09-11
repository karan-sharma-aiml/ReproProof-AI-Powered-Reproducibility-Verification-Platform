"""Models produced by repository inspection."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RepositoryMetadata(BaseModel):
    """Structured, JSON-serializable metadata for an extracted repository."""

    model_config = ConfigDict(frozen=True)

    repository_name: str
    total_files: int = Field(ge=0)
    total_folders: int = Field(ge=0)
    python_files: int = Field(ge=0)
    notebooks: int = Field(ge=0)
    important_files: list[str] = Field(default_factory=list)
    source_directories: list[str] = Field(default_factory=list)
    detected_languages: list[str] = Field(default_factory=list)
    repository_id: str = ""
    repository_path: str = ""
    tree: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    detected_frameworks: list[str] = Field(default_factory=list)
    health_score: int = Field(default=0, ge=0, le=100)
    warnings: list[str] = Field(default_factory=list)
