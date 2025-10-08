# AGENTS.md — Working with the Git Autobot Backend (FastAPI) & Dashboard

## Mission

You are setting up and extending the FastAPI backend to fully support the cockpit‑style Repository Dashboard. Implement the New Endpoints from TASK.md, wire them into existing services, and ensure they are discoverable via OpenAPI.

## Repository Map

- `fastapi_app.py` — app entry and route wiring.
- `services/` — Git, GitHub, CI, tasks, notes/snippets, and auth service layers.
- `models/` — pydantic schemas (request/response) and domain models.
- `routes/` — route modules grouped by feature (repos, local, ci, ai, notes, etc.).
- `tests/` — pytest suites for units + lightweight integration.

If any folders don’t exist yet, create them with minimal scaffolding.

## Environment & Secrets

- `.env` keys: `GITHUB_TOKEN`, `LOCAL_REPOS_DIR`, `GITHUB_API_BASE` (default: GitHub REST v3), `ALLOWED_ORIGINS`, `API_SERVER_URL`, `API_KEY`.
- Copy `.env.example` to `.env` and configure your values.
- Never log tokens or API keys. Use `os.getenv` via a small config helper.

## Setup

### Python

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt # or: uv/poetry if present
```

### Run

```bash
uvicorn fastapi_app:app --reload --port 8000
```

### Lint/Format/Typecheck (if tools present)

```bash
ruff check . || flake8 .
black --check .
pytest -q
mypy . || pyright
```

## Running the Dashboard (for local integration tests)

The Next.js frontend consumes these routes. Default dev URLs:

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

Set CORS to allow the frontend origin. Ensure OPTIONS preflight responds across routes.

## API Conventions

- JSON only. Use pydantic models for all input/output.
- Timestamps: ISO‑8601 (UTC). SHAs are lowercase hex. Branch names are strings.
- Errors: `{ "error": { "code": "string", "message": "human readable", "details": {...} } }`
- Pagination: `?page=1&per_page=50` for list endpoints that can grow.
- Filtering: query params (assignee, labels, state, etc.).
- Idempotency: avoid side effects in GET.

## Logging & Observability

- Log route start/stop, duration, and status code.
- Tag logs by repo name and route group.
- Suppress secrets; redact tokens and API keys.

## Security

- All API endpoints are protected with API key authentication via `X-API-Key` header.
- API key is loaded from `API_KEY` environment variable.
- Prefer PAT or App token in backend only (never expose to browser).
- Validate name path param to a known allowlist or sanitize path traversal.
- When touching local repos, join paths under `LOCAL_REPOS_DIR` safely.

## Testing Guidance

- Mock GitHub API and git CLI in unit tests.
- Include at least one failing CI status and one failing push scenario.
- Snapshot test for readme/rendered (stable HTML subset).

## Endpoint Groups to Implement

Reproduce exactly as listed in TASK.md:

- Repository Overview & Local Sync: sync status, branches, local presence, clone, status, pull, push.
- README: rendered markdown.
- Git Command Helper: stash/commit/checkout/reset/cherry‑pick/log.
- Commits & Diffs: remote commits, diff, staged, file-at-ref.
- Branch & PR Management: create/delete branches, graph, PRs, prune‑stale.
- Issues & Workflow: issues, recurring tasks CRUD (list/create/toggle).
- CI/CD & Health: actions latest/runs, coverage, docker, aggregate health.
- Notes & Snippets: notes get/set, snippets CRUD.
- AI Hooks: explain-error, next-step, daily-brief.
- Misc: OPTIONS preflight, meta/config.

## Minimal Schemas (illustrative — adjust as needed)

**SyncStatus:**

```json
{ "ahead": int, "behind": int, "status": "synced|ahead|behind" }
```

**Commit:**

```json
{ "sha": string, "author": string, "message": string, "date": string }
```

**DiffSummary:**

```json
{ "files": [{"path": string, "status": string, "add": int, "del": int}], "stats": {"add": int, "del": int} }
```

**Branch:**

```json
{ "name": string, "default": bool, "protected": bool }
```

**PR:**

```json
{ "id": int, "number": int, "title": string, "state": string, "head": string, "base": string, "url": string }
```

**Issue:**

```json
{ "id": int, "number": int, "title": string, "state": string, "labels": [string], "assignee": string|null, "url": string }
```

**Task:**

```json
{ "id": string, "name": string, "schedule": string, "enabled": bool, "last_run": string|null }
```

**Health:**

```json
{ "status": "ok|warn|fail", "checks": [{"name": string, "status": string, "details": object}] }
```

## Coding Standards

- Keep route modules small and cohesive; move logic into services/.
- Validate inputs with pydantic; raise HTTPException with structured errors.
- Prefer async IO for network-bound GitHub calls.
- Return minimal fields needed by the dashboard; add fields only when required by UI.

## FastAPI Application Standards

- Initialize the app through `fastapi_app.py` using the canonical metadata (`FastAPI(title="Git Autobot GitHub API", servers=[{"url": os.getenv("API_SERVER_URL", "http://localhost:8000")}])`) so the autogenerated Swagger UI and OpenAPI schema stay enabled (`/docs` and `/openapi.json` must remain reachable for the dashboard and QA tooling). The servers field is set from the `API_SERVER_URL` environment variable.
- Mirror the reference CORS configuration: attach `CORSMiddleware` with the configured allowed origins (defaulting to `*` for local dev) and keep the explicit `OPTIONS` handling until all routers expose proper preflight responses.
- Protect all API endpoints with API key authentication using the `verify_api_key` dependency from `services.auth`, applied at the router level.
- Acquire GitHub credentials the same way our `get_github_client` dependency does—read `token` overrides from query parameters, fall back to `os.getenv("GITHUB_TOKEN")`, and never log or echo the secret.
- Resolve local repository paths under `LOCAL_REPOS_DIR`, ensure the directory exists on startup, and guard against path traversal when accepting repo names.
- Prefer modular route inclusion: define feature routers under `routes/` (e.g., git, GitHub, CI) and import them into `fastapi_app.py` with `include_router` instead of expanding the app file with endpoint logic.

## Done = Shippable

- All endpoints pass tests, documented in OpenAPI, and exercised end‑to‑end via the dashboard.
- API key authentication is implemented and protects all endpoints.
- Logs are clean; CORS works from localhost:3000; no secrets leak.
- PR includes a short changelog summarizing endpoints added.
