# Import dependencies
import typer
from .cli_commands import dev, init, add, list, validate, deploy, info, remove, update

# Initialize the cli app
app = typer.Typer(
    no_args_is_help=True,
    add_completion=True,
    help="A4E CLI - Create and manage conversational AI agents",
)

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

if __name__ == "__main__":
    app()
