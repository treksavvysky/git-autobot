from __future__ import annotations

from datetime import datetime
from typing import List

from models import RecurringTask, RecurringTaskCreateBody, RecurringTaskToggleResponse
from services import state_store


def list_recurring_tasks(repo: str) -> List[RecurringTask]:
    repo_state = state_store.get_repo_state(repo)
    payload = repo_state.get("recurring_tasks", [])
    return [
        RecurringTask(
            id=item["id"],
            name=item["name"],
            schedule=item["schedule"],
            enabled=item.get("enabled", True),
            last_run=(
                datetime.fromisoformat(item["last_run"])
                if item.get("last_run")
                else None
            ),
        )
        for item in payload
    ]


def create_recurring_task(repo: str, body: RecurringTaskCreateBody) -> RecurringTask:
    task = RecurringTask(
        id=f"task-{int(datetime.utcnow().timestamp()*1000)}",
        name=body.name,
        schedule=body.schedule,
        enabled=True,
        last_run=None,
    )
    state_store.append_repo_collection(
        repo,
        "recurring_tasks",
        {
            "id": task.id,
            "name": task.name,
            "schedule": task.schedule,
            "enabled": task.enabled,
            "last_run": task.last_run.isoformat() if task.last_run else None,
        },
    )
    return task


def toggle_recurring_task(repo: str, task_id: str) -> RecurringTaskToggleResponse:
    state = state_store.get_repo_state(repo)
    tasks = state.get("recurring_tasks", [])
    for task in tasks:
        if task.get("id") == task_id:
            task["enabled"] = not task.get("enabled", True)
            state_store.update_repo_state(repo, "recurring_tasks", tasks)
            return RecurringTaskToggleResponse(id=task_id, enabled=task["enabled"])
    return RecurringTaskToggleResponse(id=task_id, enabled=False)
