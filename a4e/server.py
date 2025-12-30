"""
A4E MCP Server - Main entry point.

This server provides tools for creating and managing A4E agents.
All tools are organized in the tools/ directory by category.
"""

from pathlib import Path
import argparse

from .core import mcp, set_project_dir

# Import all tools to register them with the MCP server
# Each tool uses the @mcp.tool() decorator from core.py
from .tools import (
    # Project
    initialize_project,
    get_agent_info,
    # Agent tools
    add_tool,
    list_tools,
    # Views
    add_view,
    list_views,
    # Skills
    add_skill,
    list_skills,
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
            print(f"Error: Project directory does not exist: {project_dir}")
            exit(1)
        set_project_dir(project_dir)

    # Run MCP server
    mcp.run()


if __name__ == "__main__":
    main()
