from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ServiceInfo(BaseModel):
    """Build and runtime metadata for the service."""
    service_name: str = Field(..., description="Name of the service.")
    app_version: Optional[str] = Field(None, description="Application version (e.g., git tag/release).")
    git_sha: Optional[str] = Field(None, description="Git commit SHA of the build.")
    build_time: Optional[datetime] = Field(None, description="Time of the application build (UTC).")
    uptime: float = Field(..., description="Service uptime in seconds.")


class EnvironmentInfo(BaseModel):
    """Host environment details."""
    python_version: str = Field(..., description="Python runtime version.")
    platform: str = Field(..., description="Operating system platform.")
    container_id: Optional[str] = Field(None, description="Container ID, if running in Docker.")


class CheckResult(BaseModel):
    """Result of a single health check component."""
    status: Literal["healthy", "degraded", "unhealthy"]
    details: dict = Field(..., description="Supporting details for the check status.")


class ComponentChecks(BaseModel):
    """Collection of individual component health checks."""
    github_api: CheckResult
    gitpython: CheckResult
    workspace: CheckResult
    queue: CheckResult
    network: CheckResult


class StatusReport(BaseModel):
    """Comprehensive status report for the service."""
    overall_status: Literal["healthy", "degraded", "unhealthy"]
    service: ServiceInfo
    env: EnvironmentInfo
    checks: ComponentChecks