from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from models import CIJob, CIStatusResponse, CoverageReport, DockerStatus, HealthCheck, HealthStatusResponse


def get_latest_action(repo: str) -> CIJob:
    now = datetime.utcnow()
    return CIJob(
        id=f"latest-{repo}",
        name="build-and-test",
        status="success",
        url=f"https://github.com/example/{repo}/actions/runs/1",
        started_at=now - timedelta(minutes=5),
        completed_at=now,
    )


def get_action_runs(repo: str) -> CIStatusResponse:
    now = datetime.utcnow()
    jobs: List[CIJob] = [
        CIJob(
            id=f"run-{idx}",
            name="build-and-test",
            status="success" if idx % 2 == 0 else "failure",
            url=f"https://github.com/example/{repo}/actions/runs/{idx}",
            started_at=now - timedelta(hours=idx + 1),
            completed_at=now - timedelta(hours=idx + 1, minutes=-15),
        )
        for idx in range(1, 4)
    ]
    return CIStatusResponse(jobs=jobs)


def get_coverage(repo: str) -> CoverageReport:
    return CoverageReport(
        coverage=87.5,
        generated_at=datetime.utcnow(),
        note="Stub coverage data. Replace with real reporting pipeline.",
    )


def get_docker_status(repo: str) -> DockerStatus:
    return DockerStatus(
        tag="latest",
        published_at=datetime.utcnow() - timedelta(days=1),
        digest="sha256:stubdigest",
    )


def get_health(repo: str) -> HealthStatusResponse:
    checks = [
        HealthCheck(
            name="ci_pipeline",
            status="ok",
            details={"note": "CI pipeline passing in last stub run."},
        ),
        HealthCheck(
            name="dependencies",
            status="warn",
            details={"note": "Dependency audit stub indicates updates needed."},
        ),
    ]
    return HealthStatusResponse(status="warn", checks=checks)
