# a4e/cli_commands/dev.py

import typer
from pathlib import Path
from typing import Optional
import pyperclip  # NEW IMPORT

from ..utils.dev_manager import DevManager  # Correct relative import


# Create a 'Typer' app specifically for the 'dev' command group
app = typer.Typer(
    no_args_is_help=True,
    help="Commands for running the development server and ngrok tunnels.",
)


@app.command()
def start(
    port: int = typer.Option(5000, help="The local port to run the server on."),
    auth_token: Optional[str] = typer.Option(
        None,
        help="Your ngrok authtoken. Get it from https://dashboard.ngrok.com/get-started/your-authtoken",
    ),
    agent_path: Optional[Path] = typer.Option(
        None,
        "--agent-path",
        help="The path to the agent folder. If not provided, you will be prompted to choose.",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """
    Starts the development server with an ngrok tunnel.
    """
    project_dir = agent_path

    if not project_dir:
        # If no path is provided, scan for agents in the default location
        try:
            # Determine project root relative to this file's location
            # a4e/cli_commands/dev.py -> a4e/ -> project root
            repo_root = Path(__file__).parent.parent.parent
            agent_store_path = repo_root / "file-store" / "agent-store"

            available_agents = []
            if agent_store_path.is_dir():
                available_agents = [d for d in agent_store_path.iterdir() if d.is_dir()]

            while not project_dir:
                print("\nSelect an agent:")
                if available_agents:
                    for i, agent in enumerate(available_agents):
                        print(f"  [{i + 1}] {agent.name}")
                    prompt_text = (
                        "\nPlease choose an agent by number, or enter a custom path:"
                    )
                else:
                    prompt_text = "\nNo agents found in default store. Please enter the path to your agent's folder:"

                response = typer.prompt(prompt_text)

                try:
                    # Check if user entered a number
                    choice_index = int(response) - 1
                    if 0 <= choice_index < len(available_agents):
                        project_dir = available_agents[choice_index]
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    # User entered a path string
                    project_dir = Path(response).resolve()

                if project_dir and (
                    not project_dir.exists() or not project_dir.is_dir()
                ):
                    print(f"Error: Path '{project_dir}' is not a valid directory.")
                    project_dir = None  # Reset to re-trigger the loop

        except Exception as e:
            print(f"An error occurred while searching for agents: {e}")
            raise typer.Exit(code=1)

    # Final validation of the selected directory
    if not project_dir or not project_dir.is_dir():
        print("Error: No valid agent directory selected.")
        raise typer.Exit(code=1)

    print(f"\nUsing agent folder: {project_dir}")
    print("Starting development server...")

    result = DevManager.start_dev_server(
        project_dir=project_dir, port=port, auth_token=auth_token
    )

    if result.get("success"):
        print("Dev mode started successfully:")
        print(f"  Public URL: {result.get('public_url')}")
        hub_url = result.get("hub_url")
        print(f"  Hub URL: {hub_url}")

        try:
            pyperclip.copy(str(hub_url))
            print("  (Hub URL copied to clipboard!)")
        except pyperclip.PyperclipException:
            print(
                "  (Could not copy Hub URL to clipboard. Please install xclip/xsel or enable Wayland clipboard for Linux.)"
            )

        print("\nInstructions:")
        for instruction in result.get("instructions", []):
            print(f"  {instruction}")
    else:
        print(f"Error starting server: {result.get('error')}")
        if result.get("details"):
            print(f"Details: {result.get('details')}")
        if result.get("fix"):
            print(f"Fix: {result.get('fix')}")
        raise typer.Exit(code=1)
