from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query

from models import (
    CheckoutRequestBody,
    CherryPickRequestBody,
    CloneRepositoryRequest,
    CommitRequestBody,
    GitCommandResult,
    GitDiffSummary,
    GitFileResponse,
    GitLogResponse,
    GitStatus,
    GitStatusFile,
    LocalRepository,
    LocalRepositoryDetail,
    PullRequestBody,
    PushRequestBody,
    ResetRequestBody,
    StashRequestBody,
    StubResponse,
)
from services import git_service

router = APIRouter(prefix="/local/repos", tags=["Local Repositories"])


@router.get("", response_model=List[LocalRepository], summary="List local repositories")
def list_local_repositories() -> List[LocalRepository]:
    return git_service.list_local_repositories()


@router.get(
    "/{name}",
    response_model=LocalRepositoryDetail,
    summary="Get local repository details",
)
def local_repository(name: str) -> LocalRepositoryDetail:
    return git_service.get_local_repository(name)


@router.post(
    "/{name}/clone",
    response_model=StubResponse,
    summary="Clone repository locally (stub)",
)
def clone_repository(name: str, payload: CloneRepositoryRequest) -> StubResponse:
    return git_service.clone_repository(name, payload)


@router.get(
    "/{name}/status",
    response_model=GitStatus,
    summary="Get local git status",
)
def local_status(name: str) -> GitStatus:
    return git_service.get_status(name)


@router.post(
    "/{name}/pull",
    response_model=StubResponse,
    summary="Pull latest changes (stub)",
)
def local_pull(name: str, payload: PullRequestBody) -> StubResponse:
    return git_service.pull_repository(name, payload.rebase)


@router.post(
    "/{name}/push",
    response_model=StubResponse,
    summary="Push local changes (stub)",
)
def local_push(name: str, payload: PushRequestBody) -> StubResponse:
    return git_service.push_repository(name, payload)


@router.post(
    "/{name}/stash",
    response_model=GitCommandResult,
    summary="Run git stash (stub)",
)
def local_stash(name: str, payload: StashRequestBody) -> GitCommandResult:
    return git_service.stash_operation(name, payload)


@router.post(
    "/{name}/commit",
    response_model=GitCommandResult,
    summary="Commit changes (stub)",
)
def local_commit(name: str, payload: CommitRequestBody) -> GitCommandResult:
    return git_service.commit_changes(name, payload)


@router.post(
    "/{name}/checkout",
    response_model=GitCommandResult,
    summary="Checkout branch (stub)",
)
def local_checkout(name: str, payload: CheckoutRequestBody) -> GitCommandResult:
    return git_service.checkout_branch(name, payload.branch, payload.create)


@router.post(
    "/{name}/reset",
    response_model=GitCommandResult,
    summary="Reset repository (stub)",
)
def local_reset(name: str, payload: ResetRequestBody) -> GitCommandResult:
    return git_service.reset_repository(name, payload)


@router.post(
    "/{name}/cherry-pick",
    response_model=GitCommandResult,
    summary="Cherry-pick commits (stub)",
)
def local_cherry_pick(name: str, payload: CherryPickRequestBody) -> GitCommandResult:
    return git_service.cherry_pick(name, payload)


@router.get(
    "/{name}/log",
    response_model=GitLogResponse,
    summary="Get git log",
)
def local_log(
    name: str,
    limit: int = Query(default=50, ge=1, le=200),
    author: Optional[str] = Query(default=None),
) -> GitLogResponse:
    return git_service.get_log(name, limit=limit, author=author)


@router.get(
    "/{name}/diff",
    response_model=GitDiffSummary,
    summary="Get git diff",
)
def local_diff(
    name: str,
    target: str = Query(default="HEAD"),
    mode: str = Query(default="summary", pattern="^(summary|patch)$"),
) -> GitDiffSummary:
    return git_service.get_diff(name, target=target, mode=mode)


@router.get(
    "/{name}/staged",
    response_model=List[GitStatusFile],
    summary="List staged changes",
)
def local_staged(name: str) -> List[GitStatusFile]:
    return git_service.get_staged(name)


@router.get(
    "/{name}/file/{path:path}",
    response_model=GitFileResponse,
    summary="Read file content at ref",
)
def local_file(name: str, path: str, ref: str = Query(default="HEAD")) -> GitFileResponse:
    return git_service.read_file(name, path, ref=ref)
