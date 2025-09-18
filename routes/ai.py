from __future__ import annotations

from fastapi import APIRouter

from models import AIDailyBrief, AIExplainErrorRequest, AINextStepRequest, AIResponse
from services import ai_service

router = APIRouter(prefix="/repos/{name}/ai", tags=["AI Assist"])


@router.post(
    "/explain-error",
    response_model=AIResponse,
    summary="Explain an error (stub)",
)
def explain_error(name: str, payload: AIExplainErrorRequest) -> AIResponse:
    return ai_service.explain_error(name, payload)


@router.post(
    "/next-step",
    response_model=AIResponse,
    summary="Suggest next step (stub)",
)
def next_step(name: str, payload: AINextStepRequest) -> AIResponse:
    return ai_service.next_step(name, payload)


@router.get(
    "/daily-brief",
    response_model=AIDailyBrief,
    summary="Daily brief (stub)",
)
def daily_brief(name: str) -> AIDailyBrief:
    return ai_service.daily_brief(name)
