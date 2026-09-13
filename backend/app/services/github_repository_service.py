"""GitHub repository ingestion for the shared verification pipeline."""

from __future__ import annotations

import asyncio
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException, status
from git import GitCommandError, Repo

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.responses import UploadData
from app.services.repository_analysis_service import RepositoryAnalysisService
from app.utils.file_utils import ensure_directory, generate_upload_filename

logger = get_logger("github_repository_service")

_GITHUB_REPOSITORY_PATTERN = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9-]+)/(?P<repo>[A-Za-z0-9_.-]+)$"
)


class GitHubRepositoryError(Exception):
    """Base error for GitHub ingestion failures."""


class InvalidGitHubRepository(GitHubRepositoryError):
    """The URL is not an accepted public GitHub repository URL."""


class GitHubRepositoryNotFound(GitHubRepositoryError):
    """GitHub reported that the repository does not exist."""


class GitHubPrivateRepository(GitHubRepositoryError):
    """The repository requires authentication."""


class GitHubCloneTimeout(GitHubRepositoryError):
    """Cloning exceeded the configured timeout."""


class GitHubCloneFailure(GitHubRepositoryError):
    """The repository could not be cloned."""


def validate_github_repository_url(repository_url: str) -> str:
    """Validate and normalize the exact public GitHub URL shape we support."""
    normalized = repository_url.strip()
    match = _GITHUB_REPOSITORY_PATTERN.fullmatch(normalized)
    if not match:
        raise InvalidGitHubRepository(
            "Repository URL must match https://github.com/<owner>/<repo>"
        )

    parsed = urlparse(normalized)
    if parsed.hostname != "github.com" or parsed.username or parsed.password:
        raise InvalidGitHubRepository(
            "Repository URL must match https://github.com/<owner>/<repo>"
        )
    return normalized


def _clone_error(error: GitCommandError) -> GitHubRepositoryError:
    """Convert GitHub/Git errors into stable API-level categories."""
    details = " ".join(
        value for value in (str(error), error.stderr or "") if value
    ).lower()
    if any(
        phrase in details
        for phrase in (
            "authentication failed",
            "could not read username",
            "permission denied",
            "authentication required",
            "403",
        )
    ):
        return GitHubPrivateRepository(
            "The GitHub repository is private or requires authentication."
        )
    if "repository not found" in details or "not found" in details:
        return GitHubRepositoryNotFound("GitHub repository was not found.")
    return GitHubCloneFailure("GitHub repository could not be cloned.")


def _clone_and_prepare(repository_url: str) -> UploadData:
    """Clone, analyze, and persist a GitHub repository for normal verification."""
    settings = get_settings()
    parsed = urlparse(repository_url)
    owner, repo_name = parsed.path.strip("/").split("/", maxsplit=1)
    upload_id, saved_filename = generate_upload_filename(
        f"github_{owner}_{repo_name}.zip"
    )
    upload_dir = ensure_directory(settings.upload_path)
    repository_destination = upload_dir / upload_id / "repository"
    marker_path = upload_dir / saved_filename

    try:
        with tempfile.TemporaryDirectory(prefix="reproproof-github-") as temporary_dir:
            clone_destination = Path(temporary_dir) / "repository"
            try:
                Repo.clone_from(
                    repository_url,
                    clone_destination,
                    depth=1,
                    env={"GIT_TERMINAL_PROMPT": "0"},
                )
            except GitCommandError as error:
                raise _clone_error(error) from error

            repository_destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(
                clone_destination,
                repository_destination,
                ignore=shutil.ignore_patterns(".git"),
            )

        metadata = RepositoryAnalysisService().analyze_repository(
            repository_destination, upload_id
        )
        size_bytes = sum(
            path.stat().st_size
            for path in repository_destination.rglob("*")
            if path.is_file()
        )
        marker_path.write_text(repository_url, encoding="utf-8")
        logger.info(
            "GitHub repository prepared: url=%s id=%s files=%d",
            repository_url,
            upload_id,
            metadata.total_files,
        )
        return UploadData(
            upload_id=upload_id,
            original_filename=f"{owner}/{repo_name}",
            saved_filename=saved_filename,
            size_bytes=size_bytes,
            uploaded_at=datetime.now(timezone.utc).isoformat(),
            repository_path=f"{upload_id}/repository",
        )
    except GitHubRepositoryError:
        shutil.rmtree(upload_dir / upload_id, ignore_errors=True)
        marker_path.unlink(missing_ok=True)
        raise
    except (OSError, ValueError) as error:
        shutil.rmtree(upload_dir / upload_id, ignore_errors=True)
        marker_path.unlink(missing_ok=True)
        logger.exception("Failed to prepare GitHub repository %s", repository_url)
        raise GitHubCloneFailure(
            "The repository was cloned but could not be prepared for verification."
        ) from error


async def ingest_github_repository(repository_url: str) -> UploadData:
    """Clone and prepare a GitHub repository with a bounded execution time."""
    normalized_url = validate_github_repository_url(repository_url)
    timeout = get_settings().GITHUB_CLONE_TIMEOUT_SECONDS
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_clone_and_prepare, normalized_url),
            timeout=timeout,
        )
    except asyncio.TimeoutError as error:
        raise GitHubCloneTimeout(
            f"GitHub repository cloning exceeded the {timeout:g}-second timeout."
        ) from error
