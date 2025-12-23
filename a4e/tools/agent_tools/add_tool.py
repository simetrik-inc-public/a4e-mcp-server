"""
Add tool tool.
"""

from typing import Optional

from ...core import mcp, jinja_env, get_project_dir


@mcp.tool()
def add_tool(
    tool_name: str, description: str, parameters: dict, agent_name: Optional[str] = None
) -> dict:
    """
    Add a new tool with @tool decorator

    Args:
        tool_name: Name of the tool (snake_case)
        description: What the tool does
        parameters: Dictionary of parameters with types and descriptions
        agent_name: Optional agent ID if not in agent directory
    """
    # Validate tool name
    if not tool_name.replace("_", "").isalnum():
        return {
            "success": False,
            "error": "Tool name must be alphanumeric with underscores",
        }

    project_dir = get_project_dir(agent_name)
    tools_dir = project_dir / "tools"

    if not tools_dir.exists():
        return {
            "success": False,
            "error": f"tools/ directory not found at {tools_dir}. Are you in an agent project?",
        }

    tool_file = tools_dir / f"{tool_name}.py"
    if tool_file.exists():
        return {"success": False, "error": f"Tool '{tool_name}' already exists"}

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
            # Create a copy to avoid modifying original dict
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

