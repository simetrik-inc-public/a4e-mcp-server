"""
List views tool.
"""

from typing import Optional

from ...core import mcp, get_project_dir


@mcp.tool()
def list_views(agent_name: Optional[str] = None) -> dict:
    """
    List all views available in the current agent project
    """
    project_dir = get_project_dir(agent_name)
    views_dir = project_dir / "views"

    if not views_dir.exists():
        return {"views": [], "count": 0}

    views = []
    for view_dir in views_dir.iterdir():
        if view_dir.is_dir() and (view_dir / "view.tsx").exists():
            views.append(view_dir.name)

    return {"views": sorted(views), "count": len(views)}

