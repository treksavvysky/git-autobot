# NEXT STEPS — Repository Dashboard Backend

The following backlog captures recommended follow-up work now that the cockpit-style API scaffolding is in place.

## Git & GitHub Integrations
- Replace stubbed git write operations (clone, pull, push, stash, commit, checkout, reset, cherry-pick) with real GitPython commands gated by safety checks.
- Implement remote branch creation/deletion and stale-branch pruning via the GitHub API (today the endpoints return placeholders).
- Wire up PR creation to call GitHub's REST API and support draft PRs, reviewers, and labels.
- Enrich sync-status by comparing local and remote branches and surfacing divergence details.

## Documentation & DX
- Generate OpenAPI examples for every endpoint and publish them alongside the dashboard docs.
- Document required environment variables and expected directory layout for local repositories.
- Add how-to guides for configuring GitHub tokens and rotating credentials.

## Persistence & Storage
- Migrate the JSON state store to SQLite (or another embedded DB) for notes, snippets, and recurring tasks.
- Add migrations/versioning to the store so schema updates do not break saved data.
- Provide import/export tooling for dashboard notes/snippets/tasks.

## CI/CD & Health Metrics
- Connect CI endpoints to GitHub Actions/Checks APIs and surface workflow step results.
- Replace stubbed coverage/docker responses with real data from artifact storage or third-party services.
- Expand health checks to include dependency vulnerabilities, release cadence, and issue triage metrics.

## AI Assistant
- Integrate with the planned AI backend (OpenAI/Azure/Anthropic) and stream responses to the dashboard.
- Add context enrichment (e.g., latest CI failures, active PRs) before sending prompts.
- Support asynchronous background generation with websocket/WebPush updates.

## Testing & Observability
- Add unit tests for each router/service pair with mocked Git/GitHub interactions.
- Introduce structured logging (JSON) and request/response tracing for observability.
- Enable rate limiting/throttling to protect against abusive clients.
