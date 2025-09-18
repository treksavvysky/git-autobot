from __future__ import annotations

from typing import List

from fastapi import APIRouter

from models import Snippet, SnippetCreateBody, SnippetDeleteResponse
from services import snippet_service

router = APIRouter(prefix="/repos/{name}/snippets", tags=["Snippets"])


@router.get("/", response_model=List[Snippet], summary="List snippets")
def list_snippets(name: str) -> List[Snippet]:
    return snippet_service.list_snippets(name)


@router.post("/", response_model=Snippet, summary="Create snippet")
def create_snippet(name: str, payload: SnippetCreateBody) -> Snippet:
    return snippet_service.create_snippet(name, payload)


@router.delete(
    "/{snippet_id}",
    response_model=SnippetDeleteResponse,
    summary="Delete snippet",
)
def delete_snippet(name: str, snippet_id: str) -> SnippetDeleteResponse:
    return snippet_service.delete_snippet(name, snippet_id)
