from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from app.ai.framework import AgentContext
from app.ai.orchestration import (
    EnterpriseOrchestrator,
    WorkflowTemplates,
    enterprise_orchestrator,
)
from app.core.config import get_settings

router = APIRouter(prefix="/orchestrator", tags=["enterprise orchestration"])


class WorkflowRunRequest(BaseModel):
    template: str = "enterprise"
    repository_id: str | None = None
    parallel: bool = True
    context: dict[str, Any] = Field(default_factory=dict)


class WorkflowActionRequest(BaseModel):
    workflow_id: str


def _context(request: WorkflowRunRequest) -> AgentContext:
    context = AgentContext(shared_memory=dict(request.context))
    if request.repository_id:
        root = get_settings().upload_path.resolve()
        repository_path = (root / request.repository_id / "repository").resolve()
        if root not in repository_path.parents or not repository_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found"
            )
        context.repository_metadata.update(
            {"path": str(repository_path), "repository_id": request.repository_id}
        )
    return context


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def run(request: WorkflowRunRequest) -> dict[str, Any]:
    try:
        record = await enterprise_orchestrator.start(
            request.template, _context(request), request.repository_id, request.parallel
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return enterprise_orchestrator.status_payload(record)


@router.post("/pause")
async def pause(request: WorkflowActionRequest) -> dict[str, Any]:
    try:
        return enterprise_orchestrator.status_payload(
            await enterprise_orchestrator.pause(request.workflow_id)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post("/resume")
async def resume(request: WorkflowActionRequest) -> dict[str, Any]:
    try:
        return enterprise_orchestrator.status_payload(
            await enterprise_orchestrator.resume(request.workflow_id)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post("/cancel")
async def cancel(request: WorkflowActionRequest) -> dict[str, Any]:
    try:
        return enterprise_orchestrator.status_payload(
            await enterprise_orchestrator.cancel(request.workflow_id)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/workflows")
def workflows() -> list[dict[str, Any]]:
    return [
        enterprise_orchestrator.status_payload(record)
        for record in enterprise_orchestrator.records()
    ]


@router.get("/status")
def workflow_status(workflow_id: str) -> dict[str, Any]:
    try:
        return enterprise_orchestrator.status_payload(
            enterprise_orchestrator.get(workflow_id)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/history")
def history(workflow_id: str | None = None) -> list[dict[str, Any]]:
    records = (
        [enterprise_orchestrator.get(workflow_id)]
        if workflow_id
        else enterprise_orchestrator.records()
    )
    return [enterprise_orchestrator.status_payload(record) for record in records]


@router.get("/events")
def events(workflow_id: str) -> list[dict[str, Any]]:
    try:
        return jsonable_encoder(enterprise_orchestrator.history(workflow_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/agents")
def agents() -> dict[str, Any]:
    return {
        "agents": enterprise_orchestrator.agents(),
        "templates": WorkflowTemplates.names(),
    }


@router.get("/graph")
def graph(template: str = "enterprise") -> dict[str, Any]:
    try:
        return enterprise_orchestrator.graph(template)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post("/approve")
async def approve(request: WorkflowActionRequest) -> dict[str, Any]:
    try:
        record = enterprise_orchestrator.get(request.workflow_id)
        record.approval_required = None
        return enterprise_orchestrator.status_payload(record)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post("/reject")
async def reject(request: WorkflowActionRequest) -> dict[str, Any]:
    try:
        record = enterprise_orchestrator.get(request.workflow_id)
        record.approval_required = "rejected"
        return enterprise_orchestrator.status_payload(record)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
