"""
List skills tool.
"""

from typing import Optional
import json

from ...core import mcp, get_project_dir


@mcp.tool()
def list_skills(agent_name: Optional[str] = None) -> dict:
    """
    List all skills available in the current agent project
    """
    project_dir = get_project_dir(agent_name)
    skills_dir = project_dir / "skills"

    if not skills_dir.exists():
        return {"skills": [], "count": 0}

    skills = []
    
    # Read from schemas.json if exists
    schema_file = skills_dir / "schemas.json"
    if schema_file.exists():
        try:
            schemas = json.loads(schema_file.read_text())
            for skill_id, skill_data in schemas.items():
                skills.append({
                    "id": skill_id,
                    "name": skill_data.get("name", skill_id),
                    "description": skill_data.get("description", ""),
                    "output_view": skill_data.get("output", {}).get("view", "NONE"),
                    "internal_tools": skill_data.get("internal_tools", []),
                })
        except json.JSONDecodeError:
            pass

    # Fallback: list directories with SKILL.md
    if not skills:
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                skills.append({
                    "id": skill_dir.name,
                    "name": skill_dir.name.replace("_", " ").title(),
                    "description": "",
                    "output_view": "unknown",
                    "internal_tools": [],
                })

    return {"skills": sorted(skills, key=lambda x: x["id"]), "count": len(skills)}

