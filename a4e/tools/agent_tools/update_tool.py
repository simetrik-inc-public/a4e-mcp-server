"""
Update tool - modify existing tool's description or parameters.
"""

from typing import Optional

from ...core import mcp, jinja_env, get_project_dir


@mcp.tool()
def update_tool(
    tool_name: str,
    description: Optional[str] = None,
    parameters: Optional[dict] = None,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Update an existing tool's description or parameters.

    Args:
        tool_name: Name of the tool to update
        description: New description (optional)
        parameters: New parameters dict (optional, replaces all parameters)
        agent_name: Optional agent ID if not in agent directory
    """
    project_dir = get_project_dir(agent_name)
    tools_dir = project_dir / "tools"

    if not tools_dir.exists():
        return {
            "success": False,
            "error": f"tools/ directory not found at {tools_dir}",
            "fix": "Make sure you're in an agent project directory or specify agent_name",
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

    if description is None and parameters is None:
        return {
            "success": False,
            "error": "Nothing to update",
            "fix": "Provide at least one of: description, parameters",
        }

    try:
        # Read current tool to extract existing values if needed
        current_content = tool_file.read_text()

        # Extract current description from docstring if not provided
        if description is None:
            import re
            match = re.search(r'"""([^"]+)"""', current_content)
            if match:
                description = match.group(1).strip()
            else:
                description = f"Tool: {tool_name}"

        # If parameters not provided, we need to extract from current file
        if parameters is None:
            # For now, require parameters to be specified for update
            return {
                "success": False,
                "error": "Parameters must be specified when updating",
                "fix": "Provide the parameters dict with all parameters for the tool",
            }

        # Prepare parameters with Python types (same logic as add_tool)
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
            if isinstance(info, str):
                param_info = {"type": info}
            else:
                param_info = info.copy()
            raw_type = param_info.get("type", "Any")
            py_type = type_mapping.get(raw_type, raw_type)
            is_required = param_info.get("required", False)

            if not is_required:
                py_type = f"Optional[{py_type}] = None"

            param_info["type"] = py_type
            param_info["is_required"] = is_required
            mapped_params[name] = param_info

        sorted_params = dict(
            sorted(mapped_params.items(), key=lambda x: (not x[1]["is_required"], x[0]))
        )

        # Regenerate tool file
        template = jinja_env.get_template("tool.py.j2")
        code = template.render(
            tool_name=tool_name, description=description, parameters=sorted_params
        )
        tool_file.write_text(code)

        # Regenerate schemas
        from ..schemas import generate_schemas
        generate_schemas(force=True, agent_name=agent_name)

        return {
            "success": True,
            "message": f"Updated tool '{tool_name}'",
            "path": str(tool_file),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
