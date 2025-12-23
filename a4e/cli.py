# Import dependencies
import typer
from .cli_commands import dev

# Initialize the cli app
app = typer.Typer(
    no_args_is_help=True,
    add_completion=True,
    help="This is a Cli for creating and creating your a4e agents. We are still testing",
)

# Command groups for the cli
app.add_typer(dev.app, name="dev")

if __name__ == "__main__":
    app()
