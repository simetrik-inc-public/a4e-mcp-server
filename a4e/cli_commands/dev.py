# a4e/cli_commands/dev.py

import typer
from pathlib import Path
from typing import Optional
import pyperclip
import os


from ..utils.dev_manager import DevManager  # Correct relative import


# Create a 'Typer' app specifically for the 'dev' command group
app = typer.Typer(
    no_args_is_help=True,
    help="Commands for running the development server and ngrok tunnels.",
)


def get_ngrok_authtoken():
    """
    Attempts to retrieve the ngrok authtoken from the system.
    """
    # Try to get the ngrok token from an environment variable
    token = os.environ.get("NGROK_AUTHTOKEN")
    if token:
        return token

    # If not an environment variable try to look for it in the system
    try:
        home = Path.home()
        config_paths = [
            home / ".ngrok2" / "ngrok.yml",
            home / ".config" / "ngrok" / "ngrok.yml",
            home / "Library" / "Application Support" / "ngrok" / "ngrok.yml",
        ]
        for config_path in config_paths:
            if config_path.exists():
                with open(config_path, "r") as f:
                    for line in f:
                        if line.strip().startswith("authtoken:"):
                            return line.strip().split(":", 1)[1].strip().strip("'\"")
    except Exception:
        pass

    return None


@app.command()
def start(
    port: int = typer.Option(5000, help="The local port to run the server on."),
    auth_token: Optional[str] = typer.Option(
        None,
        help="Your ngrok authtoken. If not provided, it will be sourced from your environment or ngrok config.",
    ),
) -> None:
    """
    Starts the development server with an ngrok tunnel.
    This command must be run from within the 'agent-store' directory.
    """
    if not auth_token:
        auth_token = get_ngrok_authtoken()

    if not auth_token:
        print("Error: Could not find ngrok authtoken.")
        print(
            "Please provide it with the --auth-token option, or run 'ngrok config add-authtoken <YOUR_TOKEN>'"
        )
        raise typer.Exit(code=1)

    current_dir = Path.cwd()
    project_dir = None

    # Check if the current directory is 'agent-store'
    if current_dir.name != "agent-store":
        print("Error: This command must be run from the 'agent-store' directory.")
        print(f"Current directory: {current_dir}")
        raise typer.Exit(code=1)

    # If we are in agent-store, list available agents and prompt for selection
    agent_store_path = current_dir
    available_agents = []
    if agent_store_path.is_dir():
        available_agents = [d for d in agent_store_path.iterdir() if d.is_dir()]

    while not project_dir:
        print("\nSelect an agent to start:")
        if available_agents:
            for i, agent in enumerate(available_agents):
                print(f"  [{i + 1}] {agent.name}")
            prompt_text = "\nPlease choose an agent"
        else:
            print("No agents found in the current 'agent-store' directory.")
            raise typer.Exit(code=1)

        try:
            # Check if user entered a number
            response = typer.prompt(prompt_text, type=str)
            choice_index = int(response) - 1
            if 0 <= choice_index < len(available_agents):
                project_dir = available_agents[choice_index]
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            # User entered a path string
            print("Please enter a valid number.")

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

        try:
            pyperclip.copy(str(result.get("public_url")))
            print("  (Public URL copied to clipboard!)")
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
