"""Git operations module."""

import os
from pathlib import Path
from typing import Optional, List, Tuple
from git import Repo, InvalidGitRepositoryError, GitCommandError
from rich.console import Console
from rich.table import Table

console = Console()

class GitManager:
    """Manages Git operations for repositories."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).expanduser().resolve()
        self._repo: Optional[Repo] = None
    
    @property
    def repo(self) -> Repo:
        """Get or create Git repository instance."""
        if self._repo is None:
            try:
                self._repo = Repo(self.repo_path)
            except InvalidGitRepositoryError:
                raise ValueError(f"'{self.repo_path}' is not a valid Git repository")
        return self._repo
    
    def is_valid_repo(self) -> bool:
        """Check if the path contains a valid Git repository."""
        try:
            Repo(self.repo_path)
            return True
        except InvalidGitRepositoryError:
            return False
    
    def get_status(self) -> dict:
        """Get repository status information."""
        try:
            repo = self.repo
            
            status = {
                "path": str(self.repo_path),
                "branch": repo.active_branch.name if repo.active_branch else "HEAD",
                "dirty": repo.is_dirty(untracked_files=True),
                "untracked_files": [item.a_path for item in repo.index.diff(None)],
                "modified_files": [item.a_path for item in repo.index.diff("HEAD")],
                "staged_files": [item.a_path for item in repo.index.diff("HEAD").iter_change_type('A')],
                "ahead": 0,
                "behind": 0
            }
            
            # Check ahead/behind status
            try:
                tracking_branch = repo.active_branch.tracking_branch()
                if tracking_branch:
                    ahead_behind = repo.iter_commits(f'{tracking_branch}..{repo.active_branch}')
                    status["ahead"] = sum(1 for _ in ahead_behind)
                    
                    behind_ahead = repo.iter_commits(f'{repo.active_branch}..{tracking_branch}')
                    status["behind"] = sum(1 for _ in behind_ahead)
            except:
                pass
            
            return status
            
        except Exception as e:
            console.print(f"[red]Error getting repository status: {e}[/red]")
            return {}
    
    def get_branches(self) -> dict:
        """Get information about local and remote branches."""
        try:
            repo = self.repo
            
            local_branches = [branch.name for branch in repo.heads]
            remote_branches = []
            
            # Get remote branches
            for remote in repo.remotes:
                try:
                    for ref in remote.refs:
                        if not ref.name.endswith('/HEAD'):
                            remote_branches.append(ref.name)
                except:
                    pass
            
            current_branch = repo.active_branch.name if repo.active_branch else "HEAD"
            
            return {
                "current": current_branch,
                "local": local_branches,
                "remote": remote_branches
            }
            
        except Exception as e:
            console.print(f"[red]Error getting branch information: {e}[/red]")
            return {}
    
    def stage_all(self) -> bool:
        """Stage all changes in the repository."""
        try:
            self.repo.git.add(all=True)
            console.print("[green]✓[/green] All changes staged")
            return True
        except GitCommandError as e:
            console.print(f"[red]Error staging changes: {e}[/red]")
            return False
    
    def commit(self, message: str) -> bool:
        """Commit staged changes with the given message."""
        try:
            if not self.repo.is_dirty():
                console.print("[yellow]No changes to commit[/yellow]")
                return False
            
            self.repo.index.commit(message)
            console.print(f"[green]✓[/green] Changes committed: '{message}'")
            return True
            
        except GitCommandError as e:
            console.print(f"[red]Error committing changes: {e}[/red]")
            return False
    
    def push(self, remote: str = "origin") -> bool:
        """Push changes to the specified remote."""
        try:
            origin = self.repo.remote(name=remote)
            origin.push()
            console.print(f"[green]✓[/green] Changes pushed to {remote}")
            return True
            
        except GitCommandError as e:
            console.print(f"[red]Error pushing to {remote}: {e}[/red]")
            return False
    
    def pull(self, remote: str = "origin") -> bool:
        """Pull changes from the specified remote."""
        try:
            origin = self.repo.remote(name=remote)
            pull_info = origin.pull()
            
            for info in pull_info:
                if info.flags & info.ERROR:
                    console.print(f"[red]Error during pull: {info.ref}[/red]")
                    return False
                elif info.flags & info.REJECTED:
                    console.print(f"[yellow]Pull rejected: {info.ref}[/yellow]")
                    return False
            
            console.print(f"[green]✓[/green] Changes pulled from {remote}")
            return True
            
        except GitCommandError as e:
            console.print(f"[red]Error pulling from {remote}: {e}[/red]")
            return False
    
    def checkout_branch(self, branch_name: str, create: bool = False) -> bool:
        """Checkout a branch, optionally creating it."""
        try:
            repo = self.repo
            
            if create:
                if branch_name in [branch.name for branch in repo.heads]:
                    console.print(f"[yellow]Branch '{branch_name}' already exists[/yellow]")
                    return False
                
                new_branch = repo.create_head(branch_name)
                new_branch.checkout()
                console.print(f"[green]✓[/green] Created and checked out branch '{branch_name}'")
            else:
                # Try to checkout existing local branch
                if branch_name in [branch.name for branch in repo.heads]:
                    repo.heads[branch_name].checkout()
                    console.print(f"[green]✓[/green] Checked out branch '{branch_name}'")
                else:
                    console.print(f"[red]Branch '{branch_name}' not found[/red]")
                    return False
            
            return True
            
        except GitCommandError as e:
            console.print(f"[red]Error checking out branch '{branch_name}': {e}[/red]")
            return False


def display_status_table(status: dict) -> None:
    """Display repository status in a formatted table."""
    if not status:
        return
    
    table = Table(title=f"Repository Status: {status.get('path', '')}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    # Basic info
    table.add_row("Current Branch", status.get("branch", "Unknown"))
    table.add_row("Working Tree", "Dirty" if status.get("dirty") else "Clean")
    
    # Ahead/behind info
    if status.get("ahead", 0) > 0 or status.get("behind", 0) > 0:
        ahead_behind = f"↑{status.get('ahead', 0)} ↓{status.get('behind', 0)}"
        table.add_row("Ahead/Behind", ahead_behind)
    
    # File counts
    if status.get("modified_files"):
        table.add_row("Modified Files", str(len(status["modified_files"])))
    if status.get("untracked_files"):
        table.add_row("Untracked Files", str(len(status["untracked_files"])))
    if status.get("staged_files"):
        table.add_row("Staged Files", str(len(status["staged_files"])))
    
    console.print(table)


def display_branches_table(branches: dict) -> None:
    """Display branch information in a formatted table."""
    if not branches:
        return
    
    table = Table(title="Branch Information")
    table.add_column("Type", style="cyan")
    table.add_column("Branches", style="white")
    
    current = branches.get("current", "")
    local_branches = branches.get("local", [])
    remote_branches = branches.get("remote", [])
    
    # Highlight current branch
    local_display = []
    for branch in local_branches:
        if branch == current:
            local_display.append(f"[bold green]{branch}[/bold green] (current)")
        else:
            local_display.append(branch)
    
    table.add_row("Local", "\n".join(local_display))
    if remote_branches:
        table.add_row("Remote", "\n".join(remote_branches))
    
    console.print(table)
