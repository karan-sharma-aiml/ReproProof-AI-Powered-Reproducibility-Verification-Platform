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

from fastapi import (
    APIRouter,
    Body,
    File,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from app.services.self_healing.apply_service import ApplyService
from app.services.self_healing.backup_service import BackupService
from app.services.self_healing.history_service import HistoryService
from app.services.self_healing.models import (
    ApplyFixRequest,
    ApplyResult,
    ExecutionHistoryEntry,
    RerunRequest,
    RerunResult,
    RollbackRequest,
    RollbackResult,
)
from app.services.self_healing.retry_engine import RetryEngine
from app.services.self_healing.rollback_service import RollbackService
from app.services.platform.analytics_service import AnalyticsService
from app.services.platform.executive_summary_service import ExecutiveSummaryService
from app.services.platform.health_score_service import HealthScoreService
from app.services.platform.models import (
    AnalyticsResult,
    ExecutiveSummary,
    HealthScoreResult,
)
from app.services.platform.progress_service import ProgressBroker
from fastapi.responses import Response, StreamingResponse

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.agent_result import AgentResult
from app.models.error_analysis import ErrorAnalysis
from app.models.execution_result import ExecutionResult
from app.models.execution_event import ExecutionEvent
from app.models.expected_result import ExpectedResult
from app.models.final_verification_report import FinalVerificationReport
from app.models.repository import RepositoryMetadata
from app.models.repository_ai_analysis import RepositoryAIAnalysis
from app.services.troubleshooter.models import (
    TroubleshootRequest,
    TroubleshootingReport,
)
from app.services.troubleshooter.service import TroubleshootingService
from app.services.patch_generator.models import (
    GeneratePatchRequest,
    PatchGenerationInput,
    PatchResult,
)
from app.services.patch_generator.patch_service import (
    PatchGenerationService,
    runtime_environment,
)
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
_BACKUP_SERVICE = BackupService()
_HISTORY_SERVICE = HistoryService()
_RETRY_ENGINE = RetryEngine(
    history_service=_HISTORY_SERVICE,
    apply_service=ApplyService(_BACKUP_SERVICE),
)
_PROGRESS_BROKER = ProgressBroker()


def _report_path(repository_id: str) -> Path:
    """Return the durable JSON location for a repository report."""
    return get_settings().reports_path / f"report-{repository_id}.json"


def _store_report(repository_id: str, report: FinalVerificationReport) -> None:
    """Cache and persist a report under the same ID used by report routes."""
    _FINAL_REPORTS[repository_id] = report
    reports_path = get_settings().reports_path
    reports_path.mkdir(parents=True, exist_ok=True)
    _report_path(repository_id).write_text(report.model_dump_json(), encoding="utf-8")


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
    agent_result: AgentResult | None = None,
    execution_result: ExecutionResult | None = None,
) -> dict[str, object]:
    """Run the existing services in order and return one JSON-ready report."""
    workflow_agent = agent or ReproProofAgent()
    execution_engine = sandbox or SandboxExecutionEngine()
    analyzer = error_analyzer or ErrorAnalyzer()
    planner = repair_planner or RepairPlanner()
    verifier = verification_engine or VerificationEngine()
    metric_extractor = MetricExtractionService()
    report_service = VerificationReportService()

    resolved_agent_result = agent_result or workflow_agent.run(repository_path)
    is_python_project = resolved_agent_result.observation.project.is_python_project
    if (
        execution_result is None
        and is_python_project
        and resolved_agent_result.observation.execution_ready
    ):
        execution_result = execution_engine.execute(
            repository_path, resolved_agent_result.plan
        )
    elif execution_result is None and not is_python_project:
        execution_result = ExecutionResult(
            success=True,
            exit_code=0,
            stdout="Execution skipped (non-Python project)",
            stderr="",
            execution_time=0.0,
            timed_out=False,
            status="SKIPPED",
            logs=["Execution skipped (non-Python project)"],
        )
    elif execution_result is None:
        execution_result = ExecutionResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr=resolved_agent_result.explanation,
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
        repository_path, resolved_agent_result.observation.repository
    )
    report_key = repository_path.parent.name
    troubleshooting = TroubleshootingService().troubleshoot(
        report_key,
        execution_result,
        repository_path,
        resolved_agent_result.observation.repository.tree,
    )
    final_report = report_service.build(
        resolved_agent_result.observation.repository,
        static_analysis,
        execution_result,
        metrics,
        verification_report,
        repair_plan,
        troubleshooting,
    )
    # Use the uploaded repository directory identity that the route can
    # recover from the incoming repository_path payload. The repository
    # inspection metadata for an observation-only pass does not carry the
    # upload id through the run_verification_workflow() call chain.
    _store_report(report_key, final_report)

    return {
        "goal": resolved_agent_result.goal,
        "observation": resolved_agent_result.observation.model_dump(mode="json"),
        "plan": resolved_agent_result.plan.model_dump(mode="json"),
        "execution": execution_result.model_dump(mode="json"),
        "error_analysis": error_analysis.model_dump(mode="json"),
        "repair_plan": repair_plan.model_dump(mode="json"),
        "verification": verification_report.model_dump(mode="json"),
        "metrics": metrics,
        "report_id": report_key,
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
    from app.infrastructure.service import infrastructure_service

    infrastructure = await infrastructure_service.overview_async()
    return HealthResponse(
        success=True,
        message="Service is healthy.",
        status="ok",
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=infrastructure.database.model_dump(mode="json"),
        redis=infrastructure.cache.model_dump(mode="json"),
        object_storage=infrastructure.storage.model_dump(mode="json"),
        migration_status=infrastructure.migration_status,
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
            if not agent_result.observation.project.is_python_project:
                expected = _build_expected_from_repository(repository_path)
                run_verification_workflow(
                    repository_path,
                    expected,
                    agent_result=agent_result,
                )
                publish(
                    "EXECUTION_SKIPPED",
                    "SUCCESS",
                    "Execution skipped (non-Python project)",
                    25,
                )
                publish("CLEANUP_COMPLETED", "SUCCESS", "No sandbox was created.", 100)
                publish(
                    "VERIFICATION_READY",
                    "SUCCESS",
                    "Verification report generated.",
                    100,
                )
                return
            if not agent_result.observation.execution_ready:
                expected = _build_expected_from_repository(repository_path)
                run_verification_workflow(
                    repository_path,
                    expected,
                    agent_result=agent_result,
                )
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
            run_verification_workflow(
                repository_path,
                expected,
                agent_result=agent_result,
                execution_result=result,
            )
            if result.success:
                publish(
                    "EXECUTION_COMPLETE",
                    "SUCCESS",
                    "Execution completed successfully.",
                    92,
                )
                publish(
                    "REPORT_GENERATED",
                    "SUCCESS",
                    "Verification report generated.",
                    98,
                )
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
        return await asyncio.to_thread(
            run_verification_workflow, repository_path, expected
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/troubleshoot", response_model=TroubleshootingReport)
async def troubleshoot(payload: TroubleshootRequest) -> TroubleshootingReport:
    """Diagnose a stored execution without changing repository files."""
    report = _final_report(payload.execution_id)
    repository_path = _repository_path_from_request(
        report.repository.repository_path or f"{payload.execution_id}/repository"
    )
    troubleshooting_report = await asyncio.to_thread(
        TroubleshootingService().troubleshoot,
        payload.execution_id,
        report.execution,
        repository_path,
        report.repository.tree,
    )
    _store_report(
        payload.execution_id,
        report.model_copy(update={"troubleshooting": troubleshooting_report}),
    )
    return troubleshooting_report


@router.post("/generate-patch", response_model=PatchResult)
async def generate_patch(payload: GeneratePatchRequest) -> PatchResult:
    """Generate and validate a patch preview without applying it."""
    report = _final_report(payload.execution_id)
    repository_path = _repository_path_from_request(
        report.repository.repository_path or f"{payload.execution_id}/repository"
    )
    troubleshooting = report.troubleshooting
    if troubleshooting is None:
        troubleshooting = TroubleshootingService().troubleshoot(
            payload.execution_id,
            report.execution,
            repository_path,
            report.repository.tree,
        )
    requirements_path = repository_path / "requirements.txt"
    try:
        requirements = requirements_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        requirements = ""
    try:
        patch = await asyncio.to_thread(
            PatchGenerationService().generate,
            PatchGenerationInput(
                execution_id=payload.execution_id,
                repository_path=str(repository_path),
                repository_tree=report.repository.tree,
                execution_logs=troubleshooting.execution_log,
                stacktrace=report.execution.stderr,
                error_message=troubleshooting.detected_error or report.execution.stderr,
                root_cause=troubleshooting.root_cause,
                human_explanation=troubleshooting.explanation,
                suggested_fix=" ".join(troubleshooting.possible_fixes),
                requirements=requirements,
                environment=runtime_environment(),
            ),
        )
    except (OSError, UnicodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    _store_report(
        payload.execution_id,
        report.model_copy(
            update={"troubleshooting": troubleshooting, "generated_patch": patch}
        ),
    )
    return patch


@router.post("/apply-fix", response_model=ApplyResult)
async def apply_fix(payload: ApplyFixRequest) -> ApplyResult:
    """Back up and apply a stored validated patch preview."""
    report = _final_report(payload.execution_id)
    patch = report.generated_patch
    if patch is None or patch.patch_id != payload.patch_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patch not found"
        )
    repository_path = _repository_path_from_request(
        report.repository.repository_path or f"{payload.execution_id}/repository"
    )
    _PROGRESS_BROKER.publish(
        payload.execution_id,
        "PATCH_APPLY",
        "RUNNING",
        65,
        "Applying validated patch",
    )
    try:
        result = await asyncio.to_thread(
            ApplyService(_BACKUP_SERVICE).apply,
            payload.execution_id,
            repository_path,
            patch,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        _PROGRESS_BROKER.publish(
            payload.execution_id, "PATCH_APPLY", "FAILED", 65, str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    _store_report(
        payload.execution_id,
        report.model_copy(
            update={
                "applied_patch": patch,
                "backup_path": result.backup_location,
                "rollback_available": True,
                "final_status": "PATCH_APPLIED",
            }
        ),
    )
    _PROGRESS_BROKER.publish(
        payload.execution_id,
        "PATCH_APPLY",
        "SUCCESS",
        70,
        "Patch applied and verified",
    )
    return result


@router.post("/rerun", response_model=RerunResult)
async def rerun(payload: RerunRequest) -> RerunResult:
    """Rerun an applied patch and perform bounded intelligent retries."""
    report = _final_report(payload.execution_id)
    if report.applied_patch is None or not report.backup_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Apply a generated patch before rerunning",
        )
    repository_path = _repository_path_from_request(
        report.repository.repository_path or f"{payload.execution_id}/repository"
    )
    _PROGRESS_BROKER.publish(
        payload.execution_id, "RERUN", "RUNNING", 75, "Re-running repository"
    )
    try:
        result = await asyncio.to_thread(
            _RETRY_ENGINE.run,
            payload.execution_id,
            repository_path,
            report.applied_patch,
            report.backup_path,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        _PROGRESS_BROKER.publish(payload.execution_id, "RERUN", "FAILED", 75, str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    _store_report(
        payload.execution_id,
        report.model_copy(
            update={
                "execution": result.execution,
                "retry_count": result.retry_count,
                "applied_patch": result.applied_patch,
                "execution_history": result.history,
                "backup_path": result.backup_path,
                "rollback_available": result.rollback_available,
                "final_status": result.final_status,
            }
        ),
    )
    _PROGRESS_BROKER.publish(
        payload.execution_id,
        "FINISHED",
        "SUCCESS" if result.execution.success else "FAILED",
        100,
        result.final_status,
    )
    return result


@router.post("/rollback", response_model=RollbackResult)
async def rollback(payload: RollbackRequest) -> RollbackResult:
    """Restore all backups recorded for an execution in reverse order."""
    report = _final_report(payload.execution_id)
    repository_path = _repository_path_from_request(
        report.repository.repository_path or f"{payload.execution_id}/repository"
    )
    locations = [
        entry.backup_path for entry in report.execution_history if entry.backup_path
    ]
    if report.backup_path:
        locations.append(report.backup_path)
    _PROGRESS_BROKER.publish(
        payload.execution_id, "ROLLBACK", "RUNNING", 80, "Restoring backup files"
    )
    try:
        result = await asyncio.to_thread(
            RollbackService(_BACKUP_SERVICE).rollback,
            payload.execution_id,
            repository_path,
            locations,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        _PROGRESS_BROKER.publish(
            payload.execution_id, "ROLLBACK", "FAILED", 80, str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    _store_report(
        payload.execution_id,
        report.model_copy(
            update={
                "rollback_available": False,
                "final_status": "ROLLED_BACK",
            }
        ),
    )
    _PROGRESS_BROKER.publish(
        payload.execution_id,
        "ROLLBACK",
        "SUCCESS",
        100,
        "Original files restored",
    )
    return result


@router.get("/execution-history", response_model=list[ExecutionHistoryEntry])
async def execution_history(
    execution_id: str | None = Query(default=None),
) -> list[ExecutionHistoryEntry]:
    """Return self-healing attempts, optionally filtered by execution ID."""
    return _HISTORY_SERVICE.list(execution_id)


@router.websocket("/ws/progress/{execution_id}")
async def websocket_progress(websocket: WebSocket, execution_id: str) -> None:
    """Stream additive self-healing progress events over WebSocket."""
    await websocket.accept()
    subscriber = _PROGRESS_BROKER.subscribe(execution_id)
    try:
        while True:
            event = await asyncio.to_thread(subscriber.get)
            await websocket.send_json(event.model_dump(mode="json"))
            if (
                event.status in {"SUCCESS", "FAILED", "CANCELLED"}
                and event.progress >= 100
            ):
                break
    except WebSocketDisconnect:
        return
    finally:
        _PROGRESS_BROKER.unsubscribe(execution_id, subscriber)


@router.get("/analytics", response_model=AnalyticsResult)
async def analytics() -> AnalyticsResult:
    """Return aggregate analytics for reports held by this process."""
    return AnalyticsService().summarize(
        _FINAL_REPORTS.values(), _HISTORY_SERVICE.list()
    )


@router.get("/health-score/{repository_id}", response_model=HealthScoreResult)
async def health_score(repository_id: str) -> HealthScoreResult:
    report = _final_report(repository_id)
    result = HealthScoreService().calculate(
        report.repository,
        report.static_analysis,
        report.execution,
        patch_success=report.final_status in {"SUCCEEDED", "REPRODUCED"},
        retry_success=report.retry_count > 0 and report.execution.success,
    )
    _store_report(
        repository_id,
        report.model_copy(
            update={"health_score": result.score, "health_score_details": result}
        ),
    )
    return result


@router.get("/summary/{repository_id}", response_model=ExecutiveSummary)
async def executive_summary(repository_id: str) -> ExecutiveSummary:
    report = _final_report(repository_id)
    summary = ExecutiveSummaryService().build(repository_id, report)
    _store_report(
        repository_id,
        report.model_copy(
            update={
                "executive_summary": summary,
                "health_score": summary.health_score,
            }
        ),
    )
    return summary


# ── GET /metrics/{id}, /verification/{id}, /report/{id} ─────────────────────


def _final_report(repository_id: str) -> FinalVerificationReport:
    report = _FINAL_REPORTS.get(repository_id)
    if report is None:
        report_file = _report_path(repository_id)
        try:
            report = FinalVerificationReport.model_validate_json(
                report_file.read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            report = None
        if report is not None:
            _FINAL_REPORTS[repository_id] = report
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
