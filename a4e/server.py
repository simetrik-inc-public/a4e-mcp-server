"""
A4E MCP Server - Main entry point.

This server provides tools for creating and managing A4E agents.
All tools are organized in the tools/ directory by category.

IMPORTANT: This server communicates via stdio (stdin/stdout).
All logging MUST go to stderr to avoid breaking the MCP protocol.
"""

from pathlib import Path
import argparse
import os
import sys

from .core import mcp, set_project_dir

# Global auth state
_AUTH_TOKEN: str | None = None
_AUTH_REQUIRED: bool = False


def _log_error(message: str) -> None:
    """Log error to stderr (never stdout, which is reserved for MCP protocol)."""
    print(f"[a4e] {message}", file=sys.stderr)


def _log_info(message: str) -> None:
    """Log info to stderr (never stdout, which is reserved for MCP protocol)."""
    print(f"[a4e] {message}", file=sys.stderr)


def get_auth_token() -> str | None:
    """Get the configured auth token."""
    return _AUTH_TOKEN


def is_auth_required() -> bool:
    """Check if authentication is required."""
    return _AUTH_REQUIRED


def verify_auth_token(token: str) -> dict:
    """
    Verify an access token with A4E Hub.

    Args:
        token: The access token to verify.

    Returns:
        dict: Token introspection response with 'active' boolean.
    """
    try:
        from .utils.oauth import verify_token
        return verify_token(token)
    except ImportError:
        _log_error("OAuth module not available - httpx may not be installed")
        return {"active": False}
    except Exception as e:
        _log_error(f"Token verification failed: {e}")
        return {"active": False}

# Import all tools to register them with the MCP server
# Each tool uses the @mcp.tool() decorator from core.py
from .tools import (
    # Project
    initialize_project,
    get_agent_info,
    get_instructions,
    # Agent tools
    add_tool,
    list_tools,
    remove_tool,
    update_tool,
    # Views
    add_view,
    list_views,
    remove_view,
    update_view,
    # Skills
    add_skill,
    list_skills,
    remove_skill,
    update_skill,
    # Schemas
    generate_schemas,
    # Validation
    validate,
    # Development
    dev_start,
    dev_stop,
    check_environment,
    # Deployment
    deploy,
)


def main():
    """Entry point for the CLI"""
    global _AUTH_TOKEN, _AUTH_REQUIRED

    # Parse CLI arguments (standard MCP pattern)
    parser = argparse.ArgumentParser(
        description="A4E MCP Server for agent creation and management"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        help="Root directory for agent projects (standard MCP pattern). "
        "Agents will be created in {project-dir}/{agent-name}/",
    )
    parser.add_argument(
        "--auth-token",
        type=str,
        help="OAuth access token for authenticated requests. "
        "Can also be set via A4E_AUTH_TOKEN environment variable.",
    )
    parser.add_argument(
        "--require-auth",
        action="store_true",
        help="Require authentication for all requests.",
    )

    args, unknown = parser.parse_known_args()

    # Set global project directory
    if args.project_dir:
        project_dir = Path(args.project_dir).resolve()
        # Validate that it exists
        if not project_dir.exists():
            _log_error(f"Project directory does not exist: {project_dir}")
            sys.exit(1)
        set_project_dir(project_dir)

    # Configure authentication
    _AUTH_TOKEN = args.auth_token or os.getenv("A4E_AUTH_TOKEN")
    _AUTH_REQUIRED = args.require_auth

    if _AUTH_REQUIRED and not _AUTH_TOKEN:
        _log_error("Authentication required but no token provided")
        _log_error("Use --auth-token or set A4E_AUTH_TOKEN environment variable")
        sys.exit(1)

    if _AUTH_TOKEN:
        # Verify token on startup
        result = verify_auth_token(_AUTH_TOKEN)
        if result.get("active"):
            _log_info(f"Authenticated as: {result.get('username', 'unknown')}")
        else:
            if _AUTH_REQUIRED:
                _log_error("Invalid or expired auth token")
                sys.exit(1)
            else:
                _log_info("Warning: Auth token provided but is invalid or expired")

    # Run MCP server
    mcp.run()


if __name__ == "__main__":
    main()
