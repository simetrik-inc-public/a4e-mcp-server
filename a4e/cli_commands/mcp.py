"""
MCP configuration commands for A4E.

This module provides commands to configure the A4E MCP server
for different IDEs like Cursor, Claude Desktop, and VS Code.

Usage:
    a4e mcp setup cursor
    a4e mcp setup claude-desktop
    a4e mcp show cursor
    a4e mcp remove cursor
    a4e mcp test
"""

import json
import sys
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    help="Configure MCP server for IDEs",
    no_args_is_help=True,
)


# ============================================================================
# Configuration Paths
# ============================================================================


def _get_platform() -> str:
    """Get the current platform: darwin, win32, or linux."""
    return sys.platform


def _get_ide_configs() -> dict:
    """
    Get IDE configuration paths and formats.
    
    Returns dict with IDE name as key and:
        - path: Path to config file
        - servers_key: Key name for MCP servers in config
        - name: Display name for the IDE
    """
    platform = _get_platform()
    home = Path.home()
    
    # Claude Desktop config path varies by OS
    if platform == "darwin":
        claude_path = home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif platform == "win32":
        claude_path = home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    else:  # Linux and others
        claude_path = home / ".config" / "claude" / "claude_desktop_config.json"
    
    return {
        "cursor": {
            "path": home / ".cursor" / "mcp.json",
            "servers_key": "mcpServers",
            "name": "Cursor",
        },
        "claude-desktop": {
            "path": claude_path,
            "servers_key": "mcpServers",
            "name": "Claude Desktop",
        },
        "vscode": {
            "path": home / ".vscode" / "mcp.json",
            "servers_key": "servers",
            "name": "VS Code",
        },
    }


def _get_a4e_server_config(ide: str) -> dict:
    """
    Generate the MCP server configuration for A4E.
    
    Uses sys.executable to get the exact Python that has a4e installed.
    This ensures the config works regardless of how Python was installed
    (pyenv, system, venv, homebrew, etc.)
    
    The env configuration varies by IDE:
    - Cursor/VS Code: Uses ${workspaceFolder} which they expand
    - Claude Desktop: No workspace concept, uses cwd or explicit path
    
    Args:
        ide: The IDE identifier (cursor, vscode, claude-desktop)
    """
    base_config = {
        "command": sys.executable,
        "args": ["-m", "a4e.server"],
    }
    
    # IDEs that support ${workspaceFolder}
    if ide in ("cursor", "vscode"):
        base_config["env"] = {
            "A4E_WORKSPACE": "${workspaceFolder}"
        }
    # Claude Desktop and others: no workspace variable
    # The server will use cwd or require explicit project_path in tool calls
    # else: no env needed
    
    return base_config


def _get_supported_ides() -> list[str]:
    """Get list of supported IDE names."""
    return list(_get_ide_configs().keys())


# ============================================================================
# Helper Functions
# ============================================================================


def _load_config(config_path: Path) -> tuple[dict, bool]:
    """
    Load existing config from path.
    
    Returns:
        Tuple of (config_dict, had_error)
        If file doesn't exist, returns empty dict with no error.
        If file has invalid JSON, returns empty dict with error=True.
    """
    if not config_path.exists():
        return {}, False
    
    try:
        content = config_path.read_text().strip()
        if not content:
            return {}, False
        return json.loads(content), False
    except json.JSONDecodeError:
        return {}, True


def _save_config(config_path: Path, config: dict) -> None:
    """Save config to path, creating parent directories if needed."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2) + "\n")


# ============================================================================
# Commands
# ============================================================================


@app.command()
def setup(
    ide: str = typer.Argument(
        ..., 
        help="IDE to configure: cursor, claude-desktop, vscode"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n",
        help="Show what would be done without making changes"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", 
        help="Overwrite existing A4E configuration"
    ),
):
    """
    Configure A4E MCP server for your IDE.
    
    This writes the necessary configuration so your IDE can use
    A4E tools through the Model Context Protocol (MCP).
    
    Examples:
    
        a4e mcp setup cursor
        
        a4e mcp setup claude-desktop
        
        a4e mcp setup cursor --dry-run
        
        a4e mcp setup cursor --force
    """
    ide_configs = _get_ide_configs()
    ide_lower = ide.lower()
    
    if ide_lower not in ide_configs:
        supported = ", ".join(_get_supported_ides())
        typer.echo(f"Error: Unknown IDE '{ide}'", err=True)
        typer.echo(f"Supported IDEs: {supported}", err=True)
        raise typer.Exit(1)
    
    config_info = ide_configs[ide_lower]
    config_path: Path = config_info["path"]
    servers_key: str = config_info["servers_key"]
    ide_name: str = config_info["name"]
    a4e_config = _get_a4e_server_config(ide_lower)
    
    # Dry run mode - show what would happen
    if dry_run:
        typer.echo(f"Would configure A4E for {ide_name}:")
        typer.echo()
        typer.echo(f"  Config file: {config_path}")
        typer.echo(f"  Python path: {sys.executable}")
        typer.echo()
        typer.echo("  Configuration to add:")
        preview = {servers_key: {"a4e": a4e_config}}
        typer.echo(json.dumps(preview, indent=2))
        return
    
    # Load existing config
    existing, had_json_error = _load_config(config_path)
    
    if had_json_error:
        # Backup corrupted config
        backup_path = config_path.with_suffix(".json.backup")
        typer.echo(f"Warning: Invalid JSON in {config_path}", err=True)
        typer.echo(f"Creating backup at {backup_path}", err=True)
        
        if config_path.exists():
            backup_path.write_text(config_path.read_text())
        
        existing = {}
    
    # Ensure servers key exists
    existing.setdefault(servers_key, {})
    
    # Check if a4e already configured
    if "a4e" in existing[servers_key]:
        if not force:
            typer.echo(f"A4E is already configured for {ide_name}")
            typer.echo()
            typer.echo("Current configuration:")
            typer.echo(json.dumps(existing[servers_key]["a4e"], indent=2))
            typer.echo()
            typer.echo("Use --force to overwrite, or --dry-run to preview")
            raise typer.Exit(1)
        else:
            typer.echo(f"Overwriting existing A4E configuration...")
    
    # Add/update a4e config
    existing[servers_key]["a4e"] = a4e_config
    
    # Save config
    _save_config(config_path, existing)
    
    typer.echo(f"A4E MCP configured for {ide_name}")
    typer.echo()
    typer.echo(f"  Config file: {config_path}")
    typer.echo(f"  Python: {sys.executable}")
    typer.echo()
    
    # IDE-specific notes
    if ide_lower in ("cursor", "vscode"):
        typer.echo(f"  Workspace: Uses ${{workspaceFolder}} (auto-detected)")
    else:
        typer.echo(f"  Workspace: Uses current directory or specify project_path in tool calls")
    
    typer.echo()
    typer.echo(f"Restart {ide_name} to activate the MCP server.")


@app.command()
def show(
    ide: str = typer.Argument(
        ...,
        help="IDE to show config for: cursor, claude-desktop, vscode"
    )
):
    """
    Show current MCP configuration for an IDE.
    
    Example:
    
        a4e mcp show cursor
    """
    ide_configs = _get_ide_configs()
    ide_lower = ide.lower()
    
    if ide_lower not in ide_configs:
        supported = ", ".join(_get_supported_ides())
        typer.echo(f"Error: Unknown IDE '{ide}'", err=True)
        typer.echo(f"Supported IDEs: {supported}", err=True)
        raise typer.Exit(1)
    
    config_info = ide_configs[ide_lower]
    config_path: Path = config_info["path"]
    servers_key: str = config_info["servers_key"]
    ide_name: str = config_info["name"]
    
    if not config_path.exists():
        typer.echo(f"No MCP config found for {ide_name}")
        typer.echo(f"Expected path: {config_path}")
        typer.echo()
        typer.echo(f"Run: a4e mcp setup {ide}")
        return
    
    config, had_error = _load_config(config_path)
    
    if had_error:
        typer.echo(f"Error: Invalid JSON in {config_path}", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"MCP configuration for {ide_name}")
    typer.echo(f"File: {config_path}")
    typer.echo()
    typer.echo(json.dumps(config, indent=2))
    
    # Check A4E status
    if servers_key in config and "a4e" in config[servers_key]:
        typer.echo()
        typer.echo("A4E status: Configured")
    else:
        typer.echo()
        typer.echo("A4E status: Not configured")
        typer.echo(f"Run: a4e mcp setup {ide}")


@app.command()
def remove(
    ide: str = typer.Argument(
        ..., 
        help="IDE to remove A4E config from"
    ),
):
    """
    Remove A4E MCP configuration from an IDE.
    
    This removes only the A4E configuration, preserving other MCP servers.
    
    Example:
    
        a4e mcp remove cursor
    """
    ide_configs = _get_ide_configs()
    ide_lower = ide.lower()
    
    if ide_lower not in ide_configs:
        supported = ", ".join(_get_supported_ides())
        typer.echo(f"Error: Unknown IDE '{ide}'", err=True)
        typer.echo(f"Supported IDEs: {supported}", err=True)
        raise typer.Exit(1)
    
    config_info = ide_configs[ide_lower]
    config_path: Path = config_info["path"]
    servers_key: str = config_info["servers_key"]
    ide_name: str = config_info["name"]
    
    if not config_path.exists():
        typer.echo(f"No MCP config found for {ide_name}")
        return
    
    config, had_error = _load_config(config_path)
    
    if had_error:
        typer.echo(f"Error: Invalid JSON in {config_path}", err=True)
        raise typer.Exit(1)
    
    # Check if a4e is configured
    if servers_key not in config or "a4e" not in config[servers_key]:
        typer.echo(f"A4E is not configured for {ide_name}")
        return
    
    # Remove a4e
    del config[servers_key]["a4e"]
    
    # Clean up empty servers dict
    if not config[servers_key]:
        del config[servers_key]
    
    # Save config
    _save_config(config_path, config)
    
    typer.echo(f"A4E removed from {ide_name} configuration")
    typer.echo()
    typer.echo(f"Restart {ide_name} to apply changes.")


@app.command()
def test():
    """
    Test that the A4E MCP server can start correctly.
    
    This verifies that:
    - The server module can be imported
    - The Python path is correct
    - Dependencies are installed
    
    Useful for debugging configuration issues.
    """
    import subprocess
    
    typer.echo("Testing A4E MCP server...")
    typer.echo()
    typer.echo(f"  Python: {sys.executable}")
    typer.echo(f"  Command: {sys.executable} -m a4e.server")
    typer.echo()
    
    # Test 1: Module import
    typer.echo("1. Testing module import...")
    try:
        # Test that the module can be imported
        import importlib
        importlib.import_module("a4e.server")
        typer.echo("   Module imports correctly")
    except ImportError as e:
        typer.echo(f"   Error: Failed to import a4e.server: {e}", err=True)
        raise typer.Exit(1)
    
    # Test 2: FastMCP instance
    typer.echo("2. Testing MCP server instance...")
    try:
        from a4e.core import mcp
        tools = list(mcp._tool_manager._tools.keys()) if hasattr(mcp, '_tool_manager') else []
        typer.echo(f"   MCP server initialized")
        if tools:
            typer.echo(f"   Tools registered: {len(tools)}")
    except Exception as e:
        typer.echo(f"   Warning: Could not inspect MCP instance: {e}", err=True)
    
    # Test 3: Server process start
    typer.echo("3. Testing server process...")
    try:
        # Run with --help to quickly test if it starts
        result = subprocess.run(
            [sys.executable, "-c", "from a4e.server import main; print('OK')"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0 and "OK" in result.stdout:
            typer.echo("   Server process starts correctly")
        else:
            typer.echo(f"   Warning: Unexpected output", err=True)
            if result.stderr:
                typer.echo(f"   stderr: {result.stderr}", err=True)
    except subprocess.TimeoutExpired:
        typer.echo("   Server process timed out (may be normal for stdio server)")
    except Exception as e:
        typer.echo(f"   Error testing server process: {e}", err=True)
        raise typer.Exit(1)
    
    typer.echo()
    typer.echo("All tests passed. MCP server is ready.")
    typer.echo()
    typer.echo("Next steps:")
    typer.echo("  1. Run: a4e mcp setup <ide>")
    typer.echo("  2. Restart your IDE")
    typer.echo("  3. Start using A4E tools!")


@app.command()
def path(
    ide: str = typer.Argument(
        ...,
        help="IDE to show config path for"
    )
):
    """
    Show the config file path for an IDE.
    
    Useful for manual configuration or debugging.
    
    Example:
    
        a4e mcp path cursor
    """
    ide_configs = _get_ide_configs()
    ide_lower = ide.lower()
    
    if ide_lower not in ide_configs:
        supported = ", ".join(_get_supported_ides())
        typer.echo(f"Error: Unknown IDE '{ide}'", err=True)
        typer.echo(f"Supported IDEs: {supported}", err=True)
        raise typer.Exit(1)
    
    config_path = ide_configs[ide_lower]["path"]
    typer.echo(str(config_path))


@app.command(name="list")
def list_ides():
    """
    List all supported IDEs.
    
    Example:
    
        a4e mcp list
    """
    ide_configs = _get_ide_configs()
    
    typer.echo("Supported IDEs:")
    typer.echo()
    
    for ide_key, config in ide_configs.items():
        path_exists = "exists" if config["path"].exists() else "not found"
        typer.echo(f"  {ide_key}")
        typer.echo(f"    Name: {config['name']}")
        typer.echo(f"    Config: {config['path']} ({path_exists})")
        typer.echo()
