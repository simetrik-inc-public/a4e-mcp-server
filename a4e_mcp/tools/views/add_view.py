"""
Add view tool.
"""

from typing import Optional

from ...core import mcp, get_project_dir
from .helpers import create_view


@mcp.tool()
def add_view(
    view_id: str, description: str, props: dict, agent_name: Optional[str] = None
) -> dict:
    """
    Add a new React view

    Args:
        view_id: ID of the view (snake_case, e.g., "meal_plan")
        description: View purpose
        props: Dictionary of props with types
        agent_name: Optional agent ID if not in agent directory
    """
    # Validate view ID
    if not view_id.replace("_", "").isalnum():
        return {
            "success": False,
            "error": "View ID must be alphanumeric with underscores",
        }

    project_dir = get_project_dir(agent_name)
    result = create_view(view_id, description, props, project_dir)

    # Auto-generate schemas after adding view
    if result.get("success"):
        from ..schemas import generate_schemas
        generate_schemas(force=False, agent_name=agent_name)

    return result

