from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from models import IssueModel, RecurringTask, RecurringTaskCreateBody, RecurringTaskToggleResponse
from services import github_service, task_service

router = APIRouter(prefix="/repos/{name}", tags=["Issues & Tasks"])


@router.get(
    "/issues",
    response_model=List[IssueModel],
    summary="List repository issues",
)
def list_issues(
    name: str,
    assignee: Optional[str] = Query(default=None),
    labels: Optional[str] = Query(default=None),
    state: str = Query(default="open"),
    client=Depends(github_service.get_github_client),
) -> List[IssueModel]:
    return github_service.get_repository_issues(
        client, name, assignee=assignee, labels=labels, state=state
    )


@router.get(
    "/tasks/recurring",
    response_model=List[RecurringTask],
    summary="List recurring tasks",
)
def list_recurring(name: str) -> List[RecurringTask]:
    return task_service.list_recurring_tasks(name)


@router.post(
    "/tasks/recurring",
    response_model=RecurringTask,
    summary="Create recurring task",
)
def create_recurring(name: str, payload: RecurringTaskCreateBody) -> RecurringTask:
    return task_service.create_recurring_task(name, payload)


@router.post(
    "/tasks/recurring/{task_id}/toggle",
    response_model=RecurringTaskToggleResponse,
    summary="Toggle recurring task enabled state",
)
def toggle_recurring(name: str, task_id: str) -> RecurringTaskToggleResponse:
    return task_service.toggle_recurring_task(name, task_id)
