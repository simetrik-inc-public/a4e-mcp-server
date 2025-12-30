"""
Update skill - modify existing skill's properties.
"""

import json
from typing import Optional, List

from ...core import mcp, get_project_dir
from .helpers import create_skill


@mcp.tool()
def update_skill(
    skill_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    intent_triggers: Optional[List[str]] = None,
    output_view: Optional[str] = None,
    internal_tools: Optional[List[str]] = None,
    requires_auth: Optional[bool] = None,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Update an existing skill's properties.

    Args:
        skill_id: ID of the skill to update
        name: New human-readable name (optional)
        description: New description (optional)
        intent_triggers: New list of trigger phrases (optional)
        output_view: New view ID to render (optional)
        internal_tools: New list of tool names (optional)
        requires_auth: New auth requirement (optional)
        agent_name: Optional agent ID if not in agent directory
    """
    project_dir = get_project_dir(agent_name)
    skills_dir = project_dir / "skills"

    if not skills_dir.exists():
        return {
            "success": False,
            "error": f"skills/ directory not found at {skills_dir}",
            "fix": "Make sure you're in an agent project directory or specify agent_name",
        }

    # Check if skill exists in schemas.json
    schemas_file = skills_dir / "schemas.json"
    if not schemas_file.exists():
        return {
            "success": False,
            "error": "skills/schemas.json not found",
            "fix": "Create a skill first with add_skill()",
        }

    try:
        schemas = json.loads(schemas_file.read_text())
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse skills/schemas.json",
            "fix": "Check the file for JSON syntax errors",
        }

    if skill_id not in schemas:
        available = list(schemas.keys())
        return {
            "success": False,
            "error": f"Skill '{skill_id}' not found",
            "fix": f"Available skills: {', '.join(available) if available else 'none'}",
        }

    # Get current skill data
    current = schemas[skill_id]

    # Check if anything to update
    updates = {
        "name": name,
        "description": description,
        "intent_triggers": intent_triggers,
        "output_view": output_view,
        "internal_tools": internal_tools,
        "requires_auth": requires_auth,
    }
    if all(v is None for v in updates.values()):
        return {
            "success": False,
            "error": "Nothing to update",
            "fix": "Provide at least one of: name, description, intent_triggers, output_view, internal_tools, requires_auth",
        }

    # Merge with current values
    final_name = name if name is not None else current.get("name", skill_id)
    final_description = description if description is not None else current.get("description", "")
    final_triggers = intent_triggers if intent_triggers is not None else current.get("intent_triggers", [])
    final_view = output_view if output_view is not None else current.get("output", {}).get("view", "NONE")
    final_tools = internal_tools if internal_tools is not None else current.get("internal_tools", [])
    final_auth = requires_auth if requires_auth is not None else current.get("requires_auth", False)

    warnings = []

    # Validate output_view exists
    view_props = {}
    if final_view and final_view != "NONE":
        view_dir = project_dir / "views" / final_view
        view_schema_file = view_dir / "view.schema.json"

        if not view_dir.exists():
            return {
                "success": False,
                "error": f"View '{final_view}' not found",
                "fix": f"Create it first with add_view() or use an existing view",
            }

        if view_schema_file.exists():
            try:
                schema = json.loads(view_schema_file.read_text())
                view_props = schema.get("props", {}).get("properties", {})
            except Exception:
                warnings.append(f"Could not parse view schema for '{final_view}'")

    # Remove old skill directory if exists
    skill_dir = skills_dir / skill_id
    if skill_dir.exists():
        import shutil
        shutil.rmtree(skill_dir)

    # Remove old entry from schemas
    del schemas[skill_id]
    schemas_file.write_text(json.dumps(schemas, indent=2))

    # Create updated skill
    result = create_skill(
        skill_id=skill_id,
        name=final_name,
        description=final_description,
        intent_triggers=final_triggers,
        output_view=final_view,
        internal_tools=final_tools,
        requires_auth=final_auth,
        view_props=view_props,
        project_dir=project_dir,
    )

    if warnings and result.get("success"):
        result["warnings"] = warnings

    if result.get("success"):
        result["message"] = f"Updated skill '{skill_id}'"

    return result
