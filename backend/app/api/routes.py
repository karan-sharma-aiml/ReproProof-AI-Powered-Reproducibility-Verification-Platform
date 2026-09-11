"""
API route definitions.

All endpoint handlers live here and delegate business logic to the
service layer.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Body, File, HTTPException, UploadFile, status
from fastapi.responses import Response, StreamingResponse

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.error_analysis import ErrorAnalysis
from app.models.execution_result import ExecutionResult
from app.models.execution_event import ExecutionEvent
from app.models.expected_result import ExpectedResult
from app.models.final_verification_report import FinalVerificationReport
from app.models.repository import RepositoryMetadata
from app.models.repository_ai_analysis import RepositoryAIAnalysis
from app.services.error_analyzer import ErrorAnalyzer
from app.services.repair_planner import RepairPlanner
from app.services.reproproof_agent import ReproProofAgent
from app.services.sandbox_execution_engine import SandboxExecutionEngine
from app.services.verification_engine import VerificationEngine
from app.services.metric_extraction_service import MetricExtractionService
from app.services.verification_report_service import VerificationReportService
from app.services.execution_event_publisher import ExecutionEventPublisher
from app.services.repository_analysis_service import RepositoryAnalysisService
from app.services.repository_ai_analyzer import RepositoryAIAnalyzer
from app.schemas.responses import (
    ErrorResponse,
    HealthResponse,
    RootResponse,
    StatusResponse,
    UploadResponse,
    UploadSummary,
)
from app.services.upload_service import handle_upload

logger = get_logger("api")
router = APIRouter()
_FINAL_REPORTS: dict[str, FinalVerificationReport] = {}


def _build_expected_from_repository(repository_path: Path) -> ExpectedResult:
    """Derive the expected metric object from the repo's expected metadata file.

    The repository starter artifact keeps the expected values in an
    `expected.json` file when present, and otherwise falls back to the plain
    README text used by the QA demo. This keeps the SSE stream endpoint on the
    same verification factory path that already creates the final report.
    """
    expected_file = repository_path / "expected.json"
    if expected_file.exists():
        payload = json.loads(expected_file.read_text(encoding="utf-8"))
        metric_name = payload.get("metric") or payload.get("metric_name") or "accuracy"
        return ExpectedResult(
            expected_value=float(
                payload.get("expected") or payload.get("expected_value") or 0.0
            ),
            metric_name=str(metric_name),
            tolerance=float(payload.get("tolerance") or 0.0),
            metrics=payload.get("metrics") or {},
            percentage_tolerance=payload.get("percentage_tolerance"),
        )

    readme = repository_path / "README.md"
    readme_text = (
        readme.read_text(encoding="utf-8", errors="ignore") if readme.exists() else ""
    )

    metric_match = re.search(
        r"expected\s+metric\s*:\s*([a-zA-Z0-9_]+)\s*=\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)",
        readme_text,
        flags=re.IGNORECASE,
    )
    if not metric_match:
        metric_match = re.search(
            r"expected\s+accuracy\s*[:=]\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)",
            readme_text,
            flags=re.IGNORECASE,
        )
        metric_name = "accuracy"
        expected_value = float(metric_match.group(1)) if metric_match else 0.0
    else:
        metric_name = metric_match.group(1).strip().lower()
        expected_value = float(metric_match.group(2))

    tolerance_match = re.search(
        r"tolerance\s*[:=]\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)",
        readme_text,
        flags=re.IGNORECASE,
    )
    tolerance = float(tolerance_match.group(1)) if tolerance_match else 0.0

    return ExpectedResult(
        expected_value=expected_value,
        metric_name=metric_name,
        tolerance=tolerance,
        metrics={},
        percentage_tolerance=None,
    )


def run_verification_workflow(
    repository_path: Path,
    expected: ExpectedResult,
    *,
    agent: ReproProofAgent | None = None,
    sandbox: SandboxExecutionEngine | None = None,
    error_analyzer: ErrorAnalyzer | None = None,
    repair_planner: RepairPlanner | None = None,
    verification_engine: VerificationEngine | None = None,
) -> dict[str, object]:
    """Run the existing services in order and return one JSON-ready report."""
    workflow_agent = agent or ReproProofAgent()
    execution_engine = sandbox or SandboxExecutionEngine()
    analyzer = error_analyzer or ErrorAnalyzer()
    planner = repair_planner or RepairPlanner()
    verifier = verification_engine or VerificationEngine()
    metric_extractor = MetricExtractionService()
    report_service = VerificationReportService()

    agent_result = workflow_agent.run(repository_path)
    if agent_result.observation.execution_ready:
        execution_result = execution_engine.execute(repository_path, agent_result.plan)
    else:
        execution_result = ExecutionResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr=agent_result.explanation,
            execution_time=0.0,
            timed_out=False,
        )

    error_analysis = analyzer.analyze(execution_result)
    repair_plan = planner.create_plan(error_analysis)
    metrics = metric_extractor.extract(execution_result)
    expected_metrics = expected.metrics or {
        expected.metric_name: expected.expected_value
    }
    verification_report = verifier.verify_metrics(
        expected_metrics,
        metrics,
        absolute_tolerance=expected.tolerance,
        percentage_tolerance=expected.percentage_tolerance,
    )
    static_analysis = RepositoryAIAnalyzer().analyze(
        repository_path, agent_result.observation.repository
    )
    final_report = report_service.build(
        agent_result.observation.repository,
        static_analysis,
        execution_result,
        metrics,
        verification_report,
        repair_plan,
    )
    # Use the uploaded repository directory identity that the route can
    # recover from the incoming repository_path payload. The repository
    # inspection metadata for an observation-only pass does not carry the
    # upload id through the run_verification_workflow() call chain.
    report_key = repository_path.parent.name
    _FINAL_REPORTS[report_key] = final_report

    return {
        "goal": agent_result.goal,
        "observation": agent_result.observation.model_dump(mode="json"),
        "plan": agent_result.plan.model_dump(mode="json"),
        "execution": execution_result.model_dump(mode="json"),
        "error_analysis": error_analysis.model_dump(mode="json"),
        "repair_plan": repair_plan.model_dump(mode="json"),
        "verification": verification_report.model_dump(mode="json"),
        "metrics": metrics,
        "final_report": final_report.model_dump(mode="json"),
    }


def _repository_path_from_request(repository_path: str) -> Path:
    """Resolve an extracted repository while keeping API access inside uploads."""
    uploads_root = get_settings().upload_path.resolve()
    requested = Path(repository_path).expanduser()
    candidate = (
        requested if requested.is_absolute() else uploads_root / requested
    ).resolve()
    try:
        candidate.relative_to(uploads_root)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="repository_path must be inside the configured uploads directory",
        ) from exc
    return candidate


# ── GET / ────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=RootResponse,
    summary="Root",
    description="Returns basic application info and a link to the docs.",
)
async def root() -> RootResponse:
    settings = get_settings()
    return RootResponse(
        success=True,
        message=f"Welcome to {settings.APP_NAME}",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs="/docs",
    )


# ── GET /health ──────────────────────────────────────────────────────────────


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Lightweight liveness probe for monitoring.",
)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        success=True,
        message="Service is healthy.",
        status="ok",
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ── POST /upload ─────────────────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a ZIP file",
    description="Accepts a ZIP archive, validates it, and persists it to the uploads directory.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file type"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def upload(
    file: UploadFile = File(..., description="ZIP file to upload")
) -> UploadResponse:
    logger.info(
        "Incoming upload: filename=%s content_type=%s",
        file.filename,
        file.content_type,
    )
    data = await handle_upload(file)
    return UploadResponse(
        success=True,
        message="File uploaded successfully.",
        data=data,
    )


# ── GET /status ──────────────────────────────────────────────────────────────


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="System status",
    description="Returns the current state of uploads and reports directories.",
)
async def get_status() -> StatusResponse:
    settings = get_settings()
    upload_dir = settings.upload_path
    reports_dir = settings.reports_path

    uploads: list[UploadSummary] = []
    if upload_dir.exists():
        for entry in sorted(
            upload_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
        ):
            if entry.is_file():
                stat = entry.stat()
                uploads.append(
                    UploadSummary(
                        upload_id=entry.name.split("_", 1)[0],
                        filename=entry.name,
                        size_bytes=stat.st_size,
                        uploaded_at=datetime.fromtimestamp(
                            stat.st_mtime, tz=timezone.utc
                        ).isoformat(),
                    )
                )

    return StatusResponse(
        success=True,
        message="System status retrieved.",
        environment=settings.APP_ENV,
        uploads_dir=str(upload_dir.resolve()),
        reports_dir=str(reports_dir.resolve()),
        total_uploads=len(uploads),
        uploads=uploads,
    )


# ── GET /repository/{id} ────────────────────────────────────────────────────


@router.get(
    "/repository/{repository_id}",
    response_model=RepositoryMetadata,
    summary="Get repository analysis",
)
async def get_repository(repository_id: str) -> RepositoryMetadata:
    if not repository_id or repository_id != Path(repository_id).name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository id",
        )
    repository_path = _repository_path_from_request(f"{repository_id}/repository")
    if not repository_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository analysis not found",
        )
    return RepositoryAnalysisService().analyze_repository(
        repository_path, repository_id
    )


# ── GET /analysis/{id} ──────────────────────────────────────────────────────


@router.get(
    "/analysis/{repository_id}",
    response_model=RepositoryAIAnalysis,
    summary="Get repository reproducibility analysis",
)
async def get_repository_analysis(repository_id: str) -> RepositoryAIAnalysis:
    metadata = await get_repository(repository_id)
    repository_path = _repository_path_from_request(f"{repository_id}/repository")
    return RepositoryAIAnalyzer().analyze(repository_path, metadata)


# ── GET /execution/{id}/stream ─────────────────────────────────────────────


@router.get(
    "/execution/{repository_id}/stream",
    summary="Stream repository execution events",
)
async def stream_execution(repository_id: str) -> StreamingResponse:
    publisher = ExecutionEventPublisher()

    def publish(stage: str, event_status: str, message: str, progress: int) -> None:
        publisher.publish(
            ExecutionEvent(
                stage=stage,
                status=event_status,
                message=message,
                progress=progress,
            )
        )

    def run() -> None:
        try:
            repository_path = _repository_path_from_request(
                f"{repository_id}/repository"
            )
            publish("REPOSITORY_UPLOADED", "SUCCESS", "Repository uploaded.", 5)
            publish("REPOSITORY_EXTRACTED", "SUCCESS", "Repository extracted.", 10)
            agent_result = ReproProofAgent().run(repository_path)
            publish(
                "REPOSITORY_ANALYSIS_COMPLETE",
                "SUCCESS",
                "Repository analysis complete.",
                20,
            )
            publish(
                "EXECUTION_PLAN_GENERATED", "SUCCESS", "Execution plan generated.", 25
            )
            if not agent_result.observation.execution_ready:
                publish("EXECUTION_FAILED", "FAILED", agent_result.explanation, 25)
                publish("CLEANUP_COMPLETED", "SUCCESS", "No sandbox was created.", 100)
                publish(
                    "VERIFICATION_READY",
                    "FAILED",
                    "Execution did not produce a successful result.",
                    100,
                )
                return
            engine = SandboxExecutionEngine(
                event_publisher=publisher,
                reports_root=get_settings().reports_path,
            )
            result = engine.execute(repository_path, agent_result.plan)
            expected = _build_expected_from_repository(repository_path)
            run_verification_workflow(repository_path, expected)
            publish(
                "VERIFICATION_READY",
                "SUCCESS" if result.success else "FAILED",
                "Execution result is ready for verification.",
                100,
            )
        except Exception as exc:
            logger.exception("Streaming execution failed for %s", repository_id)
            publish("EXECUTION_FAILED", "FAILED", str(exc), 0)
            publish("CLEANUP_COMPLETED", "SUCCESS", "Execution stream closed.", 100)
            publish(
                "VERIFICATION_READY",
                "FAILED",
                "Execution result is ready for verification.",
                100,
            )

    async def events():
        task = asyncio.create_task(asyncio.to_thread(run))
        terminal_stages = {"VERIFICATION_READY"}
        while True:
            event = await asyncio.to_thread(publisher.queue.get)
            yield f"data: {json.dumps(event.model_dump(mode='json'))}\n\n"
            if event.stage in terminal_stages:
                break
        await task

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# ── POST /verify ────────────────────────────────────────────────────────────


@router.post(
    "/verify",
    summary="Run the verification workflow",
    description=(
        "Coordinates observation, planning, sandbox execution, error analysis, "
        "repair planning, and result verification for an extracted repository."
    ),
)
async def verify(payload: dict[str, object] = Body(...)) -> dict[str, object]:
    try:
        repository_value = payload.get("repository_path")
        expected_value = payload.get("expected")
        if not isinstance(repository_value, str) or not isinstance(
            expected_value, dict
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="repository_path and expected are required",
            )
        expected = ExpectedResult.model_validate(expected_value)
        repository_path = _repository_path_from_request(repository_value)
        return run_verification_workflow(repository_path, expected)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ── GET /metrics/{id}, /verification/{id}, /report/{id} ─────────────────────


def _final_report(repository_id: str) -> FinalVerificationReport:
    report = _FINAL_REPORTS.get(repository_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification report not found",
        )
    return report


@router.get("/metrics/{repository_id}")
async def get_metrics(repository_id: str) -> dict[str, float]:
    return _final_report(repository_id).metrics


@router.get("/verification/{repository_id}", response_model=FinalVerificationReport)
async def get_verification(repository_id: str) -> FinalVerificationReport:
    return _final_report(repository_id)


@router.get("/report/{repository_id}")
async def get_report(repository_id: str) -> dict[str, object]:
    report = _final_report(repository_id)
    return {
        "report": report.model_dump(mode="json"),
        "markdown": report.markdown_report,
    }


@router.get("/report/{repository_id}/markdown")
async def get_report_markdown(repository_id: str) -> Response:
    report = _final_report(repository_id)
    return Response(
        report.markdown_report,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="reproproof-{repository_id}.md"'
        },
    )


@router.get("/report/{repository_id}/pdf")
async def get_report_pdf(repository_id: str) -> Response:
    report = _final_report(repository_id)
    return Response(
        VerificationReportService().pdf_bytes(report.markdown_report),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="reproproof-{repository_id}.pdf"'
        },
    )
