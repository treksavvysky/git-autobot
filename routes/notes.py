from __future__ import annotations

from typing import List

from fastapi import APIRouter

from models import Note, NoteCreateBody
from services import notes_service

router = APIRouter(prefix="/repos/{name}/notes", tags=["Notes"])


@router.get("/", response_model=List[Note], summary="List notes")
def list_notes(name: str) -> List[Note]:
    return notes_service.list_notes(name)


@router.post("/", response_model=Note, summary="Create note")
def create_note(name: str, payload: NoteCreateBody) -> Note:
    return notes_service.add_note(name, payload)
