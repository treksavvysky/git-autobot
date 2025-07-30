import typer
from typing_extensions import Annotated

app = typer.Typer()

def version_callback(value: bool):
    if value:
        print("0.1.0")
        raise typer.Exit()

@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
):
    """
    Git Autobot CLI
    """
    pass

if __name__ == "__main__":
    app()
