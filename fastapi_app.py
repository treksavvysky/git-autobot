from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from github import Github, GithubException
from pydantic import BaseModel
import os

class Repository(BaseModel):
    name: str
    full_name: str
    html_url: str

app = FastAPI(title="Git Autobot GitHub API")

def get_github_client(token: Optional[str] = Query(default=None, description="GitHub personal access token")) -> Github:
    token = token or os.getenv("GITHUB_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="GitHub token required")
    return Github(token)

@app.get("/repos", response_model=List[Repository], summary="List user repositories")
def list_repositories(gh: Github = Depends(get_github_client)) -> List[Repository]:
    try:
        user = gh.get_user()
        repos = [Repository(name=r.name, full_name=r.full_name, html_url=r.html_url) for r in user.get_repos()]
        return repos
    except GithubException as e:
        status = getattr(e, "status", 500)
        message = getattr(e, "data", {}).get("message") if hasattr(e, "data") else str(e)
        raise HTTPException(status_code=status, detail=message)
