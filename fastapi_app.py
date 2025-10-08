from __future__ import annotations

import logging
import os
from typing import Callable

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from github import Github

from routes import ai, branches, ci, issues, local, meta, notes, pulls, repos, snippets
from services.auth import verify_api_key
from services.config import get_settings


logger = logging.getLogger("git-autobot.api")
logging.basicConfig(level=logging.INFO)

settings = get_settings()
LOCAL_REPOS_DIR = settings.local_repos_dir

server_url = os.getenv("API_SERVER_URL", "http://localhost:8000")
servers = [{"url": server_url}]

app = FastAPI(title="Git Autobot GitHub API", version="0.1.0", servers=servers)

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
    return response


app.include_router(meta.router)
app.include_router(repos.router, dependencies=[Depends(verify_api_key)])
app.include_router(branches.router, dependencies=[Depends(verify_api_key)])
app.include_router(pulls.router, dependencies=[Depends(verify_api_key)])
app.include_router(issues.router, dependencies=[Depends(verify_api_key)])
app.include_router(ci.router, dependencies=[Depends(verify_api_key)])
app.include_router(ai.router, dependencies=[Depends(verify_api_key)])
app.include_router(notes.router, dependencies=[Depends(verify_api_key)])
app.include_router(snippets.router, dependencies=[Depends(verify_api_key)])
app.include_router(local.router, dependencies=[Depends(verify_api_key)])
