from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi_app import app


def test_list_repositories_returns_repo_list():
    client = TestClient(app)
    mock_repo = MagicMock()
    mock_repo.name = "repo1"
    mock_repo.full_name = "user/repo1"
    mock_repo.html_url = "https://github.com/user/repo1"

    mock_user = MagicMock()
    mock_user.get_repos.return_value = [mock_repo]

    with patch("fastapi_app.Github") as MockGithub:
        instance = MockGithub.return_value
        instance.get_user.return_value = mock_user

        response = client.get("/repos", params={"token": "fake"})

    assert response.status_code == 200
    assert response.json() == [{
        "name": "repo1",
        "full_name": "user/repo1",
        "html_url": "https://github.com/user/repo1"
    }]
