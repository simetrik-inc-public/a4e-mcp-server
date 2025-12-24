"""
Add skill tool.
"""

from typing import Optional, List
import json

from ...core import mcp, get_project_dir
from .helpers import create_skill


@mcp.tool()
def add_skill(
    skill_id: str,
    name: str,
    description: str,
    intent_triggers: List[str],
    output_view: str,
    internal_tools: Optional[List[str]] = None,
    requires_auth: bool = False,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Add a new skill to the agent

    Args:
        skill_id: ID of the skill (snake_case, e.g., "show_welcome")
        name: Human-readable name (e.g., "Show Welcome")
        description: What the skill does and when to use it
        intent_triggers: List of phrases that trigger this skill
        output_view: View ID to render (e.g., "welcome") or "NONE" for no view
        internal_tools: List of tool names this skill uses (e.g., ["get_agents"])
        requires_auth: Whether this skill requires user authentication
        agent_name: Optional agent ID if not in agent directory
    """
    # Validate skill ID
    if not skill_id.replace("_", "").isalnum():
        return {
            "success": False,
            "error": "Skill ID must be alphanumeric with underscores",
        }

    if not intent_triggers or len(intent_triggers) == 0:
        return {
            "success": False,
            "error": "At least one intent trigger is required",
        }

    project_dir = get_project_dir(agent_name)
    warnings = []

    # Validate output_view exists
    view_props = {}
    if output_view and output_view != "NONE":
        view_dir = project_dir / "views" / output_view
        view_schema_file = view_dir / "view.schema.json"
        
        if not view_dir.exists():
            return {
                "success": False,
                "error": f"View '{output_view}' not found. Create it first with add_view()",
            }
        
        if view_schema_file.exists():
            try:
                schema = json.loads(view_schema_file.read_text())
                view_props = schema.get("props", {}).get("properties", {})
            except Exception:
                warnings.append(f"Could not parse view schema for '{output_view}'")

    # Validate internal_tools exist
    if internal_tools:
        tools_schema_file = project_dir / "tools" / "schemas.json"
        if tools_schema_file.exists():
            try:
                tools_schemas = json.loads(tools_schema_file.read_text())
                # Support both formats: dict (keys are tool names) or list (objects with 'name' field)
                if isinstance(tools_schemas, dict):
                    existing_tools = set(tools_schemas.keys())
                else:
                    existing_tools = {t.get("name") for t in tools_schemas if isinstance(t, dict)}
                
                for tool in internal_tools:
                    if tool not in existing_tools:
                        warnings.append(f"Tool '{tool}' not found in tools/schemas.json. Make sure it exists.")
            except Exception:
                warnings.append("Could not validate internal_tools against tools/schemas.json")

    result = create_skill(
        skill_id=skill_id,
        name=name,
        description=description,
        intent_triggers=intent_triggers,
        output_view=output_view,
        internal_tools=internal_tools,
        requires_auth=requires_auth,
        view_props=view_props,
        project_dir=project_dir,
    )

    # Add warnings to result if any
    if warnings and result.get("success"):
        result["warnings"] = warnings

    return result
