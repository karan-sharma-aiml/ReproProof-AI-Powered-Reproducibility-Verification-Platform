from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.research.errors import ProviderUnavailableError
from app.research.models import (
    PaperAnalysis,
    PaperAnalysisRequest,
    ProviderAnalysis,
    ResearchQuestionRequest,
)
from app.research.paper_engine import (
    PaperUnderstandingEngine,
    ProviderResearchEngine,
    ResearchAssistant,
)

router = APIRouter(prefix="/research/paper", tags=["research paper intelligence"])
_paper_engine = PaperUnderstandingEngine()


def _approved_path(path: str) -> Path:
    candidate = Path(path).resolve()
    uploads_root = get_settings().upload_path.resolve()
    if uploads_root not in candidate.parents or not candidate.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found in configured uploads",
        )
    return candidate


@router.post("/analyze", response_model=PaperAnalysis)
async def analyze_paper(request: PaperAnalysisRequest) -> PaperAnalysis:
    return await _paper_engine.analyze(_approved_path(request.path))


@router.post("/capability/{capability}", response_model=ProviderAnalysis)
async def run_paper_capability(
    capability: str, request: PaperAnalysisRequest
) -> ProviderAnalysis:
    analysis = await _paper_engine.analyze(_approved_path(request.path))
    try:
        return await ProviderResearchEngine().run(capability, analysis)
    except ProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.post("/assistant", response_model=dict[str, str])
async def ask_research_assistant(request: ResearchQuestionRequest) -> dict[str, str]:
    try:
        answer = await ResearchAssistant().ask(request.question)
    except ProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return {"question": request.question, "answer": answer}
