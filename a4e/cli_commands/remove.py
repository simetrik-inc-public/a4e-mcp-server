# a4e/cli_commands/remove.py
"""
Commands for removing tools, views, and skills from an agent.
"""

import typer
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

console = Console()

# Create a 'Typer' app for the 'remove' command group
app = typer.Typer(
    no_args_is_help=True,
    help="Remove tools, views, or skills from your agent.",
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


@app.command("tool")
def remove_tool(
    tool_name: str = typer.Argument(..., help="Name of the tool to remove"),
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
) -> None:
    """
    Remove a tool from the agent.

    Example:
        a4e remove tool calculate_bmi
        a4e remove tool calculate_bmi --yes
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    # Confirm removal
    if not yes:
        if not Confirm.ask(f"Remove tool '{tool_name}'?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(code=0)

    try:
        from ..tools.agent_tools.remove_tool import remove_tool as mcp_remove_tool

        result = mcp_remove_tool(
            tool_name=tool_name,
            agent_name=str(agent_dir),
        )

        if result.get("success"):
            console.print(f"[green]✓ Tool '{tool_name}' removed![/green]")
            console.print(f"  Removed: {result.get('removed_file')}")
        else:
            console.print(f"[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("view")
def remove_view(
    view_id: str = typer.Argument(..., help="ID of the view to remove"),
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
) -> None:
    """
    Remove a view from the agent.

    Note: The 'welcome' view cannot be removed as it's required.

    Example:
        a4e remove view results-display
        a4e remove view results-display --yes
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    # Warn about welcome view
    if view_id == "welcome":
        console.print("[red]Error: Cannot remove the 'welcome' view - it is required for all agents.[/red]")
        raise typer.Exit(code=1)

    # Confirm removal
    if not yes:
        if not Confirm.ask(f"Remove view '{view_id}'?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(code=0)

    try:
        from ..tools.views.remove_view import remove_view as mcp_remove_view

        result = mcp_remove_view(
            view_id=view_id,
            agent_name=str(agent_dir),
        )

        if result.get("success"):
            console.print(f"[green]✓ View '{view_id}' removed![/green]")
            console.print(f"  Removed: {result.get('removed_folder')}")
        else:
            console.print(f"[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("skill")
def remove_skill(
    skill_id: str = typer.Argument(..., help="ID of the skill to remove"),
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
) -> None:
    """
    Remove a skill from the agent.

    Note: The 'show_welcome' skill cannot be removed as it's required.

    Example:
        a4e remove skill show_results
        a4e remove skill show_results --yes
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    # Warn about show_welcome skill
    if skill_id == "show_welcome":
        console.print("[red]Error: Cannot remove the 'show_welcome' skill - it is required for all agents.[/red]")
        raise typer.Exit(code=1)

    # Confirm removal
    if not yes:
        if not Confirm.ask(f"Remove skill '{skill_id}'?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(code=0)

    try:
        from ..tools.skills.remove_skill import remove_skill as mcp_remove_skill

        result = mcp_remove_skill(
            skill_id=skill_id,
            agent_name=str(agent_dir),
        )

        if result.get("success"):
            console.print(f"[green]✓ Skill '{skill_id}' removed![/green]")
            console.print(f"  Removed: {result.get('removed_folder')}")
        else:
            console.print(f"[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)
