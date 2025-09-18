from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class APIError(BaseModel):
    """Standard API error payload."""

    code: str = Field(..., description="Machine readable error code")
    message: str = Field(..., description="Human readable description of the error")
    details: Optional[dict] = Field(
        default=None, description="Additional context specific to the error"
    )


class ErrorResponse(BaseModel):
    """Container used when returning structured errors."""

    error: APIError


class Repository(BaseModel):
    """Basic repository information returned from the GitHub API."""

    name: str
    description: Optional[str] = None
    visibility: Literal["public", "private"]
    default_branch: str


class CommitMetadata(BaseModel):
    sha: str
    message: str
    author: Optional[str] = None
    date: Optional[str] = None


class RepositoryDetails(BaseModel):
    name: str
    description: Optional[str] = None
    visibility: Literal["public", "private"]
    default_branch: str
    branches: List[str]
    last_commit: Optional[CommitMetadata] = None
    contributors: List[str]
    html_url: str


class ReadmeResponse(BaseModel):
    content: str


class RenderedReadmeResponse(BaseModel):
    html: str
    source_encoding: str = Field(default="utf-8")


class SyncStatus(BaseModel):
    ahead: int
    behind: int
    status: Literal["synced", "ahead", "behind", "diverged"]


class Branch(BaseModel):
    name: str
    default: bool = False
    protected: bool = False


class BranchCreateRequest(BaseModel):
    name: str
    base: str


class BranchDeleteResponse(BaseModel):
    stub: bool = Field(default=True)
    note: str = Field(default="Branch deletion is stubbed.")


class LocalRepository(BaseModel):
    name: str
    path: str


class LocalRepositoryDetail(LocalRepository):
    active_branch: Optional[str] = None
    is_dirty: bool = False
    last_commit: Optional[CommitMetadata] = None


class CloneRepositoryRequest(BaseModel):
    remote_url: Optional[str] = Field(
        default=None, description="Remote URL to clone from when available"
    )


class PullRequestBody(BaseModel):
    rebase: bool = False


class PushRequestBody(BaseModel):
    branch: Optional[str] = Field(
        default=None, description="Branch to push; defaults to current branch"
    )


class GitStatusFile(BaseModel):
    path: str
    status: str


class GitStatus(BaseModel):
    branch: Optional[str] = None
    files: List[GitStatusFile] = Field(default_factory=list)


class GitCommandResult(BaseModel):
    ok: bool
    message: str
    details: Optional[dict] = None


class StashRequestBody(BaseModel):
    action: Literal["create", "apply", "drop"]
    name: Optional[str] = Field(
        default=None, description="Optional custom stash name for create/apply"
    )


class CommitRequestBody(BaseModel):
    message: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None


class CheckoutRequestBody(BaseModel):
    branch: str
    create: bool = False


class ResetRequestBody(BaseModel):
    mode: Literal["soft", "mixed", "hard"]
    ref: str


class CherryPickRequestBody(BaseModel):
    shas: List[str]


class GitLogEntry(BaseModel):
    sha: str
    author: Optional[str] = None
    message: str
    date: datetime


class GitLogResponse(BaseModel):
    entries: List[GitLogEntry]


class GitDiffFile(BaseModel):
    path: str
    status: str
    additions: int
    deletions: int


class GitDiffStats(BaseModel):
    additions: int
    deletions: int


class GitDiffSummary(BaseModel):
    files: List[GitDiffFile]
    stats: GitDiffStats
    mode: Literal["summary", "patch"]
    patch: Optional[str] = None


class GitFileResponse(BaseModel):
    path: str
    ref: str
    content: str


class PullRequestModel(BaseModel):
    id: int
    number: int
    title: str
    state: str
    head: str
    base: str
    url: str


class PullRequestCreateBody(BaseModel):
    title: str
    head: str
    base: str
    body: Optional[str] = None
    draft: bool = False


class PullRequestCreateResponse(BaseModel):
    stub: bool = Field(default=True)
    note: str = Field(default="Pull request creation is stubbed.")
    request: PullRequestCreateBody


class GraphNode(BaseModel):
    sha: str
    parents: List[str]
    message: str
    author: Optional[str] = None
    date: Optional[datetime] = None


class GraphResponse(BaseModel):
    nodes: List[GraphNode]


class IssueModel(BaseModel):
    id: int
    number: int
    title: str
    state: Literal["open", "closed"]
    labels: List[str] = Field(default_factory=list)
    assignee: Optional[str] = None
    url: str


class RecurringTask(BaseModel):
    id: str
    name: str
    schedule: str
    enabled: bool = True
    last_run: Optional[datetime] = None


class RecurringTaskCreateBody(BaseModel):
    name: str
    schedule: str


class RecurringTaskToggleResponse(BaseModel):
    id: str
    enabled: bool


class CIJob(BaseModel):
    id: str
    name: str
    status: Literal["queued", "in_progress", "success", "failure"]
    url: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CIStatusResponse(BaseModel):
    jobs: List[CIJob]


class CoverageReport(BaseModel):
    coverage: float
    generated_at: datetime
    note: Optional[str] = None


class DockerStatus(BaseModel):
    tag: str
    published_at: datetime
    digest: str


class HealthCheck(BaseModel):
    name: str
    status: Literal["ok", "warn", "fail"]
    details: dict


class HealthStatusResponse(BaseModel):
    status: Literal["ok", "warn", "fail"]
    checks: List[HealthCheck]


class Note(BaseModel):
    id: str
    content: str
    created_at: datetime


class NoteCreateBody(BaseModel):
    content: str


class Snippet(BaseModel):
    id: str
    title: str
    content: str
    language: Optional[str] = None
    created_at: datetime


class SnippetCreateBody(BaseModel):
    title: str
    content: str
    language: Optional[str] = None


class SnippetDeleteResponse(BaseModel):
    id: str
    deleted: bool


class AIExplainErrorRequest(BaseModel):
    error: str
    context: Optional[str] = None


class AINextStepRequest(BaseModel):
    context: Optional[str] = None


class AIResponse(BaseModel):
    stub: bool = Field(default=True)
    message: str
    recommendations: List[str] = Field(default_factory=list)


class AIDailyBrief(BaseModel):
    stub: bool = Field(default=True)
    summary: str
    highlights: List[str] = Field(default_factory=list)


class MetaConfig(BaseModel):
    name: str
    version: str
    allowed_origins: List[str]


class StubResponse(BaseModel):
    stub: bool = Field(default=True)
    note: str
    details: Optional[dict] = None
