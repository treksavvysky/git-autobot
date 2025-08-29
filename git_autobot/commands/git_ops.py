"""Git operation commands."""

import typer
from typing import Optional
from pathlib import Path

from ..core.config import config
from ..core.git_ops import GitManager, display_status_table, display_branches_table
from rich.console import Console

console = Console()
git_app = typer.Typer(help="Git operation commands")


def get_repo_path(alias: Optional[str] = None, path: Optional[str] = None) -> str:
    """Get repository path from alias or direct path."""
    if alias:
        repo_config = config.get_repo(alias)
        if not repo_config:
            console.print(f"[red]Repository alias '{alias}' not found[/red]")
            raise typer.Exit(1)
        return repo_config["path"]
    elif path:
        return str(Path(path).expanduser().resolve())
    else:
        # Try current directory
        cwd = Path.cwd()
        git_manager = GitManager(cwd)
        if git_manager.is_valid_repo():
            return str(cwd)
        else:
            console.print("[red]Error: Not in a git repository and no alias/path specified[/red]")
            console.print("Use --alias to specify a configured repository or --path for a direct path")
            raise typer.Exit(1)


@git_app.command("status")
def status(
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="Repository alias"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Repository path"),
):
    """Show repository status."""
    
    repo_path = get_repo_path(alias, path)
    git_manager = GitManager(repo_path)
    
    if not git_manager.is_valid_repo():
        console.print(f"[red]'{repo_path}' is not a valid Git repository[/red]")
        raise typer.Exit(1)
    
    status_info = git_manager.get_status()
    display_status_table(status_info)


@git_app.command("branches")
def branches(
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="Repository alias"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Repository path"),
):
    """Show branch information."""
    
    repo_path = get_repo_path(alias, path)
    git_manager = GitManager(repo_path)
    
    if not git_manager.is_valid_repo():
        console.print(f"[red]'{repo_path}' is not a valid Git repository[/red]")
        raise typer.Exit(1)
    
    branch_info = git_manager.get_branches()
    display_branches_table(branch_info)


@git_app.command("add")
def add_changes(
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="Repository alias"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Repository path"),
):
    """Stage all changes in the repository."""
    
    repo_path = get_repo_path(alias, path)
    git_manager = GitManager(repo_path)
    
    if not git_manager.is_valid_repo():
        console.print(f"[red]'{repo_path}' is not a valid Git repository[/red]")
        raise typer.Exit(1)
    
    success = git_manager.stage_all()
    if not success:
        raise typer.Exit(1)


@git_app.command("commit")
def commit_changes(
    message: str = typer.Argument(..., help="Commit message"),
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="Repository alias"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Repository path"),
    add: bool = typer.Option(False, "--add", help="Stage all changes before committing"),
):
    """Commit changes with a message."""
    
    repo_path = get_repo_path(alias, path)
    git_manager = GitManager(repo_path)
    
    if not git_manager.is_valid_repo():
        console.print(f"[red]'{repo_path}' is not a valid Git repository[/red]")
        raise typer.Exit(1)
    
    # Stage changes if requested
    if add:
        if not git_manager.stage_all():
            raise typer.Exit(1)
    
    success = git_manager.commit(message)
    if not success:
        raise typer.Exit(1)


@git_app.command("push")
def push_changes(
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="Repository alias"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Repository path"),
    remote: str = typer.Option("origin", "--remote", "-r", help="Remote to push to"),
):
    """Push changes to remote repository."""
    
    repo_path = get_repo_path(alias, path)
    git_manager = GitManager(repo_path)
    
    if not git_manager.is_valid_repo():
        console.print(f"[red]'{repo_path}' is not a valid Git repository[/red]")
        raise typer.Exit(1)
    
    success = git_manager.push(remote)
    if not success:
        raise typer.Exit(1)


@git_app.command("pull")
def pull_changes(
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="Repository alias"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Repository path"),
    remote: str = typer.Option("origin", "--remote", "-r", help="Remote to pull from"),
):
    """Pull changes from remote repository."""
    
    repo_path = get_repo_path(alias, path)
    git_manager = GitManager(repo_path)
    
    if not git_manager.is_valid_repo():
        console.print(f"[red]'{repo_path}' is not a valid Git repository[/red]")
        raise typer.Exit(1)
    
    success = git_manager.pull(remote)
    if not success:
        raise typer.Exit(1)


@git_app.command("checkout")
def checkout_branch(
    branch: str = typer.Argument(..., help="Branch name to checkout"),
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="Repository alias"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Repository path"),
    create: bool = typer.Option(False, "--create", "-c", help="Create the branch if it doesn't exist"),
):
    """Checkout a branch."""
    
    repo_path = get_repo_path(alias, path)
    git_manager = GitManager(repo_path)
    
    if not git_manager.is_valid_repo():
        console.print(f"[red]'{repo_path}' is not a valid Git repository[/red]")
        raise typer.Exit(1)
    
    success = git_manager.checkout_branch(branch, create)
    if not success:
        raise typer.Exit(1)


@git_app.command("quick-commit")
def quick_commit(
    message: str = typer.Argument(..., help="Commit message"),
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="Repository alias"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Repository path"),
    push: bool = typer.Option(False, "--push", help="Push after committing"),
):
    """Stage all changes, commit, and optionally push."""
    
    repo_path = get_repo_path(alias, path)
    git_manager = GitManager(repo_path)
    
    if not git_manager.is_valid_repo():
        console.print(f"[red]'{repo_path}' is not a valid Git repository[/red]")
        raise typer.Exit(1)
    
    # Stage all changes
    if not git_manager.stage_all():
        raise typer.Exit(1)
    
    # Commit
    if not git_manager.commit(message):
        raise typer.Exit(1)
    
    # Push if requested
    if push:
        if not git_manager.push():
            raise typer.Exit(1)
    
    console.print("[green]✓[/green] Quick commit completed successfully")


@git_app.command("sync")
def sync_repo(
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="Repository alias"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Repository path"),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Commit message for local changes"),
):
    """Sync repository: commit local changes, pull, and push."""
    
    repo_path = get_repo_path(alias, path)
    git_manager = GitManager(repo_path)
    
    if not git_manager.is_valid_repo():
        console.print(f"[red]'{repo_path}' is not a valid Git repository[/red]")
        raise typer.Exit(1)
    
    # Check if there are local changes
    status_info = git_manager.get_status()
    has_changes = status_info.get("dirty", False)
    
    if has_changes:
        if not message:
            message = "Auto-sync: commit local changes"
        
        console.print("[blue]Committing local changes...[/blue]")
        if not git_manager.stage_all():
            raise typer.Exit(1)
        if not git_manager.commit(message):
            raise typer.Exit(1)
    
    # Pull latest changes
    console.print("[blue]Pulling latest changes...[/blue]")
    if not git_manager.pull():
        raise typer.Exit(1)
    
    # Push local commits
    console.print("[blue]Pushing changes...[/blue]")
    if not git_manager.push():
        raise typer.Exit(1)
    
    console.print("[green]✓[/green] Repository synchronized successfully")
