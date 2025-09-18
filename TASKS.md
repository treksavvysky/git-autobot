# TASKS.md — GitPython Clone Flow & Repo Path

## Objective

Enable the **Clone Repository** button to provision a local, host‑visible working copy using the **GitPython** SDK (not raw CLI calls). Ensure the clone lives under a configurable **`REPO_PATH`** and can be used by external tools (VSCode, code‑server) outside the app/container. Update dependency manifests to include GitPython and document the workflow.

## Summary of Work

- Implement/finish `POST /local/repos/{name}/clone` in FastAPI using **GitPython** via a service function (no Git logic inside route files).
- Ensure the working copy is created/updated under **`${REPO_PATH}/${name}`** and is bind‑mounted into containers.
- Plumb **`REPO_PATH`** through `docker-compose.yaml`, `./docker-run.sh`, and `.env` (with clear precedence).
- Update **requirements** and **pyproject** to include **GitPython** and compatible pins for `uv` workflows.
- Update **README.md** to document configuration, run instructions, and verification.

> AI Assistant Hooks and unsupported GitHub endpoints remain stubbed/fictitious as previously agreed; no changes required in this task.

---

## Deliverables

1. **FastAPI backend**

   - Route: `POST /local/repos/{name}/clone` (router: `routes/local.py`).
   - Service: `services/git_service.py` — contains all GitPython interactions.
   - Behavior:

     - If local repo **does not exist**: create parent dirs, **clone** from GitHub.
     - If local repo **exists**: validate `origin` matches, **fetch** and fast‑forward the current branch when clean; otherwise no‑op with clear status.
     - Return JSON with host path and action summary: `{ "path": "/abs/host/path", "created": bool, "updated": bool, "default_branch": "main" }`.

   - Safety: sanitize `{name}`, ensure paths remain **inside** `REPO_PATH`, never log secrets.

2. **Configuration & Runtime**

   - **Env var:** `REPO_PATH` (absolute path). Resolution priority: `./docker-run.sh --repo-path` → `.env` → compose default.
   - **docker-compose.yaml:**

     - `environment:` add `REPO_PATH=${REPO_PATH}`
     - `volumes:` add `- ${REPO_PATH}:${REPO_PATH}`

   - **./docker-run.sh:**

     - Accept `--repo-path /abs/path` (or positional). Export `REPO_PATH` and pass `-e REPO_PATH` and `-v` mapping to `docker run`.

   - **.env:** allow specifying `REPO_PATH=/absolute/host/path` (documented; optional if provided via script).

3. **Dependency Manifests**

   - **requirements.txt** — add (or ensure):

     ```txt
     GitPython>=3.1
     ```

   - **pyproject.toml** — add under `[project] dependencies`:

     ```toml
     [project]
     # ... existing fields
     dependencies = [
       # existing deps ...
       "GitPython>=3.1",
     ]
     ```

   - **uv usage** (if using Astral’s `uv`):

     - Add via: `uv add GitPython>=3.1`
     - Lock/update: `uv lock`

4. **Documentation**

   - **README.md:**

     - Prereqs: Git installed on host and container; GitHub token configured if needed.
     - Configure: `REPO_PATH` via `.env` or `./docker-run.sh --repo-path`.
     - Run: compose/uv instructions; how to click **Clone Repository**.
     - Verify: on **host**, `cd $REPO_PATH/<repo> && git status` should work.
     - Troubleshooting: permissions, wrong remote, dirty working tree, token/auth.

---

## Acceptance Criteria

- Calling `POST /local/repos/{name}/clone` on a new repo creates `${REPO_PATH}/{name}` with a valid Git working copy (visible on host).
- Calling again on an existing clean repo fetches/fast‑forwards (no data loss).
- The path is bind‑mounted in compose and discoverable by other tools.
- `requirements.txt` and `pyproject.toml` both declare **GitPython** (compatible with `uv`).
- README documents setup and verification steps.
- OpenAPI `/docs` shows the endpoint with request/response examples.

---

## Non‑Goals

- Implementing complex flows (submodules, LFS, sparse checkout) — follow‑up tasks.
- Replacing AI stubs or unsupported GitHub endpoints.

---

## Test Plan

- **Unit tests** for `git_service.clone_or_update_repo(...)`:

  - New clone success → directory created, `.git` present, default branch set.
  - Existing repo fast‑forward success; wrong remote error; dirty tree → returns status without changes; path traversal attempt rejected.

- **Integration test** with temp `REPO_PATH` bind‑mounted:

  - Start API (compose), call endpoint, assert on filesystem + `git status` from host context.

---

## Operational Notes

- GitPython requires Git installed; ensure container image and host have `git` binary.
- Consider UID/GID alignment to avoid file permission friction when mounting host paths.
- Log structured messages (no secrets); tag logs with repo name and route.
