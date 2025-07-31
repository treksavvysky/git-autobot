"""Repository management commands."""

import typer
from typing import Optional, List
from pathlib import Path

from ..core.config import config
from ..core.git_ops import GitManager
from rich.console import Console

console = Console()
repo_app = typer.Typer(help="Repository management commands")


@repo_app.command("add")
def add_repo(
    alias: str = typer.Argument(..., help="Alias for the repository"),
    path: str = typer.Argument(..., help="Path to the repository"),
    github_repo: Optional[str] = typer.Option(None, "--github", "-g", help="GitHub repo name (user/repo)"),
    branches: Optional[str] = typer.Option(None, "--branches", "-b", help="Important branches (comma-separated)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Git remote URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Repository description"),
):
    """Add a repository to the configuration."""
    
    # Validate path
    repo_path = Path(path).expanduser().resolve()
    if not repo_path.exists():
        console.print(f"[red]Error: Path '{repo_path}' does not exist[/red]")
        raise typer.Exit(1)
    
    # Check if it's a valid git repository
    git_manager = GitManager(repo_path)
    if not git_manager.is_valid_repo():
        console.print(f"[red]Error: '{repo_path}' is not a valid Git repository[/red]")
        raise typer.Exit(1)
    
    # Parse branches
    branch_list = []
    if branches:
        branch_list = [b.strip() for b in branches.split(",") if b.strip()]
    
    # Auto-detect GitHub repo if not provided
    if not github_repo and not url:
        try:
            repo = git_manager.repo
            if hasattr(repo.remotes, 'origin'):
                origin_url = repo.remotes.origin.url
                # Try to extract GitHub repo name from URL
                if "github.com" in origin_url:
                    if origin_url.startswith("git@github.com:"):
                        github_repo = origin_url.replace("git@github.com:", "").replace(".git", "")
                    elif "github.com/" in origin_url:
                        github_repo = origin_url.split("github.com/")[-1].replace(".git", "")
                    url = origin_url
        except:
            pass
    
    # Add to configuration
    success = config.add_repo(
        alias=alias,
        path=str(repo_path),
        github_repo_name=github_repo,
        branches=branch_list,
        url=url,
        description=description or ""
    )
    
    if not success:
        raise typer.Exit(1)


@repo_app.command("remove")
def remove_repo(
    alias: str = typer.Argument(..., help="Alias of the repository to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation"),
):
    """Remove a repository from the configuration."""
    
    # Check if repository exists
    repo_config = config.get_repo(alias)
    if not repo_config:
        console.print(f"[red]Repository alias '{alias}' not found[/red]")
        raise typer.Exit(1)
    
    # Confirmation unless forced
    if not force:
        path = repo_config.get("path", "")
        if not typer.confirm(f"Remove repository '{alias}' ({path}) from configuration?"):
            console.print("Operation cancelled")
            raise typer.Exit(0)
    
    success = config.remove_repo(alias)
    if not success:
        raise typer.Exit(1)


@repo_app.command("list")
def list_repos():
    """List all configured repositories."""
    config.list_repos()


@repo_app.command("show")
def show_repo(
    alias: str = typer.Argument(..., help="Alias of the repository to show"),
):
    """Show detailed information about a specific repository."""
    
    repo_config = config.get_repo(alias)
    if not repo_config:
        console.print(f"[red]Repository alias '{alias}' not found[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold cyan]Repository: {alias}[/bold cyan]")
    console.print(f"Path: {repo_config.get('path', 'N/A')}")
    console.print(f"GitHub Repo: {repo_config.get('github_repo_name', 'N/A')}")
    console.print(f"URL: {repo_config.get('url', 'N/A')}")
    console.print(f"Description: {repo_config.get('description', 'N/A')}")
    
    branches = repo_config.get('branches', [])
    if branches:
        console.print(f"Important Branches: {', '.join(branches)}")
    else:
        console.print("Important Branches: None configured")


@repo_app.command("update")
def update_repo(
    alias: str = typer.Argument(..., help="Alias of the repository to update"),
    github_repo: Optional[str] = typer.Option(None, "--github", "-g", help="GitHub repo name (user/repo)"),
    branches: Optional[str] = typer.Option(None, "--branches", "-b", help="Important branches (comma-separated)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Git remote URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Repository description"),
):
    """Update repository configuration."""
    
    repo_config = config.get_repo(alias)
    if not repo_config:
        console.print(f"[red]Repository alias '{alias}' not found[/red]")
        raise typer.Exit(1)
    
    # Update only provided fields
    updates = {}
    if github_repo is not None:
        updates["github_repo_name"] = github_repo
    if url is not None:
        updates["url"] = url
    if description is not None:
        updates["description"] = description
    if branches is not None:
        updates["branches"] = [b.strip() for b in branches.split(",") if b.strip()]
    
    if not updates:
        console.print("[yellow]No updates specified[/yellow]")
        raise typer.Exit(0)
    
    # Apply updates
    updated_config = {**repo_config, **updates}
    success = config.add_repo(alias, updated_config["path"], **{k: v for k, v in updated_config.items() if k != "path"})
    
    if success:
        console.print(f"[green]✓[/green] Repository '{alias}' updated")
    else:
        raise typer.Exit(1)
