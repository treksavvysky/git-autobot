from __future__ import annotations

import os
import platform
import shutil
import socket
import time
from datetime import datetime

from github import Github, GithubException

from models.status import (
    CheckResult,
    ComponentChecks,
    EnvironmentInfo,
    ServiceInfo,
    StatusReport,
)
from services.config import get_settings

# Global state to track service start time
START_TIME = time.time()


def get_service_info() -> ServiceInfo:
    """Gathers service metadata from environment variables."""
    build_time_str = os.getenv("BUILD_TIME")
    build_time = datetime.fromisoformat(build_time_str.replace("Z", "+00:00")) if build_time_str else None

    return ServiceInfo(
        service_name="git-autobot",
        app_version=os.getenv("APP_VERSION"),
        git_sha=os.getenv("GIT_SHA"),
        build_time=build_time,
        uptime=time.time() - START_TIME,
    )


def get_environment_info() -> EnvironmentInfo:
    """Gathers information about the runtime environment."""
    return EnvironmentInfo(
        python_version=platform.python_version(),
        platform=platform.platform(),
        container_id=os.getenv("HOSTNAME"),  # In Docker, HOSTNAME is the container ID
    )


def check_github_api() -> CheckResult:
    """Checks GitHub API connectivity and rate limits."""
    settings = get_settings()
    if not settings.github_token:
        return CheckResult(status="degraded", details={"error": "GITHUB_TOKEN not configured"})

    try:
        client = Github(settings.github_token, base_url=settings.github_api_base)
        client.get_user().login
        rate_limit = client.get_rate_limit().core
        return CheckResult(
            status="healthy",
            details={
                "authenticated": True,
                "rate_limit_remaining": rate_limit.remaining,
                "rate_limit_limit": rate_limit.limit,
                "rate_limit_reset": datetime.fromtimestamp(rate_limit.reset).isoformat(),
            },
        )
    except GithubException as e:
        return CheckResult(
            status="unhealthy",
            details={"error": "Failed to connect to GitHub API", "message": str(e)},
        )


def check_gitpython() -> CheckResult:
    """Checks if GitPython is installed and git executable is available."""
    try:
        import git
        # Check if git executable is available without creating a repo
        git.Git().version()
        return CheckResult(status="healthy", details={"version": git.__version__})
    except (ImportError, git.exc.GitCommandError) as e:
        return CheckResult(status="unhealthy", details={"error": str(e)})


def check_workspace() -> CheckResult:
    """Checks workspace directory permissions and disk space."""
    settings = get_settings()
    workspace_dir = settings.local_repos_dir
    try:
        if not workspace_dir.exists():
            return CheckResult(status="unhealthy", details={"error": f"Workspace directory does not exist: {workspace_dir}"})
        if not os.access(workspace_dir, os.R_OK | os.W_OK):
            return CheckResult(status="unhealthy", details={"error": f"Workspace is not readable/writable: {workspace_dir}"})

        disk_usage = shutil.disk_usage(workspace_dir)
        return CheckResult(
            status="healthy",
            details={
                "path": str(workspace_dir),
                "permissions": "RW",
                "disk_free_bytes": disk_usage.free,
                "disk_total_bytes": disk_usage.total,
            },
        )
    except Exception as e:
        return CheckResult(status="unhealthy", details={"error": str(e)})


def check_queue() -> CheckResult:
    """Checks the status of the task queue."""
    return CheckResult(status="degraded", details={"status": "unavailable"})


def check_network() -> CheckResult:
    """Checks DNS resolution for critical external services."""
    try:
        socket.gethostbyname("api.github.com")
        return CheckResult(status="healthy", details={"dns_resolution": "ok"})
    except socket.gaierror as e:
        return CheckResult(status="unhealthy", details={"error": str(e)})


def get_component_checks() -> ComponentChecks:
    """Performs all component health checks in parallel."""
    return ComponentChecks(
        github_api=check_github_api(),
        gitpython=check_gitpython(),
        workspace=check_workspace(),
        queue=check_queue(),
        network=check_network(),
    )


def get_overall_status(checks: ComponentChecks) -> str:
    """Aggregates individual check results into an overall status."""
    statuses = [
        checks.github_api.status,
        checks.gitpython.status,
        checks.workspace.status,
        checks.network.status,
    ]
    if "unhealthy" in statuses:
        return "unhealthy"
    if "degraded" in statuses:
        return "degraded"
    return "healthy"


def generate_status_report() -> StatusReport:
    """Generates the full status report."""
    service_info = get_service_info()
    env_info = get_environment_info()
    component_checks = get_component_checks()
    overall_status = get_overall_status(component_checks)

    return StatusReport(
        overall_status=overall_status,
        service=service_info,
        env=env_info,
        checks=component_checks,
    )