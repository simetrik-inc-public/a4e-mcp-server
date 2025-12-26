"""
Helper functions for skill management.
"""

from pathlib import Path
import json
from typing import List, Optional

from ...core import jinja_env


def create_skill(
    skill_id: str,
    name: str,
    description: str,
    intent_triggers: List[str],
    output_view: str,
    internal_tools: Optional[List[str]] = None,
    requires_auth: bool = False,
    view_props: Optional[dict] = None,
    project_dir: Path = None,
) -> dict:
    """
    Helper to create a skill directory with SKILL.md file.

    Args:
        skill_id: ID of the skill (snake_case)
        name: Human-readable name
        description: What the skill does
        intent_triggers: Phrases that trigger this skill
        output_view: View ID to render (or "NONE" for no view)
        internal_tools: List of tool names this skill uses
        requires_auth: Whether auth is required
        view_props: Expected props for the output view
        project_dir: Path to the agent project directory

    Returns:
        Result dictionary with success status
    """
    if project_dir is None:
        return {"success": False, "error": "project_dir is required"}

    skills_dir = project_dir / "skills"

    if not skills_dir.exists():
        return {
            "success": False,
            "error": f"skills/ directory not found at {skills_dir}",
        }

    skill_dir = skills_dir / skill_id
    if skill_dir.exists():
        return {"success": False, "error": f"Skill '{skill_id}' already exists"}

    try:
        skill_dir.mkdir()

        # Convert snake_case to Title Case for display
        skill_name = name or " ".join(word.title() for word in skill_id.split("_"))

        # Generate SKILL.md
        template = jinja_env.get_template("skills/skill.md.j2")
        skill_md = template.render(
            skill_name=skill_name,
            description=description,
            intent_triggers=intent_triggers,
            internal_tools=internal_tools or [],
            output_view=output_view,
            requires_auth=requires_auth,
            view_props=view_props or {},
        )
        (skill_dir / "SKILL.md").write_text(skill_md)

        # Update skills/schemas.json
        _update_skills_schema(
            skills_dir=skills_dir,
            skill_id=skill_id,
            name=skill_name,
            description=description,
            intent_triggers=intent_triggers,
            output_view=output_view,
            internal_tools=internal_tools,
            requires_auth=requires_auth,
        )

        return {
            "success": True,
            "message": f"Created skill '{skill_id}'",
            "path": str(skill_dir),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _update_skills_schema(
    skills_dir: Path,
    skill_id: str,
    name: str,
    description: str,
    intent_triggers: List[str],
    output_view: str,
    internal_tools: Optional[List[str]] = None,
    requires_auth: bool = False,
) -> None:
    """
    Update the skills/schemas.json file with the new skill.
    """
    schema_file = skills_dir / "schemas.json"

    # Load existing schemas or create empty dict
    if schema_file.exists():
        try:
            schemas = json.loads(schema_file.read_text())
        except json.JSONDecodeError:
            schemas = {}
    else:
        schemas = {}

    # Build output object
    output = {"view": output_view}
    if output_view == "NONE":
        output["view"] = "NONE"

    # Add new skill schema
    schemas[skill_id] = {
        "id": skill_id,
        "name": name,
        "description": description,
        "intent_triggers": intent_triggers,
        "requires_auth": requires_auth,
        "internal_tools": internal_tools or [],
        "output": output,
    }

    # Write updated schemas
    schema_file.write_text(json.dumps(schemas, indent=2))

