from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from models import PullRequestCreateBody, PullRequestCreateResponse, PullRequestModel
from services import github_service

router = APIRouter(prefix="/repos/{name}/pulls", tags=["Pull Requests"])


@router.get("/", response_model=List[PullRequestModel], summary="List pull requests")
def list_pulls(
    name: str, client=Depends(github_service.get_github_client)
) -> List[PullRequestModel]:
    return github_service.get_pull_requests(client, name)


@router.post(
    "/",
    response_model=PullRequestCreateResponse,
    summary="Create pull request (stub)",
)
def create_pull(
    name: str,
    payload: PullRequestCreateBody,
    client=Depends(github_service.get_github_client),
) -> PullRequestCreateResponse:
    return github_service.create_pull_request(client, name, payload)
