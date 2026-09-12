from __future__ import annotations

from fastapi import APIRouter

from app.demo import DEMO_REPOSITORY_ID, demo_overview, demo_report

router = APIRouter(prefix="/demo", tags=["demo mode"])


@router.get("/repositories")
def repositories() -> list[dict[str, str]]:
    return [
        {
            "id": DEMO_REPOSITORY_ID,
            "name": "ReproProof reference repository",
            "description": "Curated credential-free judging scenario",
        }
    ]


@router.get("/datasets")
def datasets() -> list[dict[str, str]]:
    return [
        {
            "id": "demo-dataset",
            "name": "reproducibility_metrics.csv",
            "description": "Synthetic experiment metrics for the demonstration",
        }
    ]


@router.get("/papers")
def papers() -> list[dict[str, str]]:
    return [
        {
            "id": "demo-paper",
            "name": "Reproducible AI Systems - Sample Paper",
            "description": "Synthetic paper metadata for the research workflow",
        }
    ]


@router.post("/run")
def run() -> dict[str, object]:
    return {
        "demo_id": DEMO_REPOSITORY_ID,
        "status": "completed",
        "overview": demo_overview().model_dump(),
        "report": demo_report(),
    }


@router.get("/overview")
def overview() -> dict[str, object]:
    return demo_overview().model_dump()


@router.get("/report")
def report() -> dict[str, object]:
    return demo_report()
