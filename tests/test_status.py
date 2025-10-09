from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from fastapi_app import app
from models.status import CheckResult, ComponentChecks

client = TestClient(app)


def test_status_healthy():
    """Test the /status endpoint when all checks are healthy."""
    with patch("services.health.get_component_checks") as mock_get_checks:
        mock_get_checks.return_value = ComponentChecks(
            github_api=CheckResult(status="healthy", details={}),
            gitpython=CheckResult(status="healthy", details={}),
            workspace=CheckResult(status="healthy", details={}),
            queue=CheckResult(status="degraded", details={"status": "unavailable"}),
            network=CheckResult(status="healthy", details={}),
        )

        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "healthy"
        assert data["checks"]["github_api"]["status"] == "healthy"


def test_status_degraded():
    """Test the /status endpoint when a non-critical check is degraded."""
    with patch("services.health.get_component_checks") as mock_get_checks:
        mock_get_checks.return_value = ComponentChecks(
            github_api=CheckResult(status="degraded", details={"error": "GITHUB_TOKEN not configured"}),
            gitpython=CheckResult(status="healthy", details={}),
            workspace=CheckResult(status="healthy", details={}),
            queue=CheckResult(status="degraded", details={"status": "unavailable"}),
            network=CheckResult(status="healthy", details={}),
        )

        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "degraded"
        assert data["checks"]["github_api"]["status"] == "degraded"


def test_status_unhealthy():
    """Test the /status endpoint when a critical check is unhealthy."""
    with patch("services.health.get_component_checks") as mock_get_checks:
        mock_get_checks.return_value = ComponentChecks(
            github_api=CheckResult(status="healthy", details={}),
            gitpython=CheckResult(status="unhealthy", details={"error": "git command not found"}),
            workspace=CheckResult(status="healthy", details={}),
            queue=CheckResult(status="degraded", details={"status": "unavailable"}),
            network=CheckResult(status="healthy", details={}),
        )

        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "unhealthy"
        assert data["checks"]["gitpython"]["status"] == "unhealthy"