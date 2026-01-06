"""
Add tool tool.

Creates tools with the params: Dict[str, Any] pattern required by the A4E main application.
Also includes exec() compatibility helpers for proper module loading.
"""

from typing import Optional

from ...core import mcp, jinja_env, get_project_dir


@mcp.tool()
def add_tool(
    tool_name: str, description: str, parameters: dict, agent_name: Optional[str] = None
) -> dict:
    """
    Add a new tool with params: Dict[str, Any] signature (A4E compatible)

    Args:
        tool_name: Name of the tool (snake_case)
        description: What the tool does
        parameters: Dictionary of parameters with types and descriptions
        agent_name: Optional agent ID if not in agent directory
    
    The generated tool will use the params dict pattern:
        def tool_name(params: Dict[str, Any]) -> Dict[str, Any]
    
    This is required for compatibility with the A4E main application's
    exec() context and tool wrapping system.
    """
    # Validate tool name
    if not tool_name.replace("_", "").isalnum():
        suggested = tool_name.replace("-", "_").replace(" ", "_").lower()
        return {
            "success": False,
            "error": "Tool name must be alphanumeric with underscores",
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

    tool_file = tools_dir / f"{tool_name}.py"
    if tool_file.exists():
        return {
            "success": False,
            "error": f"Tool '{tool_name}' already exists",
            "fix": "Use update_tool() to modify or remove_tool() first",
        }

    try:
        # Prepare parameters with Python types
        mapped_params = {}
        type_mapping = {
            "string": "str",
            "number": "float",
            "integer": "int",
            "boolean": "bool",
            "array": "List",
            "object": "dict",
        }

        for name, info in parameters.items():
            # Handle both simple format {'a': 'number'} and detailed format {'a': {'type': 'number', 'description': '...'}}
            if isinstance(info, str):
                param_info = {"type": info}
            else:
                param_info = info.copy()
            raw_type = param_info.get("type", "Any")

            # Map JSON type to Python type, or use as-is if not in map (allows direct Python types)
            py_type = type_mapping.get(raw_type, raw_type)

            # Handle optional parameters
            # Check for "required" key (boolean)
            is_required = param_info.get("required", False)

            if not is_required:
                py_type = f"Optional[{py_type}] = None"

            param_info["type"] = py_type
            param_info["is_required"] = is_required
            mapped_params[name] = param_info

        # Sort parameters: required first, then optional (to avoid SyntaxError)
        sorted_params = dict(
            sorted(mapped_params.items(), key=lambda x: (not x[1]["is_required"], x[0]))
        )

        template = jinja_env.get_template("tool.py.j2")
        code = template.render(
            tool_name=tool_name, description=description, parameters=sorted_params
        )
        tool_file.write_text(code)

        # Auto-generate schemas after adding tool
        from ..schemas import generate_schemas
        generate_schemas(force=False, agent_name=agent_name)

        return {
            "success": True,
            "message": f"Created tool '{tool_name}'",
            "path": str(tool_file),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

