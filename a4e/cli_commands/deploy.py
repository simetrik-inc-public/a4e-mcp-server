# a4e/cli_commands/deploy.py
"""
Command for deploying an agent to production.
"""

import typer
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Create a 'Typer' app for the 'deploy' command
app = typer.Typer(
    no_args_is_help=False,
    help="Deploy your agent to production.",
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
def deploy(
    ctx: typer.Context,
    agent_name: Optional[str] = typer.Option(
        None, "--agent", "-a", help="Agent name/path (defaults to current directory)"
    ),
    skip_validation: bool = typer.Option(
        False, "--skip-validation", help="Skip pre-deployment validation"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
) -> None:
    """
    Deploy the agent to production.

    This command will:
    1. Validate the agent (unless --skip-validation)
    2. Upload the agent to the A4E Hub
    3. Return the deployment URL

    Example:
        a4e deploy
        a4e deploy --agent my-agent --yes
    """
    agent_dir = find_agent_dir(agent_name)
    if not agent_dir:
        console.print("[red]Error: Not in an agent directory. Use --agent to specify the agent.[/red]")
        raise typer.Exit(code=1)

    console.print(Panel.fit(
        f"[bold]Deploying agent:[/bold] {agent_dir.name}",
        border_style="blue"
    ))

    # Run validation first (unless skipped)
    if not skip_validation:
        console.print("\n[bold]Step 1: Validation[/bold]")
        try:
            from ..tools.validation.validate import validate as mcp_validate

            result = mcp_validate(agent_name=str(agent_dir))

            errors = result.get("errors", [])
            warnings = result.get("warnings", [])

            if errors:
                console.print(f"[red]  ✗ Validation failed with {len(errors)} error(s)[/red]")
                for error in errors:
                    console.print(f"    [red]•[/red] {error}")
                console.print("\n[yellow]Fix errors before deploying, or use --skip-validation to bypass.[/yellow]")
                raise typer.Exit(code=1)
            elif warnings:
                console.print(f"[green]  ✓ Validation passed with {len(warnings)} warning(s)[/green]")
            else:
                console.print("[green]  ✓ Validation passed[/green]")

        except ImportError as e:
            console.print(f"[red]Error importing validation: {e}[/red]")
            raise typer.Exit(code=1)

    # Confirm deployment
    if not yes:
        console.print("")
        if not Confirm.ask("Proceed with deployment?", default=True):
            console.print("[yellow]Deployment cancelled.[/yellow]")
            raise typer.Exit(code=0)

    # Deploy
    console.print("\n[bold]Step 2: Deployment[/bold]")

    try:
        from ..tools.deploy.deploy import deploy as mcp_deploy

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Deploying to A4E Hub...", total=None)

            result = mcp_deploy(agent_name=str(agent_dir))

            progress.update(task, completed=True)

        if result.get("success"):
            console.print("[green]  ✓ Agent ready for deployment![/green]")

            # Show next steps
            next_steps = result.get("next_steps", [])
            if next_steps:
                console.print("\n[bold]Next Steps:[/bold]")
                for i, step in enumerate(next_steps, 1):
                    console.print(f"  {i}. {step}")

            console.print("\n[dim]Run 'a4e dev start' to test locally with the playground.[/dim]")
        else:
            console.print(f"[red]  ✗ Deployment failed: {result.get('error')}[/red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]Error importing deploy: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error during deployment: {e}[/red]")
        raise typer.Exit(code=1)
