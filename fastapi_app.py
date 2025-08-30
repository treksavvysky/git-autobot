from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from github import Github, GithubException
from pydantic import BaseModel
from pathlib import Path
import os


class Repository(BaseModel):
    """Basic repository information returned from the GitHub API."""

    name: str
    description: Optional[str]
    visibility: str
    default_branch: str


class CommitMetadata(BaseModel):
    """Metadata about a commit."""

    sha: str
    message: str
    author: Optional[str]
    date: Optional[str]


class RepositoryDetails(BaseModel):
    """Detailed repository information."""

    name: str
    description: Optional[str]
    visibility: str
    default_branch: str
    branches: List[str]
    last_commit: Optional[CommitMetadata]
    contributors: List[str]
    html_url: str


class ReadmeResponse(BaseModel):
    """README content."""

    content: str


class LocalRepository(BaseModel):
    """Information about a locally cloned repository."""

    name: str
    path: str


app = FastAPI(title="Git Autobot GitHub API")


def get_github_client(
    token: Optional[str] = Query(default=None, description="GitHub personal access token")
) -> Github:
    token = token or os.getenv("GITHUB_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="GitHub token required")
    return Github(token)


BASE_DIR = Path(__file__).resolve().parent
LOCAL_REPOS_DIR = Path(os.getenv("LOCAL_REPOS_DIR", BASE_DIR.parent / "local_repos")).resolve()
LOCAL_REPOS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/repos", response_model=List[Repository], summary="List user repositories")
def list_repositories(gh: Github = Depends(get_github_client)) -> List[Repository]:
    try:
        user = gh.get_user()
        repos = [
            Repository(
                name=r.name,
                description=r.description,
                visibility="private" if r.private else "public",
                default_branch=r.default_branch,
            )
            for r in user.get_repos()
        ]
        return repos
    except GithubException as e:
        status = getattr(e, "status", 500)
        message = getattr(e, "data", {}).get("message") if hasattr(e, "data") else str(e)
        raise HTTPException(status_code=status, detail=message)


@app.get("/repos/{name}", response_model=RepositoryDetails, summary="Get repository details")
def get_repository_details(name: str, gh: Github = Depends(get_github_client)) -> RepositoryDetails:
    try:
        repo = gh.get_user().get_repo(name)

        branches = [b.name for b in repo.get_branches()]

        try:
            commit_obj = repo.get_commits()[0]
            last_commit = CommitMetadata(
                sha=commit_obj.sha,
                message=commit_obj.commit.message,
                author=getattr(commit_obj.commit.author, "name", None),
                date=str(getattr(commit_obj.commit.author, "date", None)),
            )
        except Exception:
            last_commit = None

        contributors = [c.login for c in repo.get_contributors()]

        return RepositoryDetails(
            name=repo.name,
            description=repo.description,
            visibility="private" if repo.private else "public",
            default_branch=repo.default_branch,
            branches=branches,
            last_commit=last_commit,
            contributors=contributors,
            html_url=repo.html_url,
        )
    except GithubException as e:
        status = getattr(e, "status", 500)
        message = getattr(e, "data", {}).get("message") if hasattr(e, "data") else str(e)
        raise HTTPException(status_code=status, detail=message)


@app.get("/repos/{name}/readme", response_model=ReadmeResponse, summary="Get repository README")
def get_repository_readme(name: str, gh: Github = Depends(get_github_client)) -> ReadmeResponse:
    try:
        repo = gh.get_user().get_repo(name)
        readme = repo.get_readme()
        content = readme.decoded_content.decode("utf-8")
        return ReadmeResponse(content=content)
    except GithubException as e:
        status = getattr(e, "status", 500)
        if status == 404:
            raise HTTPException(status_code=404, detail="README not found")
        message = getattr(e, "data", {}).get("message") if hasattr(e, "data") else str(e)
        raise HTTPException(status_code=status, detail=message)


@app.get("/local/repos", response_model=List[LocalRepository], summary="List local repositories")
def list_local_repositories() -> List[LocalRepository]:
    repos: List[LocalRepository] = []
    if LOCAL_REPOS_DIR.exists():
        for item in LOCAL_REPOS_DIR.iterdir():
            if item.is_dir() and (item / ".git").exists():
                repos.append(LocalRepository(name=item.name, path=str(item)))
    return repos

