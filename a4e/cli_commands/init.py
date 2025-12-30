# a4e/cli_commands/init.py
"""
Interactive project initialization command.
"""

import typer
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

# Create a 'Typer' app for the 'init' command
app = typer.Typer(
    no_args_is_help=False,
    help="Initialize a new A4E agent project with an interactive wizard.",
)

CATEGORIES = [
    "Concierge",
    "E-commerce",
    "Fitness & Health",
    "Education",
    "Entertainment",
    "Productivity",
    "Finance",
    "Customer Support",
    "General",
]

TEMPLATES = {
    "basic": "Minimal files only (agent.py, metadata.json, welcome view)",
    "with-tools": "Basic + example tool",
    "with-views": "Basic + example view",
    "full": "Basic + example tool + example view",
}


def validate_agent_name(name: str) -> bool:
    """Validate agent name format (lowercase, hyphens/underscores only)."""
    return name.replace("-", "").replace("_", "").isalnum() and name.islower()


@app.callback(invoke_without_command=True)
def init(
    ctx: typer.Context,
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Agent ID (lowercase, hyphens, e.g., 'nutrition-coach')"
    ),
    display_name: Optional[str] = typer.Option(
        None, "--display-name", "-d", help="Human-readable name"
    ),
    description: Optional[str] = typer.Option(
        None, "--description", help="Short description of the agent"
    ),
    category: Optional[str] = typer.Option(
        None, "--category", "-c", help="Agent category for marketplace"
    ),
    template: Optional[str] = typer.Option(
        None, "--template", "-t", help="Project template (basic, with-tools, with-views, full)"
    ),
    directory: Optional[str] = typer.Option(
        None, "--directory", help="Directory to create agent in (defaults to current directory)"
    ),
    non_interactive: bool = typer.Option(
        False, "--yes", "-y", help="Skip interactive prompts (requires all options)"
    ),
) -> None:
    """
    Initialize a new A4E agent project.

    Run without arguments for an interactive wizard, or pass all options for non-interactive mode.
    """
    console.print(Panel.fit(
        "[bold blue]A4E Agent Creator[/bold blue]\n"
        "Create a new conversational AI agent",
        border_style="blue"
    ))

    # Interactive mode - prompt for missing values
    if not non_interactive:
        # Agent name
        if not name:
            while True:
                name = Prompt.ask(
                    "\n[bold]Agent name[/bold] (lowercase, hyphens allowed)",
                    default="my-agent"
                )
                if validate_agent_name(name):
                    break
                console.print("[red]Invalid name. Use lowercase letters, numbers, and hyphens only.[/red]")

        # Display name
        if not display_name:
            default_display = name.replace("-", " ").replace("_", " ").title()
            display_name = Prompt.ask(
                "[bold]Display name[/bold]",
                default=default_display
            )

        # Description
        if not description:
            description = Prompt.ask(
                "[bold]Description[/bold]",
                default=f"A helpful {display_name} agent"
            )

        # Category selection
        if not category:
            console.print("\n[bold]Select a category:[/bold]")
            for i, cat in enumerate(CATEGORIES, 1):
                console.print(f"  [{i}] {cat}")

            while True:
                choice = Prompt.ask("Enter number", default="9")
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(CATEGORIES):
                        category = CATEGORIES[idx]
                        break
                except ValueError:
                    pass
                console.print("[red]Invalid selection. Please enter a number.[/red]")

        # Template selection
        if not template:
            console.print("\n[bold]Select a template:[/bold]")
            for i, (key, desc) in enumerate(TEMPLATES.items(), 1):
                console.print(f"  [{i}] {key}: {desc}")

            while True:
                choice = Prompt.ask("Enter number", default="1")
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(TEMPLATES):
                        template = list(TEMPLATES.keys())[idx]
                        break
                except ValueError:
                    pass
                console.print("[red]Invalid selection. Please enter a number.[/red]")

    # Validate all required fields
    if not all([name, display_name, description, category, template]):
        console.print("[red]Error: All fields are required. Use --yes for non-interactive mode only with all options.[/red]")
        raise typer.Exit(code=1)

    if not validate_agent_name(name):
        console.print("[red]Error: Agent name must be lowercase with hyphens/underscores only.[/red]")
        raise typer.Exit(code=1)

    if category not in CATEGORIES:
        console.print(f"[red]Error: Invalid category. Choose from: {', '.join(CATEGORIES)}[/red]")
        raise typer.Exit(code=1)

    if template not in TEMPLATES:
        console.print(f"[red]Error: Invalid template. Choose from: {', '.join(TEMPLATES.keys())}[/red]")
        raise typer.Exit(code=1)

    # Confirmation
    if not non_interactive:
        console.print("\n[bold]Creating agent with:[/bold]")
        console.print(f"  Name: {name}")
        console.print(f"  Display Name: {display_name}")
        console.print(f"  Description: {description}")
        console.print(f"  Category: {category}")
        console.print(f"  Template: {template}")

        if not Confirm.ask("\nProceed?", default=True):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(code=0)

    # Import and call the MCP tool function directly
    try:
        from ..tools.project.initialize_project import initialize_project

        # Set environment variable for directory if specified
        import os
        if directory:
            os.environ["A4E_WORKSPACE"] = str(Path(directory).resolve())

        result = initialize_project(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            template=template,
        )

        if result.get("success"):
            console.print(f"\n[green]✓ Agent '{name}' created successfully![/green]")
            console.print(f"  Path: {result.get('path')}")

            console.print("\n[bold]Next steps:[/bold]")
            for step in result.get("next_steps", []):
                console.print(f"  • {step}")

            console.print(f"\n  cd {name}")
            console.print("  a4e dev start")
        else:
            console.print(f"\n[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
