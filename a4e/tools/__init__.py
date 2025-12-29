"""
A4E MCP Tools - All tools for agent creation and management.

Structure:
- project/      : Project initialization (initialize_project, get_agent_info)
- agent_tools/  : Tool management (add_tool, list_tools, remove_tool)
- views/        : View management (add_view, list_views, remove_view)
- skills/       : Skill management (add_skill, list_skills, remove_skill)
- schemas/      : Schema generation (generate_schemas)
- validation/   : Validation (validate)
- dev/          : Development server (dev_start, dev_stop, check_environment)
- deploy/       : Deployment (deploy)
"""

# Project tools
from .project import initialize_project, get_agent_info

# Agent tools management
from .agent_tools import add_tool, list_tools, remove_tool

# Views management
from .views import add_view, list_views, remove_view

# Skills management
from .skills import add_skill, list_skills, remove_skill

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
    "remove_tool",
    # Views
    "add_view",
    "list_views",
    "remove_view",
    # Skills
    "add_skill",
    "list_skills",
    "remove_skill",
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

