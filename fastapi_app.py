from __future__ import annotations

import logging
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from github import Github

from routes import ai, branches, ci, issues, local, meta, notes, pulls, repos, snippets
from services.config import get_settings


logger = logging.getLogger("git-autobot.api")
logging.basicConfig(level=logging.INFO)

settings = get_settings()
LOCAL_REPOS_DIR = settings.local_repos_dir

app = FastAPI(title="Git Autobot GitHub API", version="0.1.0")

allow_credentials = False if "*" in settings.allowed_origins else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logger(request: Request, call_next: Callable[[Request], Response]) -> Response:
    logger.info("%s %s", request.method, request.url.path)
    response = await call_next(request)
    response.headers.setdefault("Access-Control-Allow-Origin", settings.allowed_origins[0] if settings.allowed_origins else "*")
    return response


app.include_router(meta.router)
app.include_router(repos.router)
app.include_router(branches.router)
app.include_router(pulls.router)
app.include_router(issues.router)
app.include_router(ci.router)
app.include_router(ai.router)
app.include_router(notes.router)
app.include_router(snippets.router)
app.include_router(local.router)
