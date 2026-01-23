#!/usr/bin/env python3
"""
Example CLI Application with A4E Hub OAuth Integration

This demonstrates how to build a CLI application that authenticates
with A4E Hub using OAuth 2.0 with PKCE.

Prerequisites:
    pip install httpx keyring click rich

Usage:
    python example_cli_app.py login
    python example_cli_app.py status
    python example_cli_app.py api /api/users/me
    python example_cli_app.py logout

Environment Variables:
    A4E_OAUTH_CLIENT_ID - Your OAuth client ID (required)
    A4E_HUB_API_URL - A4E Hub API URL (default: http://localhost:8000)
    A4E_HUB_FRONTEND_URL - A4E Hub Frontend URL (default: http://localhost:3000)
"""

from __future__ import annotations

import json
import os
import sys

# Optional: Use click for better CLI experience
try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False

# Optional: Use rich for better output formatting
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

import httpx

from cli_oauth_client import (
    CLIOAuthClient,
    OAuthError,
    TokenRefreshError,
    OAuthConfig,
)


# Application configuration
APP_NAME = "A4E CLI"
APP_VERSION = "1.0.0"
STORAGE_KEY = "a4e-cli-example"

# Default configuration (can be overridden via environment)
DEFAULT_CLIENT_ID = os.getenv("A4E_OAUTH_CLIENT_ID", "")
DEFAULT_API_URL = os.getenv("A4E_HUB_API_URL", "http://localhost:8000")
DEFAULT_FRONTEND_URL = os.getenv("A4E_HUB_FRONTEND_URL", "http://localhost:3000")


def get_oauth_client() -> CLIOAuthClient:
    """Create and return the OAuth client."""
    if not DEFAULT_CLIENT_ID:
        print_error(
            "OAuth client ID not configured.\n"
            "Set A4E_OAUTH_CLIENT_ID environment variable or update DEFAULT_CLIENT_ID."
        )
        sys.exit(1)

    return CLIOAuthClient(
        client_id=DEFAULT_CLIENT_ID,
        hub_api_url=DEFAULT_API_URL,
        hub_frontend_url=DEFAULT_FRONTEND_URL,
        scopes=["read", "profile"],
        token_storage_key=STORAGE_KEY,
    )


def print_success(message: str):
    """Print a success message."""
    if RICH_AVAILABLE:
        console.print(f"[green][OK][/green] {message}")
    else:
        print(f"[OK] {message}")


def print_error(message: str):
    """Print an error message."""
    if RICH_AVAILABLE:
        console.print(f"[red][ERROR][/red] {message}")
    else:
        print(f"[ERROR] {message}", file=sys.stderr)


def print_info(message: str):
    """Print an info message."""
    if RICH_AVAILABLE:
        console.print(f"[blue][INFO][/blue] {message}")
    else:
        print(f"[INFO] {message}")


def print_json(data: dict):
    """Pretty print JSON data."""
    if RICH_AVAILABLE:
        console.print_json(json.dumps(data))
    else:
        print(json.dumps(data, indent=2))


# ============================================================================
# CLI Commands (with click if available, fallback to argparse)
# ============================================================================

if CLICK_AVAILABLE:
    @click.group()
    @click.version_option(version=APP_VERSION, prog_name=APP_NAME)
    def cli():
        """A4E CLI - Command line interface for A4E Hub."""
        pass

    @cli.command()
    def login():
        """Authenticate with A4E Hub."""
        client = get_oauth_client()

        # Check if already logged in
        tokens = client.get_stored_tokens()
        if tokens:
            introspection = client.introspect_token()
            if introspection.get("active"):
                print_info(f"Already logged in as {introspection.get('username', 'unknown')}")
                if click.confirm("Login again?", default=False):
                    client.clear_stored_tokens()
                else:
                    return

        print_info("Starting authentication flow...")
        print_info("A browser window will open for you to log in.")

        try:
            tokens = client.authenticate(timeout=300)
            print_success("Authentication successful!")

            # Show token info
            introspection = client.introspect_token()
            if RICH_AVAILABLE:
                table = Table(title="Authentication Details")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")
                table.add_row("Username", introspection.get("username", "N/A"))
                table.add_row("Scopes", introspection.get("scope", "N/A"))
                table.add_row("Token Type", tokens.get("token_type", "Bearer"))
                table.add_row("Expires In", f"{tokens.get('expires_in', 'N/A')} seconds")
                console.print(table)
            else:
                print(f"\nUsername: {introspection.get('username', 'N/A')}")
                print(f"Scopes: {introspection.get('scope', 'N/A')}")
                print(f"Expires In: {tokens.get('expires_in', 'N/A')} seconds")

        except OAuthError as e:
            print_error(f"Authentication failed: {e}")
            sys.exit(1)

    @cli.command()
    def logout():
        """Log out and revoke tokens."""
        client = get_oauth_client()

        tokens = client.get_stored_tokens()
        if not tokens:
            print_info("Not logged in.")
            return

        print_info("Revoking tokens...")
        client.revoke_token()
        client.clear_stored_tokens()
        print_success("Logged out successfully.")

    @cli.command()
    def status():
        """Show current authentication status."""
        client = get_oauth_client()

        tokens = client.get_stored_tokens()
        if not tokens:
            print_info("Not logged in. Use 'login' command to authenticate.")
            return

        introspection = client.introspect_token()

        if RICH_AVAILABLE:
            if introspection.get("active"):
                panel = Panel(
                    f"[green]Logged in as:[/green] {introspection.get('username', 'unknown')}\n"
                    f"[blue]Scopes:[/blue] {introspection.get('scope', 'N/A')}\n"
                    f"[blue]Client ID:[/blue] {introspection.get('client_id', 'N/A')}",
                    title="Authentication Status",
                    border_style="green",
                )
                console.print(panel)
            else:
                panel = Panel(
                    "[yellow]Token expired or invalid.[/yellow]\n"
                    "Use 'login' command to re-authenticate.",
                    title="Authentication Status",
                    border_style="yellow",
                )
                console.print(panel)
        else:
            if introspection.get("active"):
                print(f"Logged in as: {introspection.get('username', 'unknown')}")
                print(f"Scopes: {introspection.get('scope', 'N/A')}")
            else:
                print("Token expired or invalid. Use 'login' to re-authenticate.")

    @cli.command()
    def refresh():
        """Refresh the access token."""
        client = get_oauth_client()

        tokens = client.get_stored_tokens()
        if not tokens:
            print_error("Not logged in. Use 'login' command first.")
            sys.exit(1)

        try:
            new_tokens = client.refresh_tokens()
            print_success("Token refreshed successfully!")
            print_info(f"New token expires in {new_tokens.get('expires_in', 'N/A')} seconds")
        except TokenRefreshError as e:
            print_error(f"Failed to refresh token: {e}")
            print_info("Try logging in again with 'login' command.")
            sys.exit(1)

    @cli.command()
    @click.argument("endpoint")
    @click.option("--method", "-m", default="GET", help="HTTP method (GET, POST, etc.)")
    @click.option("--data", "-d", default=None, help="JSON data for POST/PUT requests")
    def api(endpoint: str, method: str, data: str):
        """
        Make an API call to A4E Hub.

        ENDPOINT is the API path (e.g., /api/users/me)
        """
        client = get_oauth_client()

        access_token = client.get_access_token(auto_refresh=True)
        if not access_token:
            print_error("Not logged in or token expired. Use 'login' command.")
            sys.exit(1)

        # Build full URL
        url = f"{DEFAULT_API_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {access_token}"}

        # Parse JSON data if provided
        json_data = None
        if data:
            try:
                json_data = json.loads(data)
            except json.JSONDecodeError:
                print_error("Invalid JSON data provided.")
                sys.exit(1)

        print_info(f"{method} {url}")

        try:
            with httpx.Client() as http_client:
                response = http_client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=json_data,
                )

            print_info(f"Status: {response.status_code}")

            try:
                result = response.json()
                print_json(result)
            except json.JSONDecodeError:
                print(response.text)

        except httpx.RequestError as e:
            print_error(f"Request failed: {e}")
            sys.exit(1)

    @cli.command()
    def token():
        """Display the current access token (for debugging)."""
        client = get_oauth_client()

        tokens = client.get_stored_tokens()
        if not tokens:
            print_error("Not logged in. Use 'login' command first.")
            sys.exit(1)

        access_token = tokens.get("access_token", "N/A")

        if RICH_AVAILABLE:
            console.print(Panel(
                f"[dim]{access_token}[/dim]",
                title="Access Token",
                border_style="blue",
            ))
        else:
            print(f"Access Token:\n{access_token}")

        print_info("Use this token in the Authorization header: Bearer <token>")

else:
    # Fallback to argparse if click is not available
    import argparse

    def main_argparse():
        parser = argparse.ArgumentParser(
            description="A4E CLI - Command line interface for A4E Hub"
        )
        parser.add_argument("--version", action="version", version=f"{APP_NAME} {APP_VERSION}")

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Login command
        subparsers.add_parser("login", help="Authenticate with A4E Hub")

        # Logout command
        subparsers.add_parser("logout", help="Log out and revoke tokens")

        # Status command
        subparsers.add_parser("status", help="Show current authentication status")

        # Refresh command
        subparsers.add_parser("refresh", help="Refresh the access token")

        # API command
        api_parser = subparsers.add_parser("api", help="Make an API call")
        api_parser.add_argument("endpoint", help="API endpoint path")
        api_parser.add_argument("-m", "--method", default="GET", help="HTTP method")
        api_parser.add_argument("-d", "--data", help="JSON data for POST/PUT")

        # Token command
        subparsers.add_parser("token", help="Display the current access token")

        args = parser.parse_args()

        if args.command == "login":
            login_argparse()
        elif args.command == "logout":
            logout_argparse()
        elif args.command == "status":
            status_argparse()
        elif args.command == "refresh":
            refresh_argparse()
        elif args.command == "api":
            api_argparse(args.endpoint, args.method, args.data)
        elif args.command == "token":
            token_argparse()
        else:
            parser.print_help()

    def login_argparse():
        client = get_oauth_client()
        tokens = client.get_stored_tokens()
        if tokens:
            introspection = client.introspect_token()
            if introspection.get("active"):
                print_info(f"Already logged in as {introspection.get('username', 'unknown')}")
                response = input("Login again? [y/N]: ")
                if response.lower() != 'y':
                    return
                client.clear_stored_tokens()

        print_info("Starting authentication flow...")
        try:
            tokens = client.authenticate(timeout=300)
            print_success("Authentication successful!")
            introspection = client.introspect_token()
            print(f"Username: {introspection.get('username', 'N/A')}")
            print(f"Scopes: {introspection.get('scope', 'N/A')}")
        except OAuthError as e:
            print_error(f"Authentication failed: {e}")
            sys.exit(1)

    def logout_argparse():
        client = get_oauth_client()
        if not client.get_stored_tokens():
            print_info("Not logged in.")
            return
        client.revoke_token()
        client.clear_stored_tokens()
        print_success("Logged out successfully.")

    def status_argparse():
        client = get_oauth_client()
        tokens = client.get_stored_tokens()
        if not tokens:
            print_info("Not logged in.")
            return
        introspection = client.introspect_token()
        if introspection.get("active"):
            print(f"Logged in as: {introspection.get('username', 'unknown')}")
            print(f"Scopes: {introspection.get('scope', 'N/A')}")
        else:
            print("Token expired or invalid.")

    def refresh_argparse():
        client = get_oauth_client()
        if not client.get_stored_tokens():
            print_error("Not logged in.")
            sys.exit(1)
        try:
            new_tokens = client.refresh_tokens()
            print_success("Token refreshed!")
            print_info(f"Expires in {new_tokens.get('expires_in', 'N/A')} seconds")
        except TokenRefreshError as e:
            print_error(f"Failed to refresh: {e}")
            sys.exit(1)

    def api_argparse(endpoint, method, data):
        client = get_oauth_client()
        access_token = client.get_access_token(auto_refresh=True)
        if not access_token:
            print_error("Not logged in or token expired.")
            sys.exit(1)

        url = f"{DEFAULT_API_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {access_token}"}
        json_data = json.loads(data) if data else None

        print_info(f"{method} {url}")
        with httpx.Client() as http_client:
            response = http_client.request(method=method.upper(), url=url, headers=headers, json=json_data)
        print_info(f"Status: {response.status_code}")
        try:
            print_json(response.json())
        except:
            print(response.text)

    def token_argparse():
        client = get_oauth_client()
        tokens = client.get_stored_tokens()
        if not tokens:
            print_error("Not logged in.")
            sys.exit(1)
        print(f"Access Token:\n{tokens.get('access_token', 'N/A')}")


if __name__ == "__main__":
    if CLICK_AVAILABLE:
        cli()
    else:
        main_argparse()
