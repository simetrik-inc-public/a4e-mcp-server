"""
Start development server tool.
"""

from pathlib import Path
from typing import Optional
import importlib.util

from ...core import mcp, get_project_dir


@mcp.tool()
def dev_start(
    port: int = 5000, auth_token: Optional[str] = None, agent_name: Optional[str] = None
) -> dict:
    """
    Start development mode with ngrok tunnel
    """
    # Import DevManager dynamically
    dev_manager_path = Path(__file__).parent.parent.parent / "utils" / "dev_manager.py"
    spec = importlib.util.spec_from_file_location("dev_manager", dev_manager_path)
    if not spec or not spec.loader:
        return {"success": False, "error": "Failed to load dev_manager module"}
    dev_manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dev_manager_module)
    DevManager = dev_manager_module.DevManager

    project_dir = get_project_dir(agent_name)
    return DevManager.start_dev_server(project_dir, port, auth_token)

