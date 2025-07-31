import typer
from typing_extensions import Annotated

from .commands.repo import repo_app
from .commands.git_ops import git_app

app = typer.Typer(
    help="Git Autobot - A developer CLI tool to streamline git workflows",
    no_args_is_help=True
)

def version_callback(value: bool):
    if value:
        print("git-autobot version 0.2.0")
        raise typer.Exit()

@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=version_callback, is_eager=True, help="Show version"),
    ] = None,
):
    """
    Git Autobot CLI - Streamline your git workflows
    
    A powerful command-line tool for managing multiple git repositories,
    automating common git operations, and integrating with GitHub.
    """
    pass

# Add command groups
app.add_typer(repo_app, name="repo", help="Repository management commands")
app.add_typer(git_app, name="git", help="Git operation commands")

if __name__ == "__main__":
    app()
