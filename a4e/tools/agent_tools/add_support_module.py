"""
Add support module tool.

Creates support modules (db.py, models.py, etc.) with exec() compatibility
for proper loading in the A4E main application.
"""

from typing import Optional

from ...core import mcp, jinja_env, get_project_dir


@mcp.tool()
def add_support_module(
    module_name: str,
    description: str,
    agent_name: Optional[str] = None
) -> dict:
    """
    Add a support module (db.py, models.py, etc.) with exec() compatibility

    Args:
        module_name: Name of the module (snake_case, e.g., "db", "models", "helpers")
        description: What the module does
        agent_name: Optional agent ID if not in agent directory
    
    Support modules are loaded by all tools and need special handling
    to work in the exec() context used by the A4E main application.
    
    The generated module includes:
    - __name__ definition for exec() compatibility
    - sys.path manipulation for imports
    - Self-test code that only runs when executed directly
    """
    # Validate module name
    if not module_name.replace("_", "").isalnum():
        suggested = module_name.replace("-", "_").replace(" ", "_").lower()
        return {
            "success": False,
            "error": "Module name must be alphanumeric with underscores",
            "fix": f"Try: {suggested}",
        }

    project_dir = get_project_dir(agent_name)
    tools_dir = project_dir / "tools"

    if not tools_dir.exists():
        return {
            "success": False,
            "error": f"tools/ directory not found at {tools_dir}",
            "fix": "Initialize an agent first with initialize_project() or specify agent_name",
        }

    module_file = tools_dir / f"{module_name}.py"
    if module_file.exists():
        return {
            "success": False,
            "error": f"Module '{module_name}' already exists",
            "fix": "Edit the existing file or remove it first",
        }

    try:
        # Get agent name for template
        metadata_file = project_dir / "metadata.json"
        agent_display_name = module_name
        if metadata_file.exists():
            import json
            try:
                metadata = json.loads(metadata_file.read_text())
                agent_display_name = metadata.get("name", module_name)
            except Exception:
                pass

        template = jinja_env.get_template("support_module.py.j2")
        code = template.render(
            module_name=module_name,
            description=description,
            agent_name=agent_display_name
        )
        module_file.write_text(code)

        return {
            "success": True,
            "message": f"Created support module '{module_name}' with exec() compatibility",
            "path": str(module_file),
            "notes": [
                "Module includes __name__ fix for exec() context",
                "Module includes sys.path manipulation for imports",
                "Self-test code only runs when executed directly",
                "This module will NOT be included in tools/schemas.json"
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

