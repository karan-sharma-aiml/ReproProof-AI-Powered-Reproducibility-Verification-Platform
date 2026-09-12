from __future__ import annotations

from pathlib import Path
import csv
import io
import json
import zipfile

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.core.config import get_settings
from app.showcase.models import ArchitectureArtifact, EnterpriseOverview, ReadmeArtifact
from app.showcase.exports import JudgePresentationExporter
from app.showcase.service import ShowcaseService

router = APIRouter(prefix="/platform", tags=["enterprise platform"])
_service = ShowcaseService()
_presentation_exporter = JudgePresentationExporter()


def _repository_path(repository_id: str) -> Path:
    uploads_root = get_settings().upload_path.resolve()
    repository_path = (uploads_root / repository_id / "repository").resolve()
    if uploads_root not in repository_path.parents or not repository_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found"
        )
    return repository_path


@router.get("/overview/{repository_id}", response_model=EnterpriseOverview)
async def overview(repository_id: str) -> EnterpriseOverview:
    return await _service.overview(repository_id, _repository_path(repository_id))


@router.get("/readme/{repository_id}", response_model=ReadmeArtifact)
def readme(repository_id: str) -> ReadmeArtifact:
    return _service.readme(repository_id, _repository_path(repository_id))


@router.get("/architecture/{repository_id}", response_model=ArchitectureArtifact)
def architecture(repository_id: str) -> ArchitectureArtifact:
    return _service.architecture(repository_id, _repository_path(repository_id))


@router.get("/report/{repository_id}/pptx")
async def report_pptx(repository_id: str) -> Response:
    overview_result = await _service.overview(
        repository_id, _repository_path(repository_id)
    )
    return Response(
        _presentation_exporter.export(overview_result),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="reproproof-{repository_id}.pptx"'
        },
    )


@router.get("/report/{repository_id}/json")
async def report_json(repository_id: str) -> Response:
    overview_result = await _service.overview(
        repository_id, _repository_path(repository_id)
    )
    return Response(
        json.dumps(overview_result.model_dump(), indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="reproproof-{repository_id}.json"'
        },
    )


@router.get("/report/{repository_id}/markdown")
async def report_markdown(repository_id: str) -> Response:
    overview_result = await _service.overview(
        repository_id, _repository_path(repository_id)
    )
    content = (
        "# ReproProof Evaluation\n\n"
        + f"- Verdict: {overview_result.verdict}\n- Overall score: {overview_result.overall_score:.1f}/100\n- Confidence: {overview_result.confidence:.0%}\n\n## Scores\n\n"
        + "\n".join(
            f"- {name}: {score:.1f}/100"
            for name, score in overview_result.scores.items()
        )
    )
    return Response(
        content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="reproproof-{repository_id}.md"'
        },
    )


@router.get("/report/{repository_id}/csv")
async def report_csv(repository_id: str) -> Response:
    overview_result = await _service.overview(
        repository_id, _repository_path(repository_id)
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["metric", "value"])
    writer.writerow(["verdict", overview_result.verdict])
    writer.writerow(["overall_score", overview_result.overall_score])
    writer.writerow(["confidence", overview_result.confidence])
    writer.writerows(overview_result.scores.items())
    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="reproproof-{repository_id}.csv"'
        },
    )


@router.get("/report/{repository_id}/zip")
async def report_zip(repository_id: str) -> Response:
    overview_result = await _service.overview(
        repository_id, _repository_path(repository_id)
    )
    readme_result = _service.readme(repository_id, _repository_path(repository_id))
    architecture_result = _service.architecture(
        repository_id, _repository_path(repository_id)
    )
    markdown = (
        "# ReproProof Evaluation\n\n"
        + f"- Verdict: {overview_result.verdict}\n- Overall score: {overview_result.overall_score:.1f}/100\n- Confidence: {overview_result.confidence:.0%}\n"
    )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "report.json", json.dumps(overview_result.model_dump(), indent=2)
        )
        archive.writestr("report.md", markdown)
        archive.writestr("README.md", readme_result.content)
        archive.writestr("architecture.mmd", architecture_result.content)
    return Response(
        output.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="reproproof-{repository_id}.zip"'
        },
    )


@router.get("/report/{repository_id}/pdf")
def report_pdf(repository_id: str) -> Response:
    from app.api.routes import _final_report
    from app.services.verification_report_service import VerificationReportService

    report = _final_report(repository_id)
    return Response(
        VerificationReportService().pdf_bytes(report.markdown_report),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="reproproof-{repository_id}.pdf"'
        },
    )
