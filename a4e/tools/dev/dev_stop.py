"""
Stop development server tool.
"""

from pathlib import Path
import importlib.util

from ...core import mcp


@mcp.tool()
def dev_stop(port: int = 5000) -> dict:
    """
    Stop development server and cleanup tunnels
    """
    # Import DevManager dynamically
    dev_manager_path = Path(__file__).parent.parent.parent / "utils" / "dev_manager.py"
    spec = importlib.util.spec_from_file_location("dev_manager", dev_manager_path)
    if not spec or not spec.loader:
        return {"success": False, "error": "Failed to load dev_manager module"}
    dev_manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dev_manager_module)
    DevManager = dev_manager_module.DevManager

    return DevManager.stop_dev_server(port)

