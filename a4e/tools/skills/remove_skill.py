"""
Remove skill tool.
"""

from pathlib import Path
from typing import Optional
import json
import shutil

from ...core import mcp, get_project_dir


@mcp.tool()
def remove_skill(
    skill_id: str,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Remove a skill from the agent

    Args:
        skill_id: ID of the skill to remove (the folder name)
        agent_name: Optional agent ID if not in agent directory

    Returns:
        Result with success status and removed folder path
    """
    project_dir = get_project_dir(agent_name)
    skills_dir = project_dir / "skills"

    if not skills_dir.exists():
        return {
            "success": False,
            "error": f"skills/ directory not found at {skills_dir}. Are you in an agent project?",
        }

    skill_folder = skills_dir / skill_id

    if not skill_folder.exists():
        return {
            "success": False,
            "error": f"Skill '{skill_id}' not found at {skill_folder}",
        }

    # Prevent removing the mandatory show_welcome skill
    if skill_id == "show_welcome":
        return {
            "success": False,
            "error": "Cannot remove the 'show_welcome' skill - it is required for all agents",
        }

    try:
        # Remove the skill folder and all its contents
        shutil.rmtree(skill_folder)

        # Update schemas.json if it exists
        schemas_file = skills_dir / "schemas.json"
        if schemas_file.exists():
            try:
                schemas = json.loads(schemas_file.read_text())
                # Skills schemas is a dict with skill_id as keys
                if skill_id in schemas:
                    del schemas[skill_id]
                    schemas_file.write_text(json.dumps(schemas, indent=2))
            except (json.JSONDecodeError, KeyError):
                pass  # Ignore schema update errors

        return {
            "success": True,
            "message": f"Removed skill '{skill_id}'",
            "removed_folder": str(skill_folder),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
