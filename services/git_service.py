from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException
from git import GitCommandError, Repo

from models import (
    CherryPickRequestBody,
    CloneRepositoryRequest,
    CommitMetadata,
    CommitRequestBody,
    GitCommandResult,
    GitDiffFile,
    GitDiffStats,
    GitDiffSummary,
    GitFileResponse,
    GitLogEntry,
    GitLogResponse,
    GitStatus,
    GitStatusFile,
    LocalRepository,
    LocalRepositoryDetail,
    PushRequestBody,
    ResetRequestBody,
    StashRequestBody,
    StubResponse,
)
from services.config import get_settings


def _local_root() -> Path:
    try:
        from fastapi_app import LOCAL_REPOS_DIR as override

        return Path(override)
    except Exception:
        return get_settings().local_repos_dir


def _safe_repo_name(name: str) -> str:
    if "/" in name or ".." in name or name.strip() == "":
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "invalid_repo_name",
                    "message": "Repository name contains illegal characters.",
                    "details": {"name": name},
                }
            },
        )
    return name


def _repo_path(name: str) -> Path:
    root = _local_root()
    safe_name = _safe_repo_name(name)
    return root / safe_name


def _open_repo(name: str) -> Repo:
    repo_path = _repo_path(name)
    if not repo_path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "repo_not_found",
                    "message": f"Repository '{name}' is not cloned locally.",
                    "details": {"path": str(repo_path)},
                }
            },
        )
    try:
        return Repo(repo_path)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "repo_open_failed",
                    "message": str(exc),
                    "details": {"path": str(repo_path)},
                }
            },
        ) from exc


def list_local_repositories() -> List[LocalRepository]:
    root = _local_root()
    repos: List[LocalRepository] = []
    for entry in root.iterdir():
        if entry.is_dir() and (entry / ".git").exists():
            repos.append(LocalRepository(name=entry.name, path=str(entry)))
    return repos


def get_local_repository(name: str) -> LocalRepositoryDetail:
    repo_path = _repo_path(name)
    repo = _open_repo(name)

    last_commit = None
    try:
        commit = next(repo.iter_commits(max_count=1))
        last_commit = CommitMetadata(
            sha=commit.hexsha,
            message=commit.message,
            author=getattr(commit.author, "name", None),
            date=datetime.utcfromtimestamp(commit.committed_date).isoformat(),
        )
    except Exception:
        last_commit = None

    try:
        branch_name = repo.active_branch.name  # type: ignore[union-attr]
    except Exception:
        branch_name = None

    return LocalRepositoryDetail(
        name=name,
        path=str(repo_path),
        active_branch=branch_name,
        is_dirty=repo.is_dirty(untracked_files=True),
        last_commit=last_commit,
    )


def clone_repository(name: str, payload: CloneRepositoryRequest) -> StubResponse:
    """Clone repository stub.

    Cloning from remote is not available in the starter; return stub metadata.
    """

    repo_path = _repo_path(name)
    return StubResponse(
        note=(
            "Clone operation is not yet implemented. Create the repository manually "
            f"at {repo_path} and the dashboard will pick it up."
        ),
        details={"remote_url": payload.remote_url, "path": str(repo_path)},
    )


def get_status(name: str) -> GitStatus:
    repo = _open_repo(name)
    status_lines = repo.git.status("--short", "--branch").splitlines()
    branch = None
    files: List[GitStatusFile] = []
    for line in status_lines:
        if line.startswith("##"):
            branch = line.replace("##", "").strip()
            continue
        if len(line) >= 3:
            status_code = line[:2].strip()
            file_path = line[3:]
            files.append(GitStatusFile(path=file_path, status=status_code))
    return GitStatus(branch=branch, files=files)


def pull_repository(name: str, rebase: bool) -> StubResponse:
    return StubResponse(
        note="Pull operation is stubbed. Configure remotes and implement later.",
        details={"rebase": rebase},
    )


def push_repository(name: str, payload: PushRequestBody) -> StubResponse:
    return StubResponse(
        note="Push operation is stubbed. Configure remotes and implement later.",
        details={"branch": payload.branch},
    )


def stash_operation(name: str, payload: StashRequestBody) -> GitCommandResult:
    return GitCommandResult(
        ok=True,
        message="Stash command is stubbed; no action performed.",
        details={"action": payload.action, "name": payload.name},
    )


def commit_changes(name: str, payload: CommitRequestBody) -> GitCommandResult:
    return GitCommandResult(
        ok=True,
        message="Commit command is stubbed; no commit created.",
        details={"message": payload.message},
    )


def checkout_branch(name: str, branch: str, create: bool) -> GitCommandResult:
    return GitCommandResult(
        ok=True,
        message="Checkout command is stubbed; no branch change occurred.",
        details={"branch": branch, "create": create},
    )


def reset_repository(name: str, payload: ResetRequestBody) -> GitCommandResult:
    return GitCommandResult(
        ok=True,
        message="Reset command is stubbed; no reset performed.",
        details={"mode": payload.mode, "ref": payload.ref},
    )


def cherry_pick(name: str, payload: CherryPickRequestBody) -> GitCommandResult:
    return GitCommandResult(
        ok=True,
        message="Cherry-pick command is stubbed; no commits applied.",
        details={"shas": payload.shas},
    )


def get_log(name: str, limit: int = 50, author: Optional[str] = None) -> GitLogResponse:
    repo = _open_repo(name)
    kwargs = {}
    if author:
        kwargs["author"] = author
    commits = list(repo.iter_commits(max_count=limit, **kwargs))
    entries = [
        GitLogEntry(
            sha=commit.hexsha,
            author=getattr(commit.author, "name", None),
            message=commit.message,
            date=datetime.utcfromtimestamp(commit.committed_date),
        )
        for commit in commits
    ]
    return GitLogResponse(entries=entries)


def get_diff(name: str, target: str = "HEAD", mode: str = "summary") -> GitDiffSummary:
    repo = _open_repo(name)
    try:
        if mode == "patch":
            patch_text = repo.git.diff(target)
            files: List[GitDiffFile] = []
            stats = GitDiffStats(additions=0, deletions=0)
            return GitDiffSummary(
                files=files,
                stats=stats,
                mode="patch",
                patch=patch_text,
            )
        diff_index = repo.git.diff("--numstat", target).splitlines()
        files: List[GitDiffFile] = []
        additions_total = 0
        deletions_total = 0
        for entry in diff_index:
            parts = entry.split("\t")
            if len(parts) >= 3:
                additions = int(parts[0]) if parts[0].isdigit() else 0
                deletions = int(parts[1]) if parts[1].isdigit() else 0
                path = parts[2]
                additions_total += additions
                deletions_total += deletions
                files.append(
                    GitDiffFile(
                        path=path,
                        status="modified",
                        additions=additions,
                        deletions=deletions,
                    )
                )
        stats = GitDiffStats(additions=additions_total, deletions=deletions_total)
        return GitDiffSummary(files=files, stats=stats, mode="summary")
    except GitCommandError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "diff_failed",
                    "message": str(exc),
                    "details": {"target": target, "mode": mode},
                }
            },
        ) from exc


def get_staged(name: str) -> List[GitStatusFile]:
    repo = _open_repo(name)
    diff_index = repo.index.diff("HEAD")
    files: List[GitStatusFile] = []
    for item in diff_index:
        files.append(GitStatusFile(path=item.a_path, status=item.change_type))
    return files


def read_file(name: str, path: str, ref: str = "HEAD") -> GitFileResponse:
    repo = _open_repo(name)
    try:
        content = repo.git.show(f"{ref}:{path}")
        return GitFileResponse(path=path, ref=ref, content=content)
    except GitCommandError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "file_not_found",
                    "message": str(exc),
                    "details": {"path": path, "ref": ref},
                }
            },
        ) from exc
