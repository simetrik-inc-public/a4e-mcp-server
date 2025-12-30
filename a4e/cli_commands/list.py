# a4e/cli_commands/list.py
"""
Commands for listing tools, views, and skills in an agent.
"""

import typer
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

console = Console()

# Create a 'Typer' app for the 'list' command group
app = typer.Typer(
    no_args_is_help=True,
    help="List tools, views, or skills in your agent.",
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


@app.command("tools")
def list_tools(
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed information"
    ),
) -> None:
    """
    List all tools in the agent.

    Example:
        a4e list tools
        a4e list tools --agent my-agent -v
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    try:
        from ..tools.agent_tools.list_tools import list_tools as mcp_list_tools

        result = mcp_list_tools(agent_name=str(agent_dir))

        # Handle response (list_tools returns {"tools": [...], "count": N})
        if "error" not in result:
            tools = result.get("tools", [])

            if not tools:
                console.print("[yellow]No tools found.[/yellow]")
                return

            table = Table(title=f"Tools ({len(tools)})")
            table.add_column("Name", style="cyan")
            table.add_column("File", style="dim")

            for tool in tools:
                # tools is a list of strings (tool names)
                table.add_row(tool, f"tools/{tool}.py")

            console.print(table)
        else:
            console.print(f"[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("views")
def list_views(
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed information"
    ),
) -> None:
    """
    List all views in the agent.

    Example:
        a4e list views
        a4e list views --agent my-agent -v
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    try:
        from ..tools.views.list_views import list_views as mcp_list_views

        result = mcp_list_views(agent_name=str(agent_dir))

        # Handle response (list_views returns {"views": [...], "count": N})
        if "error" not in result:
            views = result.get("views", [])

            if not views:
                console.print("[yellow]No views found.[/yellow]")
                return

            table = Table(title=f"Views ({len(views)})")
            table.add_column("ID", style="cyan")
            table.add_column("Path", style="dim")

            for view in views:
                # views is a list of strings (view names)
                table.add_row(view, f"views/{view}/view.tsx")

            console.print(table)
        else:
            console.print(f"[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("skills")
def list_skills(
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed information"
    ),
) -> None:
    """
    List all skills in the agent.

    Example:
        a4e list skills
        a4e list skills --agent my-agent -v
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    try:
        from ..tools.skills.list_skills import list_skills as mcp_list_skills

        result = mcp_list_skills(agent_name=str(agent_dir))

        # Handle response (list_skills returns {"skills": [...], "count": N})
        if "error" not in result:
            skills = result.get("skills", [])

            if not skills:
                console.print("[yellow]No skills found.[/yellow]")
                return

            table = Table(title=f"Skills ({len(skills)})")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            if verbose:
                table.add_column("Output View")
                table.add_column("Triggers")

            for skill in skills:
                if verbose:
                    triggers = ", ".join(skill.get("intent_triggers", [])[:3])
                    if len(skill.get("intent_triggers", [])) > 3:
                        triggers += "..."
                    table.add_row(
                        skill.get("id", ""),
                        skill.get("name", ""),
                        skill.get("output_view", ""),
                        triggers
                    )
                else:
                    table.add_row(skill.get("id", ""), skill.get("name", ""))

            console.print(table)
        else:
            console.print(f"[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("all")
def list_all(
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
) -> None:
    """
    List all tools, views, and skills in the agent.
    """
    console.print("[bold]Tools:[/bold]")
    list_tools(agent_name=agent_name, verbose=False)

    console.print("\n[bold]Views:[/bold]")
    list_views(agent_name=agent_name, verbose=False)

    console.print("\n[bold]Skills:[/bold]")
    list_skills(agent_name=agent_name, verbose=False)
