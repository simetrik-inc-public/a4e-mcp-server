# a4e/cli_commands/update.py
"""
Commands for updating tools, views, and skills in an agent.
"""

import typer
import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

# Create a 'Typer' app for the 'update' command group
app = typer.Typer(
    no_args_is_help=True,
    help="Update existing tools, views, or skills.",
)

TYPE_OPTIONS = ["string", "number", "integer", "boolean", "array", "object"]


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
def update_tool(
    tool_name: Optional[str] = typer.Argument(None, help="Name of the tool to update"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="New description"
    ),
    parameters_json: Optional[str] = typer.Option(
        None, "--parameters", "-p", help="New parameters as JSON string"
    ),
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path"
    ),
) -> None:
    """
    Update an existing tool's description or parameters.

    Example:
        a4e update tool calculate_bmi -d "New description"
        a4e update tool calculate_bmi -p '{"weight": "number", "height": "number"}'
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    # List available tools if none specified
    if not tool_name:
        tools_dir = agent_dir / "tools"
        if tools_dir.exists():
            available = [f.stem for f in tools_dir.glob("*.py") if f.stem != "__init__"]
            if available:
                console.print("[bold]Available tools:[/bold]")
                for t in available:
                    console.print(f"  • {t}")
            tool_name = Prompt.ask("[bold]Tool to update[/bold]")
        else:
            console.print("[red]No tools directory found[/red]")
            raise typer.Exit(code=1)

    if not description and not parameters_json:
        console.print("[yellow]What would you like to update?[/yellow]")
        update_desc = Confirm.ask("Update description?", default=False)
        if update_desc:
            description = Prompt.ask("New description")

        update_params = Confirm.ask("Update parameters?", default=False)
        if update_params:
            console.print("[dim]Enter parameters as JSON or use interactive mode[/dim]")
            parameters_json = Prompt.ask("Parameters JSON", default="{}")

    parameters = None
    if parameters_json:
        try:
            parameters = json.loads(parameters_json)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON for parameters[/red]")
            raise typer.Exit(code=1)

    try:
        from ..tools.agent_tools.update_tool import update_tool as mcp_update_tool

        result = mcp_update_tool(
            tool_name=tool_name,
            description=description,
            parameters=parameters,
            agent_name=str(agent_dir),
        )

        if result.get("success"):
            console.print(f"\n[green]✓ Tool '{tool_name}' updated![/green]")
            console.print(f"  Path: {result.get('path')}")
        else:
            console.print(f"\n[red]Error: {result.get('error')}[/red]")
            if result.get("fix"):
                console.print(f"  [yellow]Fix: {result.get('fix')}[/yellow]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("view")
def update_view(
    view_id: Optional[str] = typer.Argument(None, help="ID of the view to update"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="New description"
    ),
    props_json: Optional[str] = typer.Option(
        None, "--props", "-p", help="New props as JSON string"
    ),
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path"
    ),
) -> None:
    """
    Update an existing view's description or props.

    Example:
        a4e update view dashboard -d "New description"
        a4e update view dashboard -p '{"title": "string", "items": "array"}'
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    # List available views if none specified
    if not view_id:
        views_dir = agent_dir / "views"
        if views_dir.exists():
            available = [d.name for d in views_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
            if available:
                console.print("[bold]Available views:[/bold]")
                for v in available:
                    console.print(f"  • {v}")
            view_id = Prompt.ask("[bold]View to update[/bold]")
        else:
            console.print("[red]No views directory found[/red]")
            raise typer.Exit(code=1)

    if not description and not props_json:
        console.print("[yellow]What would you like to update?[/yellow]")
        update_desc = Confirm.ask("Update description?", default=False)
        if update_desc:
            description = Prompt.ask("New description")

        update_props = Confirm.ask("Update props?", default=False)
        if update_props:
            props_json = Prompt.ask("Props JSON", default="{}")

    props = None
    if props_json:
        try:
            props = json.loads(props_json)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON for props[/red]")
            raise typer.Exit(code=1)

    try:
        from ..tools.views.update_view import update_view as mcp_update_view

        result = mcp_update_view(
            view_id=view_id,
            description=description,
            props=props,
            agent_name=str(agent_dir),
        )

        if result.get("success"):
            console.print(f"\n[green]✓ View '{view_id}' updated![/green]")
            console.print(f"  Path: {result.get('path')}")
        else:
            console.print(f"\n[red]Error: {result.get('error')}[/red]")
            if result.get("fix"):
                console.print(f"  [yellow]Fix: {result.get('fix')}[/yellow]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("skill")
def update_skill(
    skill_id: Optional[str] = typer.Argument(None, help="ID of the skill to update"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New display name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    intent_triggers: Optional[str] = typer.Option(
        None, "--triggers", "-t", help="New comma-separated triggers"
    ),
    output_view: Optional[str] = typer.Option(None, "--view", "-v", help="New output view"),
    internal_tools: Optional[str] = typer.Option(
        None, "--tools", help="New comma-separated internal tools"
    ),
    requires_auth: Optional[bool] = typer.Option(None, "--auth/--no-auth", help="Requires auth"),
    agent_name: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent name/path"),
) -> None:
    """
    Update an existing skill's properties.

    Example:
        a4e update skill show_results --name "Display Results" --view new-results
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    # List available skills if none specified
    if not skill_id:
        skills_file = agent_dir / "skills" / "schemas.json"
        if skills_file.exists():
            try:
                schemas = json.loads(skills_file.read_text())
                available = list(schemas.keys())
                if available:
                    console.print("[bold]Available skills:[/bold]")
                    for s in available:
                        console.print(f"  • {s}")
                skill_id = Prompt.ask("[bold]Skill to update[/bold]")
            except json.JSONDecodeError:
                console.print("[red]Could not parse skills/schemas.json[/red]")
                raise typer.Exit(code=1)
        else:
            console.print("[red]No skills/schemas.json found[/red]")
            raise typer.Exit(code=1)

    # Parse list options
    triggers_list = [t.strip() for t in intent_triggers.split(",")] if intent_triggers else None
    tools_list = [t.strip() for t in internal_tools.split(",") if t.strip()] if internal_tools else None

    try:
        from ..tools.skills.update_skill import update_skill as mcp_update_skill

        result = mcp_update_skill(
            skill_id=skill_id,
            name=name,
            description=description,
            intent_triggers=triggers_list,
            output_view=output_view,
            internal_tools=tools_list,
            requires_auth=requires_auth,
            agent_name=str(agent_dir),
        )

        if result.get("success"):
            console.print(f"\n[green]✓ Skill '{skill_id}' updated![/green]")
            console.print(f"  Path: {result.get('path')}")
            if result.get("warnings"):
                for w in result["warnings"]:
                    console.print(f"  [yellow]Warning: {w}[/yellow]")
        else:
            console.print(f"\n[red]Error: {result.get('error')}[/red]")
            if result.get("fix"):
                console.print(f"  [yellow]Fix: {result.get('fix')}[/yellow]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)
