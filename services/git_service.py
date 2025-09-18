from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException
from git import GitCommandError, Repo

from models import (
    CherryPickRequestBody,
    CloneRepositoryRequest,
    CloneRepositoryResponse,
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
    LocalBranchStatus,
    LocalRemote,
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


def _normalize_remote_candidate(url: str) -> str:
    candidate = url.strip()
    if candidate.startswith("http") and not candidate.endswith(".git"):
        candidate = candidate.rstrip("/") + ".git"
    return candidate


def _discover_default_branch(repo: Repo) -> Optional[str]:
    try:
        return repo.active_branch.name  # type: ignore[union-attr]
    except Exception:
        try:
            ref = repo.git.symbolic_ref("refs/remotes/origin/HEAD")
            if ref.startswith("refs/remotes/"):
                return "/".join(ref.split("/")[3:])
        except Exception:
            return None
    return None


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


def list_local_remotes(name: str) -> List[LocalRemote]:
    repo = _open_repo(name)
    remotes: List[LocalRemote] = []
    for remote in repo.remotes:
        remotes.append(LocalRemote(name=remote.name, urls=list(remote.urls)))
    return remotes


def list_local_branches(name: str) -> List[LocalBranchStatus]:
    repo = _open_repo(name)
    try:
        active_name = repo.active_branch.name  # type: ignore[union-attr]
    except Exception:
        active_name = None

    branches: List[LocalBranchStatus] = []
    for branch in repo.branches:
        tracking_name: Optional[str] = None
        ahead = 0
        behind = 0
        try:
            tracking_ref = branch.tracking_branch()
        except Exception:
            tracking_ref = None
        if tracking_ref is not None:
            tracking_name = getattr(tracking_ref, "name", str(tracking_ref))
            try:
                ahead = sum(1 for _ in repo.iter_commits(f"{tracking_name}..{branch.name}"))
                behind = sum(1 for _ in repo.iter_commits(f"{branch.name}..{tracking_name}"))
            except GitCommandError:
                ahead = behind = 0

        branches.append(
            LocalBranchStatus(
                name=branch.name,
                is_active=branch.name == active_name,
                tracking=tracking_name,
                ahead=ahead,
                behind=behind,
            )
        )

    branches.sort(key=lambda item: (0 if item.is_active else 1, item.name.lower()))
    return branches


def clone_repository(name: str, payload: CloneRepositoryRequest) -> CloneRepositoryResponse:
    repo_path = _repo_path(name)
    repo_path.parent.mkdir(parents=True, exist_ok=True)

    remote_url = payload.remote_url.strip() if payload.remote_url else None
    normalized_remote = (
        _normalize_remote_candidate(remote_url) if remote_url else None
    )

    created = False
    updated = False
    message: Optional[str] = None
    repo: Optional[Repo] = None

    if not repo_path.exists():
        if not normalized_remote:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "remote_required",
                        "message": "Remote URL is required for an initial clone.",
                        "details": {"name": name},
                    }
                },
            )
        try:
            repo = Repo.clone_from(normalized_remote, repo_path)
            created = True
            message = "Repository cloned successfully."
        except GitCommandError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "clone_failed",
                        "message": str(exc),
                        "details": {"remote_url": normalized_remote},
                    }
                },
            ) from exc
    else:
        repo = _open_repo(name)
        origin = None
        if repo.remotes:
            try:
                origin = repo.remote("origin")
            except ValueError:
                origin = repo.remotes[0]
        if origin is None:
            if normalized_remote:
                origin = repo.create_remote("origin", normalized_remote)
            else:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": {
                            "code": "remote_missing",
                            "message": (
                                "Local repository has no remote configured; provide a remote URL "
                                "to continue."
                            ),
                            "details": {"name": name},
                        }
                    },
                )
        else:
            if normalized_remote:
                existing_urls = {
                    _normalize_remote_candidate(url) for url in origin.urls
                }
                if normalized_remote not in existing_urls:
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": {
                                "code": "remote_mismatch",
                                "message": (
                                    "Local repository remote does not match the requested remote URL."
                                ),
                                "details": {
                                    "requested": normalized_remote,
                                    "existing": list(existing_urls),
                                },
                            }
                        },
                    )

        try:
            origin.fetch()
        except GitCommandError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "fetch_failed",
                        "message": str(exc),
                        "details": {"remote": origin.name if origin else None},
                    }
                },
            ) from exc

        if repo.is_dirty(untracked_files=True):
            message = (
                "Local repository has uncommitted changes; fetched remote refs without "
                "fast-forwarding."
            )
        else:
            try:
                active_branch = repo.active_branch
            except Exception:
                active_branch = None

            if active_branch is None:
                message = (
                    "Repository is in a detached HEAD state; fetched remote refs without "
                    "fast-forwarding."
                )
            else:
                tracking_branch = active_branch.tracking_branch()
                target_ref = None
                if tracking_branch is not None:
                    target_ref = tracking_branch.name
                elif origin is not None:
                    target_ref = f"{origin.name}/{active_branch.name}"

                if target_ref and target_ref in {ref.name for ref in repo.refs}:
                    try:
                        repo.git.merge("--ff-only", target_ref)
                        updated = True
                        message = "Repository fast-forwarded to latest remote state."
                    except GitCommandError as exc:
                        raise HTTPException(
                            status_code=409,
                            detail={
                                "error": {
                                    "code": "fast_forward_failed",
                                    "message": str(exc),
                                    "details": {"target": target_ref},
                                }
                            },
                        ) from exc
                else:
                    message = (
                        "No remote tracking branch found; fetched remote refs without fast-forwarding."
                    )

    assert repo is not None
    default_branch = _discover_default_branch(repo)

    return CloneRepositoryResponse(
        path=str(repo_path),
        created=created,
        updated=updated,
        default_branch=default_branch,
        message=message,
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


def pull_repository(name: str, rebase: bool) -> GitCommandResult:
    repo = _open_repo(name)

    try:
        active_branch = repo.active_branch
    except TypeError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "detached_head",
                    "message": "Cannot pull while HEAD is detached.",
                    "details": {},
                }
            },
        ) from exc

    tracking_branch = active_branch.tracking_branch()

    pull_args: List[str] = []
    if rebase:
        pull_args.append("--rebase")

    remote_name: Optional[str] = None
    remote_ref: Optional[str] = None

    if tracking_branch is not None:
        tracking_name = tracking_branch.name
        if "/" in tracking_name:
            remote_name, remote_ref = tracking_name.split("/", 1)
        else:
            remote_name = tracking_name
    elif repo.remotes:
        remote = next((r for r in repo.remotes if r.name == "origin"), repo.remotes[0])
        remote_name = remote.name
        remote_ref = active_branch.name
        pull_args.extend([remote_name, remote_ref])
    else:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "no_remote",
                    "message": "Repository has no remotes configured for pulling.",
                    "details": {"branch": active_branch.name},
                }
            },
        )

    try:
        output = repo.git.pull(*pull_args)
    except GitCommandError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "pull_failed",
                    "message": str(exc),
                    "details": {
                        "branch": active_branch.name,
                        "remote": remote_name,
                        "rebase": rebase,
                    },
                }
            },
        ) from exc

    return GitCommandResult(
        ok=True,
        message="Pull completed successfully.",
        details={
            "branch": active_branch.name,
            "remote": remote_name,
            "rebase": rebase,
            "output": output.strip(),
        },
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
