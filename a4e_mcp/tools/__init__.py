"""
A4E MCP Tools - All tools for agent creation and management.

Structure:
- project/      : Project initialization (initialize_project, get_agent_info)
- agent_tools/  : Tool management (add_tool, list_tools)
- views/        : View management (add_view, list_views)
- schemas/      : Schema generation (generate_schemas)
- validation/   : Validation (validate)
- dev/          : Development server (dev_start, dev_stop, check_environment)
- deploy/       : Deployment (deploy)
"""

# Project tools
from .project import initialize_project, get_agent_info

# Agent tools management
from .agent_tools import add_tool, list_tools

# Views management
from .views import add_view, list_views

# Schema generation
from .schemas import generate_schemas

# Validation
from .validation import validate

# Development
from .dev import dev_start, dev_stop, check_environment

# Deployment
from .deploy import deploy

__all__ = [
    # Project
    "initialize_project",
    "get_agent_info",
    # Agent tools
    "add_tool",
    "list_tools",
    # Views
    "add_view",
    "list_views",
    # Schemas
    "generate_schemas",
    # Validation
    "validate",
    # Development
    "dev_start",
    "dev_stop",
    "check_environment",
    # Deployment
    "deploy",
]

