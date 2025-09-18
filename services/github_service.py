from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from fastapi import HTTPException, Query
from github import Github, GithubException

from models import (
    Branch,
    BranchCreateRequest,
    CommitMetadata,
    IssueModel,
    PullRequestCreateBody,
    PullRequestCreateResponse,
    PullRequestModel,
    RecurringTask,
    RecurringTaskCreateBody,
    Repository,
    RepositoryDetails,
    SyncStatus,
)
from services.config import get_settings


def _raise_github_error(exc: GithubException) -> None:
    status = getattr(exc, "status", 500) or 500
    data = getattr(exc, "data", {}) or {}
    message = data.get("message", str(exc))
    raise HTTPException(
        status_code=status,
        detail={
            "error": {
                "code": "github_error",
                "message": message,
                "details": {"status": status},
            }
        },
    ) from exc


def get_github_client(
    token: Optional[str] = Query(
        default=None,
        description=(
            "GitHub personal access token. If omitted the backend will fall back "
            "to the configured GITHUB_TOKEN environment variable."
        ),
    )
) -> Github:
    """FastAPI dependency that resolves the Github client."""

    settings = get_settings()
    resolved_token = token or settings.github_token
    if not resolved_token:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "missing_token",
                    "message": "GitHub token required for this endpoint.",
                    "details": {},
                }
            },
        )
    from fastapi_app import Github as GithubFactory

    return GithubFactory(resolved_token, base_url=settings.github_api_base)


def list_repositories(client: Github) -> List[Repository]:
    try:
        user = client.get_user()
        repos: List[Repository] = []
        for repo in user.get_repos():
            repos.append(
                Repository(
                    name=repo.name,
                    description=repo.description,
                    visibility="private" if repo.private else "public",
                    default_branch=repo.default_branch,
                )
            )
        return repos
    except GithubException as exc:
        _raise_github_error(exc)


def get_repository_details(client: Github, name: str) -> RepositoryDetails:
    try:
        repo = client.get_user().get_repo(name)
        branches = [branch.name for branch in repo.get_branches()]
        try:
            commit_obj = repo.get_commits()[0]
            author = getattr(commit_obj.commit.author, "name", None)
            date_value = getattr(commit_obj.commit.author, "date", None)
            if isinstance(date_value, datetime):
                date_repr = date_value.isoformat()
            elif date_value is not None:
                date_repr = str(date_value)
            else:
                date_repr = None
            last_commit = CommitMetadata(
                sha=commit_obj.sha,
                message=commit_obj.commit.message,
                author=author,
                date=date_repr,
            )
        except Exception:
            last_commit = None
        contributors = [contributor.login for contributor in repo.get_contributors()]
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
    except GithubException as exc:
        _raise_github_error(exc)


def get_repository_readme(client: Github, name: str) -> str:
    try:
        repo = client.get_user().get_repo(name)
        readme = repo.get_readme()
        return readme.decoded_content.decode("utf-8")
    except GithubException as exc:
        _raise_github_error(exc)


def get_repository_readme_rendered(client: Github, name: str) -> str:
    """Return rendered README HTML.

    Rendering is stubbed until a markdown renderer is introduced. For now we
    return the raw content and mark the payload as stubbed at the router layer.
    """

    return get_repository_readme(client, name)


def get_repository_branches(client: Github, name: str) -> List[Branch]:
    try:
        repo = client.get_user().get_repo(name)
        default_branch = repo.default_branch
        branches: List[Branch] = []
        for branch in repo.get_branches():
            branches.append(
                Branch(
                    name=branch.name,
                    default=branch.name == default_branch,
                    protected=getattr(branch, "protected", False),
                )
            )
        return branches
    except GithubException as exc:
        _raise_github_error(exc)


def get_repository_commits(client: Github, name: str, limit: int = 50) -> List[CommitMetadata]:
    try:
        repo = client.get_user().get_repo(name)
        commits: List[CommitMetadata] = []
        for commit in repo.get_commits()[:limit]:
            date_obj = getattr(commit.commit.author, "date", None)
            date_str = date_obj.isoformat() if date_obj else None
            commits.append(
                CommitMetadata(
                    sha=commit.sha,
                    message=commit.commit.message,
                    author=getattr(commit.commit.author, "name", None),
                    date=date_str,
                )
            )
        return commits
    except GithubException as exc:
        _raise_github_error(exc)


def create_branch(client: Github, name: str, payload: BranchCreateRequest) -> Branch:
    """Create a new branch from the requested base.

    Creation is stubbed for now to avoid mutating remote state without
    additional safeguards.
    """

    return Branch(name=payload.name, default=False, protected=False)


def delete_branch(client: Github, name: str, branch: str) -> None:
    """Delete a branch on the remote repository.

    Branch deletion is intentionally stubbed to avoid destructive operations in
    the starter project. The router returns a stub payload to the client.
    """

    return None


def get_pull_requests(client: Github, name: str) -> List[PullRequestModel]:
    try:
        repo = client.get_user().get_repo(name)
        pulls: List[PullRequestModel] = []
        for pull in repo.get_pulls(state="open"):
            pulls.append(
                PullRequestModel(
                    id=pull.id,
                    number=pull.number,
                    title=pull.title,
                    state=pull.state,
                    head=pull.head.ref,
                    base=pull.base.ref,
                    url=pull.html_url,
                )
            )
        return pulls
    except GithubException as exc:
        _raise_github_error(exc)


def create_pull_request(
    client: Github, name: str, payload: PullRequestCreateBody
) -> PullRequestCreateResponse:
    """Stub for PR creation; returns payload for debugging."""

    return PullRequestCreateResponse(
        request=payload,
        note=(
            "PR creation is stubbed. Integrate with GitHub's create_pull request "
            "API when ready."
        ),
    )


def prune_stale_branches(client: Github, name: str, branch: str) -> SyncStatus:
    """Return a stub sync status indicating the action is pending implementation."""

    return SyncStatus(ahead=0, behind=0, status="synced")


def get_repository_graph(client: Github, name: str, limit: int = 20) -> List[dict]:
    try:
        repo = client.get_user().get_repo(name)
        nodes: List[dict] = []
        for commit in repo.get_commits()[:limit]:
            nodes.append(
                {
                    "sha": commit.sha,
                    "parents": [parent.sha for parent in commit.parents],
                    "message": commit.commit.message,
                    "author": getattr(commit.commit.author, "name", None),
                    "date": getattr(commit.commit.author, "date", None),
                }
            )
        return nodes
    except GithubException as exc:
        _raise_github_error(exc)


def get_repository_sync_status(client: Github, name: str) -> SyncStatus:
    """Return a stub sync status while local/remote comparison is wired."""

    return SyncStatus(ahead=0, behind=0, status="synced")


def get_repository_issues(
    client: Github,
    name: str,
    assignee: Optional[str] = None,
    labels: Optional[str] = None,
    state: str = "open",
) -> List[IssueModel]:
    try:
        repo = client.get_user().get_repo(name)
        
        # Build parameters conditionally to avoid passing None values
        params = {"state": state}
        if assignee is not None:
            params["assignee"] = assignee
        if labels is not None:
            params["labels"] = labels.split(",")
            
        issues: Iterable = repo.get_issues(**params)
        results: List[IssueModel] = []
        for issue in issues:
            if issue.pull_request is not None:
                # Skip pull-request pseudo issues.
                continue
            results.append(
                IssueModel(
                    id=issue.id,
                    number=issue.number,
                    title=issue.title,
                    state="closed" if issue.state == "closed" else "open",
                    labels=[label.name for label in issue.labels],
                    assignee=getattr(issue.assignee, "login", None),
                    url=issue.html_url,
                )
            )
        return results
    except GithubException as exc:
        _raise_github_error(exc)


def list_recurring_tasks(_: Github, __: str) -> List[RecurringTask]:
    """Recurring tasks are maintained locally; return an empty list placeholder."""

    return []


def create_recurring_task(
    _: Github, __: str, payload: RecurringTaskCreateBody
) -> RecurringTask:
    """Create a stub recurring task."""

    now = datetime.utcnow()
    return RecurringTask(
        id=f"stub-{int(now.timestamp())}",
        name=payload.name,
        schedule=payload.schedule,
        enabled=True,
        last_run=None,
    )
