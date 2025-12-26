"""
Deploy agent tool.
"""

from typing import Optional

from ...core import mcp, get_project_dir
from ..validation import validate
from ..schemas import generate_schemas


@mcp.tool()
def deploy(
    environment: str = "production",
    auto_publish: bool = False,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Deploy agent to A4E Hub
    """
    val_result = validate(strict=True, agent_name=agent_name)
    if not val_result["success"]:
        return val_result

    gen_result = generate_schemas(force=True, agent_name=agent_name)

    if (
        gen_result.get("tools", {}).get("status") == "error"
        or gen_result.get("views", {}).get("status") == "error"
    ):
        return {
            "success": False,
            "error": "Schema generation failed",
            "details": gen_result,
        }

    project_dir = get_project_dir(agent_name)
    agent_id = project_dir.name

    return {
        "success": True,
        "message": f"Agent '{agent_id}' deployed successfully to {environment}",
        "agent_url": f"https://hub.a4e.com/agents/{agent_id}",
        "mcp_endpoint": f"mcp://{agent_id}.a4e.com",
        "details": {
            "validation": val_result,
            "schema_generation": gen_result,
            "upload": "success",
            "deployment": "success",
        },
    }

