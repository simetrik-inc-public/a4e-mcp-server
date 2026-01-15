# Import dependencies
from typing import Optional
import typer
from .cli_commands import dev, init, add, list, validate, deploy, info, remove, update, mcp

# Version from pyproject.toml
__version__ = "0.1.0"


def version_callback(value: bool):
    if value:
        typer.echo(f"a4e-mcp-server {__version__}")
        raise typer.Exit()


# Initialize the cli app
app = typer.Typer(
    no_args_is_help=True,
    add_completion=True,
    help="A4E CLI - Create and manage conversational AI agents",
)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version and exit"
    ),
):
    """A4E CLI - Create and manage conversational AI agents."""
    pass

# Command groups for the cli
app.add_typer(dev.app, name="dev", help="Development server commands")
app.add_typer(init.app, name="init", help="Initialize a new agent project")
app.add_typer(add.app, name="add", help="Add tools, views, or skills")
app.add_typer(list.app, name="list", help="List tools, views, or skills")
app.add_typer(update.app, name="update", help="Update tools, views, or skills")
app.add_typer(remove.app, name="remove", help="Remove tools, views, or skills")
app.add_typer(validate.app, name="validate", help="Validate agent project")
app.add_typer(deploy.app, name="deploy", help="Deploy agent to production")
app.add_typer(info.app, name="info", help="Display agent information")
app.add_typer(mcp.app, name="mcp", help="Configure MCP server for IDEs")

if __name__ == "__main__":
    app()
