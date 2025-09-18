TASK.md — FastAPI Support for Cockpit-Style Repository Dashboard
Objective

Implement the missing FastAPI endpoints required by the Repository Dashboard (Next.js) so the page can operate entirely on live data and actions. Keep the API surface cohesive, documented, and CORS‑enabled.

Scope

Only implement the endpoints listed below (no extra features beyond what is required by the dashboard). Preserve existing routes and their behavior. Provide minimal request/response schemas (pydantic models) and standardized error handling.

Non‑Goals

Frontend work in Next.js (handled separately).

Business logic beyond Git operations, GitHub API passthrough, and simple task/notes storage.

Constraints

Follow RESTful naming and use nouns for resources.

JSON in/out; UTF‑8; timestamps in ISO‑8601.

Idempotent GET; safe error messages (no secrets); rate‑limit as needed.

Respect .env (e.g., GITHUB_TOKEN, LOCAL_REPOS_DIR).

Add CORS for all new routes.

Acceptance Criteria

All endpoints compile and run under uvicorn.

200/4xx/5xx semantics are correct; structured error payloads.

Basic unit tests for happy-path and key failure modes per route.

Lint/format clean (ruff/flake8 + black) and type-checked (mypy/pyright).

OpenAPI docs (/docs) list each new endpoint with models and examples.

New Endpoints to Implement
Repository Overview & Local Sync

GET /repos/{name}/sync-status

GET /repos/{name}/branches

GET /local/repos/{name}

POST /local/repos/{name}/clone

GET /local/repos/{name}/status

POST /local/repos/{name}/pull (query/body flag: rebase: bool)

POST /local/repos/{name}/push (optional: branch)

README

GET /repos/{name}/readme/rendered

Git Command Helper

POST /local/repos/{name}/stash (create/apply/drop)

POST /local/repos/{name}/commit (message, author opts)

POST /local/repos/{name}/checkout (branch, create flag)

POST /local/repos/{name}/reset (mode: soft/mixed/hard, ref)

POST /local/repos/{name}/cherry-pick (sha list)

GET /local/repos/{name}/log (limit, author filter)

Commits & Diffs

GET /repos/{name}/commits (remote)

GET /local/repos/{name}/diff (vs target; mode: summary/patch)

GET /local/repos/{name}/staged

GET /local/repos/{name}/file/{path} (at ref=HEAD by default)

Branch & PR Management

POST /repos/{name}/branches (create from base)

DELETE /repos/{name}/branches/{branch}

GET /repos/{name}/graph (compact DAG for UI)

GET /repos/{name}/pulls

POST /repos/{name}/pulls

POST /repos/{name}/branches/{branch}/prune-stale (policy‑based local cleanup)

Issues & Workflow Panel

GET /repos/{name}/issues (filters: assignee, labels, state)

GET /repos/{name}/tasks/recurring

POST /repos/{name}/tasks/recurring

POST /repos/{name}/tasks/recurring/{id}/toggle

CI/CD & Health

GET /repos/{name}/ci/actions/latest

GET /repos/{name}/ci/actions/runs

GET /repos/{name}/ci/coverage

GET /repos/{name}/ci/docker

GET /repos/{name}/health

Notes & Snippets

GET /repos/{name}/notes

POST /repos/{name}/notes

GET /repos/{name}/snippets

POST /repos/{name}/snippets

DELETE /repos/{name}/snippets/{id}

AI Assistant Hooks

POST /repos/{name}/ai/explain-error

POST /repos/{name}/ai/next-step

GET /repos/{name}/ai/daily-brief

Misc

OPTIONS /\* (CORS preflight)

GET /meta/config
