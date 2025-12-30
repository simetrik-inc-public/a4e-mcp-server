# a4e/cli_commands/validate.py
"""
Command for validating an agent project.
"""

import typer
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Create a 'Typer' app for the 'validate' command
app = typer.Typer(
    no_args_is_help=False,
    help="Validate your agent project for errors and warnings.",
)


def find_agent_dir(agent_name: Optional[str] = None) -> Optional[Path]:
    """Find the agent directory from name or current working directory."""
    cwd = Path.cwd()

    if agent_name:
        if Path(agent_name).is_absolute() and Path(agent_name).exists():
            return Path(agent_name)
        if (cwd / agent_name).exists():
            return cwd / agent_name
        agent_store = cwd / "file-store" / "agent-store" / agent_name
        if agent_store.exists():
            return agent_store
        return None

    if (cwd / "agent.py").exists() and (cwd / "metadata.json").exists():
        return cwd

    return None


@app.callback(invoke_without_command=True)
def validate(
    ctx: typer.Context,
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
    strict: bool = typer.Option(
        False, "--strict", "-s", help="Treat warnings as errors"
    ),
) -> None:
    """
    Validate the agent project structure and code.

    Checks for:
    - Required files (agent.py, metadata.json, prompts/agent.md, etc.)
    - Python syntax errors
    - Type hints on public functions
    - Schema existence
    - Skill dependencies (views, tools)

    Example:
        a4e validate
        a4e validate --agent my-agent --strict
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    console.print(Panel.fit(
        f"[bold]Validating agent:[/bold] {agent_dir.name}",
        border_style="blue"
    ))

    try:
        from ..tools.validation.validate import validate as mcp_validate

        result = mcp_validate(agent_name=str(agent_dir))

        if result.get("success"):
            errors = result.get("errors", [])
            warnings = result.get("warnings", [])

            # Show errors
            if errors:
                console.print(f"\n[red bold]Errors ({len(errors)}):[/red bold]")
                for error in errors:
                    console.print(f"  [red]✗[/red] {error}")

            # Show warnings
            if warnings:
                console.print(f"\n[yellow bold]Warnings ({len(warnings)}):[/yellow bold]")
                for warning in warnings:
                    console.print(f"  [yellow]⚠[/yellow] {warning}")

            # Summary
            console.print("")
            if errors:
                console.print(f"[red bold]Validation failed with {len(errors)} error(s)[/red bold]")
                raise typer.Exit(code=1)
            elif warnings and strict:
                console.print(f"[yellow bold]Validation failed with {len(warnings)} warning(s) (strict mode)[/yellow bold]")
                raise typer.Exit(code=1)
            elif warnings:
                console.print(f"[green]✓ Validation passed with {len(warnings)} warning(s)[/green]")
            else:
                console.print("[green bold]✓ Validation passed - no issues found![/green bold]")

        else:
            console.print(f"[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)
