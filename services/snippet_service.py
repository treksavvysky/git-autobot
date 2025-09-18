from __future__ import annotations

from datetime import datetime
from typing import List

from models import Snippet, SnippetCreateBody, SnippetDeleteResponse
from services import state_store


def list_snippets(repo: str) -> List[Snippet]:
    repo_state = state_store.get_repo_state(repo)
    snippets_payload = repo_state.get("snippets", [])
    return [
        Snippet(
            id=item["id"],
            title=item["title"],
            content=item["content"],
            language=item.get("language"),
            created_at=datetime.fromisoformat(item["created_at"]),
        )
        for item in snippets_payload
    ]


def create_snippet(repo: str, payload: SnippetCreateBody) -> Snippet:
    snippet = Snippet(
        id=f"snippet-{int(datetime.utcnow().timestamp()*1000)}",
        title=payload.title,
        content=payload.content,
        language=payload.language,
        created_at=datetime.utcnow(),
    )
    state_store.append_repo_collection(
        repo,
        "snippets",
        {
            "id": snippet.id,
            "title": snippet.title,
            "content": snippet.content,
            "language": snippet.language,
            "created_at": snippet.created_at.isoformat(),
        },
    )
    return snippet


def delete_snippet(repo: str, snippet_id: str) -> SnippetDeleteResponse:
    deleted = state_store.remove_repo_collection_item(repo, "snippets", snippet_id)
    return SnippetDeleteResponse(id=snippet_id, deleted=deleted)
