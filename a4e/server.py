"""
A4E MCP Server - Main entry point.

This server provides tools for creating and managing A4E agents.
All tools are organized in the tools/ directory by category.

IMPORTANT: This server communicates via stdio (stdin/stdout).
All logging MUST go to stderr to avoid breaking the MCP protocol.
"""

from pathlib import Path
import argparse
import sys

from .core import mcp, set_project_dir


def _log_error(message: str) -> None:
    """Log error to stderr (never stdout, which is reserved for MCP protocol)."""
    print(f"[a4e] {message}", file=sys.stderr)

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
    # Parse CLI arguments (standard MCP pattern)
    parser = argparse.ArgumentParser(
        description="A4E MCP Server for agent creation and management"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        help="Root directory for agent projects (standard MCP pattern). "
        "Agents will be created in {project-dir}/file-store/agent-store/",
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

    # Run MCP server
    mcp.run()


if __name__ == "__main__":
    main()
