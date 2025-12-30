"""
Get agent info tool.
"""

from typing import Optional
import json

from ...core import mcp, get_project_dir


@mcp.tool()
def get_agent_info(agent_name: Optional[str] = None) -> dict:
    """
    Get general metadata and info about the current agent
    """
    project_dir = get_project_dir(agent_name)
    metadata_file = project_dir / "metadata.json"

    if not metadata_file.exists():
        return {
            "error": f"metadata.json not found in {project_dir}. Are you in an agent project?"
        }

    try:
        metadata = json.loads(metadata_file.read_text())

        # Count structure
        tools_dir = project_dir / "tools"
        views_dir = project_dir / "views"
        skills_dir = project_dir / "skills"
        prompts_dir = project_dir / "prompts"

        tools = []
        if tools_dir.exists():
            tools = [f.stem for f in tools_dir.glob("*.py") if f.stem != "__init__"]

        views = []
        if views_dir.exists():
            views = [d.name for d in views_dir.iterdir() if d.is_dir() and (d / "view.tsx").exists()]

        skills = []
        if skills_dir.exists():
            skills = [d.name for d in skills_dir.iterdir() if d.is_dir()]

        prompts = []
        if prompts_dir.exists():
            prompts = [f.stem for f in prompts_dir.glob("*.md")]

        return {
            "agent_id": project_dir.name,
            "metadata": metadata,
            "path": str(project_dir),
            "structure": {
                "tools": tools,
                "tools_count": len(tools),
                "views": views,
                "views_count": len(views),
                "skills": skills,
                "skills_count": len(skills),
                "prompts": prompts,
                "prompts_count": len(prompts),
            }
        }
    except Exception as e:
        return {"error": f"Failed to read metadata: {str(e)}"}

