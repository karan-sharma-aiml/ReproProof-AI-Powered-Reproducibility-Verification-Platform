"""GitHub repository verification routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.responses import ErrorResponse, UploadResponse
from app.services.github_repository_service import (
    GitHubCloneFailure,
    GitHubCloneTimeout,
    GitHubPrivateRepository,
    GitHubRepositoryNotFound,
    InvalidGitHubRepository,
    ingest_github_repository,
)

router = APIRouter(tags=["github verification"])


class GitHubVerificationRequest(BaseModel):
    repository_url: str = Field(..., min_length=1)


@router.post(
    "/verify/github",
    response_model=UploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid repository URL"},
        403: {"model": ErrorResponse, "description": "Private repository"},
        404: {"model": ErrorResponse, "description": "Repository not found"},
        408: {"model": ErrorResponse, "description": "Clone timeout"},
        502: {"model": ErrorResponse, "description": "Clone or preparation failure"},
    },
    summary="Verify a GitHub repository",
    description=(
        "Clone a public GitHub repository, analyze it using the same repository "
        "pipeline as ZIP uploads, and return the normal upload response."
    ),
)
async def verify_github_repository(
    request: GitHubVerificationRequest,
) -> UploadResponse:
    try:
        data = await ingest_github_repository(request.repository_url)
    except InvalidGitHubRepository as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except GitHubPrivateRepository as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error
    except GitHubRepositoryNotFound as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except GitHubCloneTimeout as error:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=str(error),
        ) from error
    except GitHubCloneFailure as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return UploadResponse(
        success=True,
        message="GitHub repository prepared for verification.",
        data=data,
    )
