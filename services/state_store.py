from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

_STATE_FILE = Path(__file__).resolve().parent.parent / "dashboard_state.json"


def _ensure_state_file() -> None:
    if not _STATE_FILE.exists():
        _STATE_FILE.write_text("{}", encoding="utf-8")


def _load_state() -> Dict[str, Any]:
    _ensure_state_file()
    try:
        return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_state(state: Dict[str, Any]) -> None:
    _STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def get_repo_state(repo: str) -> Dict[str, Any]:
    state = _load_state()
    return state.setdefault(repo, {})


def update_repo_state(repo: str, key: str, value: Any) -> Dict[str, Any]:
    state = _load_state()
    repo_state = state.setdefault(repo, {})
    repo_state[key] = value
    _save_state(state)
    return repo_state


def append_repo_collection(repo: str, key: str, item: Any) -> Any:
    state = _load_state()
    repo_state = state.setdefault(repo, {})
    collection = repo_state.setdefault(key, [])
    collection.append(item)
    _save_state(state)
    return item


def remove_repo_collection_item(repo: str, key: str, item_id: str) -> bool:
    state = _load_state()
    repo_state = state.setdefault(repo, {})
    collection = repo_state.setdefault(key, [])
    before = len(collection)
    repo_state[key] = [item for item in collection if item.get("id") != item_id]
    _save_state(state)
    return before != len(repo_state[key])
