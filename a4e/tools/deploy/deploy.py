"""
Deploy agent tool.
"""

from typing import Optional
from urllib.parse import urlencode

from ...core import mcp, get_project_dir
from ..validation import validate
from ..schemas import generate_schemas

HUB_URL = "https://dev-a4e.global.simetrik.com"


@mcp.tool()
def deploy(
    environment: str = "production",
    auto_publish: bool = False,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Deploy agent to A4E Hub.

    This validates the agent, regenerates schemas, and prepares it for deployment.
    To test locally with the playground, use `dev_start` instead.
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
        "message": f"Agent '{agent_id}' validated and schemas generated for {environment}",
        "agent_id": agent_id,
        "next_steps": [
            f"Run 'a4e dev start' to test locally with the playground",
            f"The playground URL will be: {HUB_URL}/builder/playground?url=<ngrok_url>&agent={agent_id}",
        ],
        "details": {
            "validation": val_result,
            "schema_generation": gen_result,
        },
    }

