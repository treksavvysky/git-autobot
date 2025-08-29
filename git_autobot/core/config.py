"""Configuration management for git-autobot."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from rich.console import Console
from rich.table import Table

console = Console()

class Config:
    """Manages repository configuration storage and retrieval."""
    
    def __init__(self, config_file: str = "repo_config.json"):
        self.config_file = Path(config_file)
        self._config_cache: Optional[Dict[str, Any]] = None
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file with caching."""
        if self._config_cache is not None:
            return self._config_cache
            
        if not self.config_file.exists():
            self._config_cache = {}
            return self._config_cache
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            # Validate structure
            if not isinstance(config, dict):
                console.print(f"[yellow]Warning: Configuration in {self.config_file} is not a dictionary.[/yellow]")
                self._config_cache = {}
                return self._config_cache
                
            # Validate each entry
            for alias, details in list(config.items()):
                if not isinstance(details, dict) or "path" not in details:
                    console.print(f"[yellow]Warning: Invalid entry for alias '{alias}'. Removing from config.[/yellow]")
                    del config[alias]
                    
            self._config_cache = config
            return self._config_cache
            
        except (IOError, json.JSONDecodeError) as e:
            console.print(f"[red]Error loading configuration: {e}[/red]")
            self._config_cache = {}
            return self._config_cache
    
    def save(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Update cache
            self._config_cache = config.copy()
            return True
            
        except IOError as e:
            console.print(f"[red]Error saving configuration: {e}[/red]")
            return False
    
    def add_repo(self, alias: str, path: str, **kwargs) -> bool:
        """Add or update a repository configuration."""
        if not alias or not path:
            console.print("[red]Error: Both alias and path are required.[/red]")
            return False
        
        config = self.load()
        
        repo_entry = {
            "path": str(Path(path).expanduser().resolve()),
            "branches": kwargs.get("branches", []),
            "url": kwargs.get("url"),
            "github_repo_name": kwargs.get("github_repo_name"),
            "description": kwargs.get("description", "")
        }
        
        # Remove None values
        repo_entry = {k: v for k, v in repo_entry.items() if v is not None}
        
        config[alias] = repo_entry
        
        if self.save(config):
            console.print(f"[green]✓[/green] Repository '{alias}' added to configuration")
            return True
        return False
    
    def get_repo(self, alias: str) -> Optional[Dict[str, Any]]:
        """Get repository configuration by alias."""
        config = self.load()
        return config.get(alias)
    
    def remove_repo(self, alias: str) -> bool:
        """Remove a repository from configuration."""
        config = self.load()
        
        if alias not in config:
            console.print(f"[red]Repository alias '{alias}' not found.[/red]")
            return False
        
        del config[alias]
        
        if self.save(config):
            console.print(f"[green]✓[/green] Repository '{alias}' removed from configuration")
            return True
        return False
    
    def list_repos(self) -> None:
        """Display all repositories in a formatted table."""
        config = self.load()
        
        if not config:
            console.print("[yellow]No repositories found in configuration.[/yellow]")
            return
        
        table = Table(title="Configured Repositories")
        table.add_column("Alias", style="cyan", no_wrap=True)
        table.add_column("Path", style="magenta")
        table.add_column("GitHub Repo", style="green")
        table.add_column("Branches", style="blue")
        table.add_column("Description", style="white")
        
        for alias, details in config.items():
            path = details.get("path", "")
            github_repo = details.get("github_repo_name", "")
            branches = ", ".join(details.get("branches", []))
            description = details.get("description", "")
            
            table.add_row(alias, path, github_repo, branches, description)
        
        console.print(table)
    
    def clear_cache(self):
        """Clear the configuration cache."""
        self._config_cache = None


# Global config instance
config = Config()
