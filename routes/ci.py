from __future__ import annotations

from fastapi import APIRouter

from models import CIJob, CIStatusResponse, CoverageReport, DockerStatus, HealthStatusResponse
from services import ci_service

router = APIRouter(prefix="/repos/{name}", tags=["CI & Health"])


@router.get(
    "/ci/actions/latest",
    response_model=CIJob,
    summary="Get latest GitHub Actions job (stub)",
)
def latest_action(name: str) -> CIJob:
    return ci_service.get_latest_action(name)


@router.get(
    "/ci/actions/runs",
    response_model=CIStatusResponse,
    summary="List recent CI runs (stub)",
)
def action_runs(name: str) -> CIStatusResponse:
    return ci_service.get_action_runs(name)


@router.get(
    "/ci/coverage",
    response_model=CoverageReport,
    summary="Get code coverage summary (stub)",
)
def coverage(name: str) -> CoverageReport:
    return ci_service.get_coverage(name)


@router.get(
    "/ci/docker",
    response_model=DockerStatus,
    summary="Get docker image status (stub)",
)
def docker_status(name: str) -> DockerStatus:
    return ci_service.get_docker_status(name)


@router.get(
    "/health",
    response_model=HealthStatusResponse,
    summary="Get aggregated repository health (stub)",
)
def health(name: str) -> HealthStatusResponse:
    return ci_service.get_health(name)
