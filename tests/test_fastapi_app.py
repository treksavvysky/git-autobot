from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi_app import app
import fastapi_app
import os


def test_list_repositories_returns_repo_list():
    client = TestClient(app)

    mock_repo = MagicMock()
    mock_repo.name = "repo1"
    mock_repo.description = "A repo"
    mock_repo.private = False
    mock_repo.default_branch = "main"

    mock_user = MagicMock()
    mock_user.get_repos.return_value = [mock_repo]

    with patch("fastapi_app.Github") as MockGithub, \
         patch("services.auth.os.getenv", return_value="test_api_key"):
        instance = MockGithub.return_value
        instance.get_user.return_value = mock_user
        response = client.get("/repos", params={"token": "fake"}, headers={"X-API-Key": "test_api_key"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "name": "repo1",
            "description": "A repo",
            "visibility": "public",
            "default_branch": "main",
        }
    ]


def test_get_repository_details():
    client = TestClient(app)

    mock_repo = MagicMock()
    mock_repo.name = "repo1"
    mock_repo.description = "A repo"
    mock_repo.private = False
    mock_repo.default_branch = "main"
    mock_repo.html_url = "https://github.com/user/repo1"

    branch_main = MagicMock()
    branch_main.name = "main"
    branch_dev = MagicMock()
    branch_dev.name = "dev"
    mock_repo.get_branches.return_value = [branch_main, branch_dev]

    commit = MagicMock()
    commit.sha = "abc123"
    commit.commit = MagicMock()
    commit.commit.message = "init"
    commit.commit.author = MagicMock()
    commit.commit.author.name = "author"
    commit.commit.author.date = "2024-01-01"
    mock_repo.get_commits.return_value = [commit]

    contributor = MagicMock()
    contributor.login = "contrib"
    mock_repo.get_contributors.return_value = [contributor]

    mock_user = MagicMock()
    mock_user.get_repo.return_value = mock_repo

    with patch("fastapi_app.Github") as MockGithub, \
         patch("services.auth.os.getenv", return_value="test_api_key"):
        instance = MockGithub.return_value
        instance.get_user.return_value = mock_user
        response = client.get("/repos/repo1", params={"token": "fake"}, headers={"X-API-Key": "test_api_key"})

    assert response.status_code == 200
    assert response.json() == {
        "name": "repo1",
        "description": "A repo",
        "visibility": "public",
        "default_branch": "main",
        "branches": ["main", "dev"],
        "last_commit": {
            "sha": "abc123",
            "message": "init",
            "author": "author",
            "date": "2024-01-01",
        },
        "contributors": ["contrib"],
        "html_url": "https://github.com/user/repo1",
    }


def test_get_repository_readme():
    client = TestClient(app)

    readme = MagicMock()
    readme.decoded_content = b"# Title"

    mock_repo = MagicMock()
    mock_repo.get_readme.return_value = readme

    mock_user = MagicMock()
    mock_user.get_repo.return_value = mock_repo

    with patch("fastapi_app.Github") as MockGithub, \
         patch("services.auth.os.getenv", return_value="test_api_key"):
        instance = MockGithub.return_value
        instance.get_user.return_value = mock_user
        response = client.get("/repos/repo1/readme", params={"token": "fake"}, headers={"X-API-Key": "test_api_key"})

    assert response.status_code == 200
    assert response.json() == {"content": "# Title"}


def test_list_local_repositories(tmp_path):
    client = TestClient(app)

    repo_dir = tmp_path / "repo1"
    (repo_dir / ".git").mkdir(parents=True)

    # Patch LOCAL_REPOS_DIR to our temporary path
    original_path = fastapi_app.LOCAL_REPOS_DIR
    fastapi_app.LOCAL_REPOS_DIR = tmp_path

    with patch("services.auth.os.getenv", return_value="test_api_key"):
        response = client.get("/local/repos", headers={"X-API-Key": "test_api_key"})

    assert response.status_code == 200
    assert response.json() == [
        {"name": "repo1", "path": str(repo_dir)}
    ]

    # restore
    fastapi_app.LOCAL_REPOS_DIR = original_path

