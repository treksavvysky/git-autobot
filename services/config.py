from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List, Optional


@dataclass
class Settings:
    """Runtime configuration derived from environment variables."""

    github_token: Optional[str]
    github_api_base: str
    local_repos_dir: Path
    allowed_origins: List[str]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Resolve runtime settings from the environment once per process."""

    base_dir = Path(__file__).resolve().parent.parent
    repo_path_env = os.getenv("REPO_PATH") or os.getenv("LOCAL_REPOS_DIR")
    if repo_path_env:
        local_repos_dir = Path(repo_path_env).expanduser().resolve()
    else:
        local_repos_dir = (base_dir / "local_repos").resolve()
    local_repos_dir.mkdir(parents=True, exist_ok=True)

    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    if allowed_origins_env.strip() == "*":
        allowed_origins = ["*"]
    else:
        allowed_origins = [
            origin.strip()
            for origin in allowed_origins_env.split(",")
            if origin.strip()
        ]
        if not allowed_origins:
            allowed_origins = ["http://localhost:3000"]

    return Settings(
        github_token=os.getenv("GITHUB_TOKEN"),
        github_api_base=os.getenv("GITHUB_API_BASE", "https://api.github.com"),
        local_repos_dir=local_repos_dir,
        allowed_origins=allowed_origins,
    )
