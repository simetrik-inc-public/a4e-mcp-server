# a4e/cli_commands/auth.py
"""
Authentication commands for A4E Hub.

Provides OAuth 2.0 authentication using Authorization Code Flow with PKCE.
"""

import typer
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Create a 'Typer' app for the 'auth' command group
app = typer.Typer(
    no_args_is_help=True,
    help="Authenticate with A4E Hub.",
)


def _get_oauth_client(client_id: Optional[str] = None):
    """Get configured OAuth client."""
    import os
    from ..utils.oauth import A4EOAuthClient, KEYRING_AVAILABLE

    resolved_client_id = client_id or os.getenv("A4E_OAUTH_CLIENT_ID")

    if not resolved_client_id:
        console.print("[red]Error: No client ID provided.[/red]")
        console.print("\nSet A4E_OAUTH_CLIENT_ID environment variable or use --client-id option.")
        console.print("\nTo get a client ID:")
        console.print("  1. Go to A4E Hub Settings > OAuth Applications")
        console.print("  2. Create a new application")
        console.print("  3. Copy the client_id")
        raise typer.Exit(code=1)

    if not KEYRING_AVAILABLE:
        console.print("[yellow]Warning: keyring not available. Tokens will not be persisted.[/yellow]")
        console.print("Install keyring for secure token storage: pip install keyring\n")

    return A4EOAuthClient(client_id=resolved_client_id)


@app.command("login")
def login(
    client_id: Optional[str] = typer.Option(
        None, "--client-id", "-c", help="OAuth client ID (or set A4E_OAUTH_CLIENT_ID)"
    ),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Don't open browser automatically"
    ),
    timeout: int = typer.Option(
        300, "--timeout", "-t", help="Authentication timeout in seconds"
    ),
) -> None:
    """
    Log in to A4E Hub.

    Opens a browser window for authentication using OAuth 2.0 with PKCE.
    Tokens are securely stored in the system keyring.

    Example:
        a4e auth login
        a4e auth login --client-id my-app-id
    """
    from ..utils.oauth import OAuthError, AuthenticationTimeoutError

    client = _get_oauth_client(client_id)

    # Check if already logged in
    if client.is_authenticated():
        user_info = client.get_user_info()
        username = user_info.get("username", "Unknown") if user_info else "Unknown"
        console.print(f"[yellow]Already logged in as {username}[/yellow]")
        console.print("Use 'a4e auth logout' to log out first, or 'a4e auth status' to see details.")
        return

    console.print("[bold]Logging in to A4E Hub...[/bold]\n")

    def on_url_ready(url: str):
        console.print("Opening browser for authentication...")
        console.print(f"\n[dim]If the browser doesn't open, visit:[/dim]")
        console.print(f"[link={url}]{url}[/link]\n")

    try:
        tokens = client.authenticate(
            timeout=timeout,
            open_browser=not no_browser,
            on_url_ready=on_url_ready,
        )

        # Get user info after successful login
        user_info = client.get_user_info()

        console.print(Panel.fit(
            "[bold green]Login successful![/bold green]\n\n"
            f"[bold]User:[/bold] {user_info.get('username', 'Unknown') if user_info else 'Unknown'}\n"
            f"[bold]Scopes:[/bold] {user_info.get('scope', 'N/A') if user_info else 'N/A'}",
            title="Authenticated",
            border_style="green"
        ))

    except AuthenticationTimeoutError:
        console.print("[red]Error: Authentication timed out.[/red]")
        console.print("Please try again with a longer timeout using --timeout.")
        raise typer.Exit(code=1)

    except OAuthError as e:
        console.print(f"[red]Authentication failed: {e.error}[/red]")
        if e.description:
            console.print(f"[dim]{e.description}[/dim]")
        raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("logout")
def logout(
    client_id: Optional[str] = typer.Option(
        None, "--client-id", "-c", help="OAuth client ID (or set A4E_OAUTH_CLIENT_ID)"
    ),
    revoke: bool = typer.Option(
        True, "--revoke/--no-revoke", help="Revoke tokens on the server"
    ),
) -> None:
    """
    Log out from A4E Hub.

    Removes stored tokens and optionally revokes them on the server.

    Example:
        a4e auth logout
        a4e auth logout --no-revoke
    """
    client = _get_oauth_client(client_id)

    tokens = client.get_stored_tokens()
    if not tokens:
        console.print("[yellow]Not currently logged in.[/yellow]")
        return

    if revoke:
        console.print("Revoking tokens...")
        success = client.revoke_token()
        if success:
            console.print("[green]Tokens revoked successfully.[/green]")
        else:
            console.print("[yellow]Could not revoke tokens on server (they have been removed locally).[/yellow]")
    else:
        client.clear_stored_tokens()

    console.print("[green]Logged out successfully.[/green]")


@app.command("status")
def status(
    client_id: Optional[str] = typer.Option(
        None, "--client-id", "-c", help="OAuth client ID (or set A4E_OAUTH_CLIENT_ID)"
    ),
) -> None:
    """
    Show current authentication status.

    Displays whether you're logged in, token validity, and user information.

    Example:
        a4e auth status
    """
    client = _get_oauth_client(client_id)

    tokens = client.get_stored_tokens()

    if not tokens:
        console.print(Panel.fit(
            "[bold yellow]Not logged in[/bold yellow]\n\n"
            "Use 'a4e auth login' to authenticate with A4E Hub.",
            title="Authentication Status",
            border_style="yellow"
        ))
        return

    # Check token validity
    introspection = client.introspect_token()
    is_active = introspection.get("active", False)

    if is_active:
        user_info = client.get_user_info()

        table = Table(title="Authentication Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row("Status", "[green]Logged in[/green]")
        table.add_row("User", user_info.get("username", "Unknown") if user_info else "Unknown")
        table.add_row("Email", user_info.get("email", "N/A") if user_info else "N/A")
        table.add_row("Scopes", user_info.get("scope", "N/A") if user_info else "N/A")
        table.add_row("Token Active", "[green]Yes[/green]")

        if tokens.get("stored_at"):
            table.add_row("Authenticated At", tokens.get("stored_at", "N/A"))

        console.print(table)
    else:
        console.print(Panel.fit(
            "[bold yellow]Session expired[/bold yellow]\n\n"
            "Your authentication has expired.\n"
            "Use 'a4e auth refresh' to refresh your tokens,\n"
            "or 'a4e auth login' to log in again.",
            title="Authentication Status",
            border_style="yellow"
        ))


@app.command("refresh")
def refresh(
    client_id: Optional[str] = typer.Option(
        None, "--client-id", "-c", help="OAuth client ID (or set A4E_OAUTH_CLIENT_ID)"
    ),
) -> None:
    """
    Refresh authentication tokens.

    Uses the refresh token to obtain new access tokens.

    Example:
        a4e auth refresh
    """
    from ..utils.oauth import TokenRefreshError

    client = _get_oauth_client(client_id)

    tokens = client.get_stored_tokens()
    if not tokens:
        console.print("[yellow]Not logged in. Use 'a4e auth login' first.[/yellow]")
        raise typer.Exit(code=1)

    if not tokens.get("refresh_token"):
        console.print("[red]No refresh token available. Please log in again.[/red]")
        raise typer.Exit(code=1)

    console.print("Refreshing tokens...")

    try:
        client.refresh_tokens()
        console.print("[green]Tokens refreshed successfully.[/green]")

        # Show updated status
        user_info = client.get_user_info()
        if user_info:
            console.print(f"\n[bold]User:[/bold] {user_info.get('username', 'Unknown')}")
            console.print(f"[bold]Scopes:[/bold] {user_info.get('scope', 'N/A')}")

    except TokenRefreshError as e:
        console.print(f"[red]Failed to refresh tokens: {e.error}[/red]")
        if e.description:
            console.print(f"[dim]{e.description}[/dim]")
        console.print("\nPlease log in again with 'a4e auth login'.")
        raise typer.Exit(code=1)


@app.command("token")
def token(
    client_id: Optional[str] = typer.Option(
        None, "--client-id", "-c", help="OAuth client ID (or set A4E_OAUTH_CLIENT_ID)"
    ),
    refresh_if_expired: bool = typer.Option(
        True, "--refresh/--no-refresh", help="Refresh token if expired"
    ),
) -> None:
    """
    Print the current access token.

    Useful for debugging or using with other tools.

    Example:
        a4e auth token
        curl -H "Authorization: Bearer $(a4e auth token)" https://api.example.com
    """
    client = _get_oauth_client(client_id)

    access_token = client.get_access_token(auto_refresh=refresh_if_expired)

    if access_token:
        # Print just the token for easy piping
        typer.echo(access_token)
    else:
        console.print("[red]No valid access token available.[/red]", err=True)
        console.print("Use 'a4e auth login' to authenticate.", err=True)
        raise typer.Exit(code=1)
