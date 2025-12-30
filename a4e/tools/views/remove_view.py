"""
Remove view tool.
"""

from pathlib import Path
from typing import Optional
import json
import shutil

from ...core import mcp, get_project_dir


@mcp.tool()
def remove_view(
    view_id: str,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Remove a view from the agent

    Args:
        view_id: ID of the view to remove (the folder name)
        agent_name: Optional agent ID if not in agent directory

    Returns:
        Result with success status and removed folder path
    """
    project_dir = get_project_dir(agent_name)
    views_dir = project_dir / "views"

    if not views_dir.exists():
        return {
            "success": False,
            "error": f"views/ directory not found at {views_dir}. Are you in an agent project?",
        }

    view_folder = views_dir / view_id

    if not view_folder.exists():
        return {
            "success": False,
            "error": f"View '{view_id}' not found at {view_folder}",
        }

    # Prevent removing the mandatory welcome view
    if view_id == "welcome":
        return {
            "success": False,
            "error": "Cannot remove the 'welcome' view - it is required for all agents",
        }

    try:
        # Remove the view folder and all its contents
        shutil.rmtree(view_folder)

        # Update schemas.json if it exists
        schemas_file = views_dir / "schemas.json"
        if schemas_file.exists():
            try:
                schemas = json.loads(schemas_file.read_text())
                if view_id in schemas:
                    del schemas[view_id]
                    schemas_file.write_text(json.dumps(schemas, indent=2))
            except (json.JSONDecodeError, KeyError):
                pass  # Ignore schema update errors

        return {
            "success": True,
            "message": f"Removed view '{view_id}'",
            "removed_folder": str(view_folder),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
