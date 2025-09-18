from __future__ import annotations

from fastapi import APIRouter, Depends

from models import Branch, BranchCreateRequest, BranchDeleteResponse, SyncStatus
from services import github_service

router = APIRouter(prefix="/repos/{name}/branches", tags=["Branches"])


@router.post("/", response_model=Branch, summary="Create a branch (stub)")
def create_branch(
    name: str,
    payload: BranchCreateRequest,
    client=Depends(github_service.get_github_client),
) -> Branch:
    return github_service.create_branch(client, name, payload)


@router.delete(
    "/{branch}",
    response_model=BranchDeleteResponse,
    summary="Delete a branch (stub)",
)
def delete_branch(
    name: str,
    branch: str,
    client=Depends(github_service.get_github_client),
) -> BranchDeleteResponse:
    github_service.delete_branch(client, name, branch)
    return BranchDeleteResponse()


@router.post(
    "/{branch}/prune-stale",
    response_model=SyncStatus,
    summary="Prune stale local branches (stub)",
)
def prune_stale(
    name: str,
    branch: str,
    client=Depends(github_service.get_github_client),
) -> SyncStatus:
    return github_service.prune_stale_branches(client, name, branch)
