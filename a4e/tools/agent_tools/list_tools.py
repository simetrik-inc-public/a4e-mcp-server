"""
List tools tool.
"""

from typing import Optional

from ...core import mcp, get_project_dir


@mcp.tool()
def list_tools(agent_name: Optional[str] = None) -> dict:
    """
    List all tools available in the current agent project
    """
    project_dir = get_project_dir(agent_name)
    tools_dir = project_dir / "tools"

    if not tools_dir.exists():
        return {"tools": [], "count": 0}

    tools = []
    for tool_file in tools_dir.glob("*.py"):
        if tool_file.name == "__init__.py":
            continue
        tools.append(tool_file.stem)

    return {"tools": sorted(tools), "count": len(tools)}

