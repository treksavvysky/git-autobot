from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query

from models import (
    Branch,
    CommitMetadata,
    GraphResponse,
    ReadmeResponse,
    RenderedReadmeResponse,
    Repository,
    RepositoryDetails,
    SyncStatus,
)
from services import github_service

router = APIRouter(prefix="/repos", tags=["Repositories"])


@router.get("", response_model=List[Repository], summary="List repositories")
def list_repositories(client=Depends(github_service.get_github_client)) -> List[Repository]:
    return github_service.list_repositories(client)


@router.get(
    "/{name}",
    response_model=RepositoryDetails,
    summary="Get repository details",
)
def repository_details(
    name: str, client=Depends(github_service.get_github_client)
) -> RepositoryDetails:
    return github_service.get_repository_details(client, name)


@router.get(
    "/{name}/readme",
    response_model=ReadmeResponse,
    summary="Retrieve repository README (raw)",
)
def repository_readme(
    name: str, client=Depends(github_service.get_github_client)
) -> ReadmeResponse:
    content = github_service.get_repository_readme(client, name)
    return ReadmeResponse(content=content)


@router.get(
    "/{name}/readme/rendered",
    response_model=RenderedReadmeResponse,
    summary="Retrieve README rendered as HTML",
)
def repository_readme_rendered(
    name: str, client=Depends(github_service.get_github_client)
) -> RenderedReadmeResponse:
    content = github_service.get_repository_readme_rendered(client, name)
    return RenderedReadmeResponse(
        html=content,
        source_encoding="utf-8",
    )


@router.get(
    "/{name}/sync-status",
    response_model=SyncStatus,
    summary="Get repository sync status",
)
def repository_sync_status(
    name: str, client=Depends(github_service.get_github_client)
) -> SyncStatus:
    return github_service.get_repository_sync_status(client, name)


@router.get(
    "/{name}/branches",
    response_model=List[Branch],
    summary="List repository branches",
)
def repository_branches(
    name: str, client=Depends(github_service.get_github_client)
) -> List[Branch]:
    return github_service.get_repository_branches(client, name)


@router.get(
    "/{name}/commits",
    response_model=List[CommitMetadata],
    summary="List recent commits from GitHub",
)
def repository_commits(
    name: str,
    limit: int = Query(default=50, ge=1, le=200),
    client=Depends(github_service.get_github_client),
) -> List[CommitMetadata]:
    return github_service.get_repository_commits(client, name, limit)


@router.get(
    "/{name}/graph",
    response_model=GraphResponse,
    summary="Retrieve a compact commit graph",
)
def repository_graph(
    name: str,
    limit: int = Query(default=20, ge=1, le=200),
    client=Depends(github_service.get_github_client),
) -> GraphResponse:
    nodes = github_service.get_repository_graph(client, name, limit)
    return GraphResponse(nodes=nodes)
