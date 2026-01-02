# a4e/cli_commands/info.py
"""
Command for displaying agent information.
"""

import typer
import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Create a 'Typer' app for the 'info' command
app = typer.Typer(
    no_args_is_help=False,
    help="Display information about your agent.",
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
def info(
    ctx: typer.Context,
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
) -> None:
    """
    Display information about the agent.

    Shows metadata, structure, and statistics about the agent.

    Example:
        a4e info
        a4e info --agent my-agent --json
    """
    # If a subcommand is being invoked, skip the callback logic
    if ctx.invoked_subcommand is not None:
        return

    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    try:
        from ..tools.project.get_agent_info import get_agent_info as mcp_get_agent_info

        result = mcp_get_agent_info(agent_name=str(agent_dir))

        # Handle response (get_agent_info returns {"agent_id", "metadata", "path"} or {"error"})
        if "error" not in result:
            if json_output:
                console.print(json.dumps(result, indent=2))
                return

            # Display panel with basic info
            metadata = result.get("metadata", {})

            console.print(Panel.fit(
                f"[bold cyan]{metadata.get('display_name', agent_dir.name)}[/bold cyan]\n"
                f"[dim]{metadata.get('description', 'No description')}[/dim]\n\n"
                f"[bold]ID:[/bold] {metadata.get('id', agent_dir.name)}\n"
                f"[bold]Category:[/bold] {metadata.get('category', 'Unknown')}\n"
                f"[bold]Path:[/bold] {agent_dir}",
                title="Agent Info",
                border_style="blue"
            ))

            # Structure summary
            structure = result.get("structure", {})

            table = Table(title="Structure Summary")
            table.add_column("Component", style="cyan")
            table.add_column("Count", justify="right")

            table.add_row("Tools", str(structure.get("tools_count", 0)))
            table.add_row("Views", str(structure.get("views_count", 0)))
            table.add_row("Skills", str(structure.get("skills_count", 0)))
            table.add_row("Prompts", str(structure.get("prompts_count", 0)))

            console.print("")
            console.print(table)

            # List items if present
            if structure.get("tools"):
                console.print("\n[bold]Tools:[/bold]")
                for tool in structure.get("tools", []):
                    console.print(f"  • {tool}")

            if structure.get("views"):
                console.print("\n[bold]Views:[/bold]")
                for view in structure.get("views", []):
                    console.print(f"  • {view}")

            if structure.get("skills"):
                console.print("\n[bold]Skills:[/bold]")
                for skill in structure.get("skills", []):
                    console.print(f"  • {skill}")

        else:
            console.print(f"[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("instructions")
def instructions(
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
) -> None:
    """
    Show instructions for AI agents on how to use A4E tools.

    This displays the comprehensive documentation that AI assistants
    (like Claude, Cursor, etc.) use to understand how to create A4E agents.

    Example:
        a4e info instructions
        a4e info instructions --json
    """
    try:
        from ..tools.project.get_instructions import get_instructions as mcp_get_instructions

        result = mcp_get_instructions()

        if result.get("success"):
            if json_output:
                console.print(json.dumps(result, indent=2))
                return

            # Display the instructions with nice formatting
            console.print(Panel.fit(
                "[bold cyan]A4E Agent Creator - AI Instructions[/bold cyan]\n\n"
                "These instructions are provided to AI assistants when they use\n"
                "the A4E MCP tools to create agents.",
                border_style="blue"
            ))

            # Display quick reference
            quick_ref = result.get("quick_reference", {})

            table = Table(title="Quick Reference")
            table.add_column("Item", style="cyan")
            table.add_column("Value")

            table.add_row("Workflow", " → ".join(quick_ref.get("workflow", [])))
            table.add_row("Parameter Types", ", ".join(quick_ref.get("parameter_types", [])))
            table.add_row("Templates", ", ".join(quick_ref.get("templates", [])))

            naming = quick_ref.get("naming", {})
            table.add_row("agent_name", naming.get("agent_name", ""))
            table.add_row("tool_name", naming.get("tool_name", ""))
            table.add_row("view_id", naming.get("view_id", ""))
            table.add_row("skill_id", naming.get("skill_id", ""))

            console.print("")
            console.print(table)

            # Print the full instructions
            console.print("\n[bold]Full Instructions:[/bold]\n")
            console.print(result.get("instructions", ""))

        else:
            console.print(f"[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
