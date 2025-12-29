"""
Remove tool tool.
"""

from pathlib import Path
from typing import Optional
import json

from ...core import mcp, get_project_dir


@mcp.tool()
def remove_tool(
    tool_name: str,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Remove a tool from the agent

    Args:
        tool_name: Name of the tool to remove (without .py extension)
        agent_name: Optional agent ID if not in agent directory

    Returns:
        Result with success status and removed file path
    """
    project_dir = get_project_dir(agent_name)
    tools_dir = project_dir / "tools"

    if not tools_dir.exists():
        return {
            "success": False,
            "error": f"tools/ directory not found at {tools_dir}",
            "fix": "Initialize an agent first with initialize_project() or specify agent_name",
        }

    tool_file = tools_dir / f"{tool_name}.py"

    if not tool_file.exists():
        # List available tools for helpful error
        available = [f.stem for f in tools_dir.glob("*.py") if f.stem != "__init__"]
        return {
            "success": False,
            "error": f"Tool '{tool_name}' not found",
            "fix": f"Available tools: {', '.join(available) if available else 'none'}",
        }

    try:
        # Remove the tool file
        tool_file.unlink()

        # Update schemas.json if it exists
        schemas_file = tools_dir / "schemas.json"
        if schemas_file.exists():
            try:
                schemas = json.loads(schemas_file.read_text())
                if tool_name in schemas:
                    del schemas[tool_name]
                    schemas_file.write_text(json.dumps(schemas, indent=2))
            except (json.JSONDecodeError, KeyError):
                pass  # Ignore schema update errors

        return {
            "success": True,
            "message": f"Removed tool '{tool_name}'",
            "removed_file": str(tool_file),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
