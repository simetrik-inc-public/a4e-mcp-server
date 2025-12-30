# a4e/cli_commands/add.py
"""
Commands for adding tools, views, and skills to an agent.
"""

import typer
import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()

# Create a 'Typer' app for the 'add' command group
app = typer.Typer(
    no_args_is_help=True,
    help="Add tools, views, or skills to your agent.",
)

TYPE_OPTIONS = ["string", "number", "integer", "boolean", "array", "object"]


def find_agent_dir(agent_name: Optional[str] = None) -> Optional[Path]:
    """Find the agent directory from name or current working directory."""
    cwd = Path.cwd()

    if agent_name:
        # Check if it's an absolute path
        if Path(agent_name).is_absolute() and Path(agent_name).exists():
            return Path(agent_name)
        # Check relative to cwd
        if (cwd / agent_name).exists():
            return cwd / agent_name
        # Check in agent-store
        agent_store = cwd / "file-store" / "agent-store" / agent_name
        if agent_store.exists():
            return agent_store
        return None

    # Check if cwd is an agent directory (has agent.py and metadata.json)
    if (cwd / "agent.py").exists() and (cwd / "metadata.json").exists():
        return cwd

    return None


def prompt_for_parameters() -> dict:
    """Interactive prompt for tool/view parameters."""
    parameters = {}

    console.print("\n[bold]Define parameters[/bold] (press Enter with empty name to finish)")

    while True:
        param_name = Prompt.ask("Parameter name", default="")
        if not param_name:
            break

        # Parameter type
        console.print("  Type options: " + ", ".join(f"[{i+1}]{t}" for i, t in enumerate(TYPE_OPTIONS)))
        type_choice = Prompt.ask("  Type", default="1")
        try:
            param_type = TYPE_OPTIONS[int(type_choice) - 1]
        except (ValueError, IndexError):
            param_type = type_choice if type_choice in TYPE_OPTIONS else "string"

        # Description
        param_desc = Prompt.ask("  Description", default=f"The {param_name} parameter")

        # Required?
        is_required = Confirm.ask("  Required?", default=False)

        parameters[param_name] = {
            "type": param_type,
            "description": param_desc,
            "required": is_required,
        }

        console.print(f"  [green]✓ Added parameter '{param_name}'[/green]")

    return parameters


@app.command("tool")
def add_tool(
    tool_name: Optional[str] = typer.Argument(None, help="Name of the tool (snake_case)"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="What the tool does"
    ),
    parameters_json: Optional[str] = typer.Option(
        None, "--parameters", "-p", help="Parameters as JSON string"
    ),
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
    non_interactive: bool = typer.Option(
        False, "--yes", "-y", help="Skip interactive prompts"
    ),
) -> None:
    """
    Add a new tool to the agent.

    Example:
        a4e add tool calculate_bmi -d "Calculate BMI"
        a4e add tool  # Interactive mode
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    # Interactive prompts
    if not non_interactive:
        if not tool_name:
            tool_name = Prompt.ask("[bold]Tool name[/bold] (snake_case)")

        if not description:
            description = Prompt.ask("[bold]Description[/bold]", default=f"A tool that {tool_name.replace('_', ' ')}")

        if not parameters_json:
            parameters = prompt_for_parameters()
        else:
            try:
                parameters = json.loads(parameters_json)
            except json.JSONDecodeError:
                console.print("[red]Invalid JSON for parameters[/red]")
                raise typer.Exit(code=1)
    else:
        if not all([tool_name, description]):
            console.print("[red]Error: --yes requires tool_name and --description[/red]")
            raise typer.Exit(code=1)
        parameters = json.loads(parameters_json) if parameters_json else {}

    # Validate tool name
    if not tool_name.replace("_", "").isalnum():
        console.print("[red]Error: Tool name must be alphanumeric with underscores[/red]")
        raise typer.Exit(code=1)

    try:
        from ..tools.agent_tools.add_tool import add_tool as mcp_add_tool

        result = mcp_add_tool(
            tool_name=tool_name,
            description=description,
            parameters=parameters,
            agent_name=str(agent_dir),
        )

        if result.get("success"):
            console.print(f"\n[green]✓ Tool '{tool_name}' created![/green]")
            console.print(f"  Path: {result.get('path')}")
            console.print("\n  [dim]Implement your tool logic in the generated file.[/dim]")
        else:
            console.print(f"\n[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("view")
def add_view(
    view_id: Optional[str] = typer.Argument(None, help="View ID (lowercase, hyphens)"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="View description"
    ),
    props_json: Optional[str] = typer.Option(
        None, "--props", "-p", help="Props as JSON string"
    ),
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
    non_interactive: bool = typer.Option(
        False, "--yes", "-y", help="Skip interactive prompts"
    ),
) -> None:
    """
    Add a new React view to the agent.

    Example:
        a4e add view results-display -d "Display search results"
        a4e add view  # Interactive mode
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    # Interactive prompts
    if not non_interactive:
        if not view_id:
            view_id = Prompt.ask("[bold]View ID[/bold] (lowercase, hyphens)")

        if not description:
            description = Prompt.ask("[bold]Description[/bold]", default=f"A view for {view_id.replace('-', ' ')}")

        if not props_json:
            console.print("\n[bold]Define props[/bold] (press Enter with empty name to finish)")
            props = {}

            while True:
                prop_name = Prompt.ask("Prop name", default="")
                if not prop_name:
                    break

                console.print("  Type options: " + ", ".join(f"[{i+1}]{t}" for i, t in enumerate(TYPE_OPTIONS)))
                type_choice = Prompt.ask("  Type", default="1")
                try:
                    prop_type = TYPE_OPTIONS[int(type_choice) - 1]
                except (ValueError, IndexError):
                    prop_type = type_choice if type_choice in TYPE_OPTIONS else "string"

                prop_desc = Prompt.ask("  Description", default=f"The {prop_name} prop")

                props[prop_name] = {
                    "type": prop_type,
                    "description": prop_desc,
                }
                console.print(f"  [green]✓ Added prop '{prop_name}'[/green]")
        else:
            try:
                props = json.loads(props_json)
            except json.JSONDecodeError:
                console.print("[red]Invalid JSON for props[/red]")
                raise typer.Exit(code=1)
    else:
        if not all([view_id, description]):
            console.print("[red]Error: --yes requires view_id and --description[/red]")
            raise typer.Exit(code=1)
        props = json.loads(props_json) if props_json else {}

    try:
        from ..tools.views.add_view import add_view as mcp_add_view

        result = mcp_add_view(
            view_id=view_id,
            description=description,
            props=props,
            agent_name=str(agent_dir),
        )

        if result.get("success"):
            console.print(f"\n[green]✓ View '{view_id}' created![/green]")
            console.print(f"  Path: {result.get('path')}")
            console.print("\n  [dim]Customize the React component in view.tsx[/dim]")
        else:
            console.print(f"\n[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("skill")
def add_skill(
    skill_id: Optional[str] = typer.Argument(None, help="Skill ID (lowercase, underscores)"),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Display name for the skill"
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Skill description"
    ),
    intent_triggers: Optional[str] = typer.Option(
        None, "--triggers", "-t", help="Comma-separated list of intent triggers"
    ),
    output_view: Optional[str] = typer.Option(
        None, "--view", "-v", help="Output view ID"
    ),
    internal_tools: Optional[str] = typer.Option(
        None, "--tools", help="Comma-separated list of internal tools"
    ),
    requires_auth: bool = typer.Option(
        False, "--auth", help="Requires authentication"
    ),
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
    non_interactive: bool = typer.Option(
        False, "--yes", "-y", help="Skip interactive prompts"
    ),
) -> None:
    """
    Add a new skill to the agent.

    Example:
        a4e add skill show_results --name "Show Results" --view results-display
        a4e add skill  # Interactive mode
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    # Interactive prompts
    if not non_interactive:
        if not skill_id:
            skill_id = Prompt.ask("[bold]Skill ID[/bold] (snake_case)")

        if not name:
            default_name = skill_id.replace("_", " ").title()
            name = Prompt.ask("[bold]Display name[/bold]", default=default_name)

        if not description:
            description = Prompt.ask("[bold]Description[/bold]", default=f"A skill for {name.lower()}")

        if not intent_triggers:
            console.print("\n[bold]Enter intent triggers[/bold] (comma-separated phrases)")
            triggers_input = Prompt.ask("Triggers", default=skill_id.replace("_", " "))
            intent_triggers_list = [t.strip() for t in triggers_input.split(",") if t.strip()]
        else:
            intent_triggers_list = [t.strip() for t in intent_triggers.split(",")]

        if not output_view:
            # List available views
            views_dir = agent_dir / "views"
            available_views = [d.name for d in views_dir.iterdir() if d.is_dir()] if views_dir.exists() else []

            if available_views:
                console.print("\n[bold]Available views:[/bold]")
                for i, v in enumerate(available_views, 1):
                    console.print(f"  [{i}] {v}")

            output_view = Prompt.ask("[bold]Output view[/bold]", default=available_views[0] if available_views else "welcome")

        if not internal_tools:
            # List available tools
            tools_dir = agent_dir / "tools"
            available_tools = [f.stem for f in tools_dir.glob("*.py") if f.stem != "__init__" and f.stem != "schemas"] if tools_dir.exists() else []

            if available_tools:
                console.print("\n[bold]Available tools:[/bold]")
                for t in available_tools:
                    console.print(f"  • {t}")

            tools_input = Prompt.ask("[bold]Internal tools[/bold] (comma-separated, or empty)", default="")
            internal_tools_list = [t.strip() for t in tools_input.split(",") if t.strip()]
        else:
            internal_tools_list = [t.strip() for t in internal_tools.split(",") if t.strip()]

        requires_auth = Confirm.ask("Requires authentication?", default=False)
    else:
        if not all([skill_id, name, description, output_view]):
            console.print("[red]Error: --yes requires skill_id, --name, --description, and --view[/red]")
            raise typer.Exit(code=1)
        intent_triggers_list = [t.strip() for t in (intent_triggers or "").split(",")] if intent_triggers else []
        internal_tools_list = [t.strip() for t in (internal_tools or "").split(",")] if internal_tools else []

    try:
        from ..tools.skills.add_skill import add_skill as mcp_add_skill

        result = mcp_add_skill(
            skill_id=skill_id,
            name=name,
            description=description,
            intent_triggers=intent_triggers_list,
            output_view=output_view,
            internal_tools=internal_tools_list,
            requires_auth=requires_auth,
            agent_name=str(agent_dir),
        )

        if result.get("success"):
            console.print(f"\n[green]✓ Skill '{skill_id}' created![/green]")
            console.print(f"  Path: {result.get('path')}")
            console.print("\n  [dim]Review the generated SKILL.md for documentation.[/dim]")
        else:
            console.print(f"\n[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing tools: {e}[/red]")
        raise typer.Exit(code=1)
