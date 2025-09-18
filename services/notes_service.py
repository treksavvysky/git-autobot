from __future__ import annotations

from datetime import datetime
from typing import List

from models import Note, NoteCreateBody
from services import state_store


def list_notes(repo: str) -> List[Note]:
    repo_state = state_store.get_repo_state(repo)
    notes_payload = repo_state.get("notes", [])
    return [
        Note(
            id=item["id"],
            content=item["content"],
            created_at=datetime.fromisoformat(item["created_at"]),
        )
        for item in notes_payload
    ]


def add_note(repo: str, payload: NoteCreateBody) -> Note:
    note = Note(
        id=f"note-{int(datetime.utcnow().timestamp()*1000)}",
        content=payload.content,
        created_at=datetime.utcnow(),
    )
    state_store.append_repo_collection(
        repo,
        "notes",
        {"id": note.id, "content": note.content, "created_at": note.created_at.isoformat()},
    )
    return note
