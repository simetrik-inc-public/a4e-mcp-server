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
        return {
            "agent_id": project_dir.name,
            "metadata": metadata,
            "path": str(project_dir),
        }
    except Exception as e:
        return {"error": f"Failed to read metadata: {str(e)}"}

