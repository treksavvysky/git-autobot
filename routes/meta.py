from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from models import MetaConfig
from models.status import StatusReport
from services.auth import verify_api_key
from services.config import get_settings
from services.health import generate_status_report

router = APIRouter(tags=["Meta"])


@router.get("/status", response_model=StatusReport, summary="Service health and status")
def get_status() -> StatusReport:
    """
    Provides a detailed status report of the service, including build
    information, environment details, and the health of its components.
    """
    return generate_status_report()


@router.options("/{full_path:path}", summary="CORS preflight handler")
def options_handler(full_path: str) -> Response:
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )


@router.get("/meta/config", response_model=MetaConfig, summary="Backend metadata", dependencies=[Depends(verify_api_key)])
def meta_config() -> MetaConfig:
    settings = get_settings()
    return MetaConfig(
        name="git-autobot-backend",
        version="0.1.0",
        allowed_origins=settings.allowed_origins,
    )
