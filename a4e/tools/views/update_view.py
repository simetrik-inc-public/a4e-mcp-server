"""
Update view - modify existing view's description or props.
"""

import json
from typing import Optional

from ...core import mcp, jinja_env, get_project_dir


@mcp.tool()
def update_view(
    view_id: str,
    description: Optional[str] = None,
    props: Optional[dict] = None,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Update an existing view's description or props.

    Args:
        view_id: ID of the view to update
        description: New description (optional)
        props: New props dict (optional, replaces all props)
        agent_name: Optional agent ID if not in agent directory
    """
    project_dir = get_project_dir(agent_name)
    views_dir = project_dir / "views"

    if not views_dir.exists():
        return {
            "success": False,
            "error": f"views/ directory not found at {views_dir}",
            "fix": "Make sure you're in an agent project directory or specify agent_name",
        }

    view_dir = views_dir / view_id
    if not view_dir.exists():
        # List available views for helpful error
        available = [d.name for d in views_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
        return {
            "success": False,
            "error": f"View '{view_id}' not found",
            "fix": f"Available views: {', '.join(available) if available else 'none'}",
        }

    if description is None and props is None:
        return {
            "success": False,
            "error": "Nothing to update",
            "fix": "Provide at least one of: description, props",
        }

    try:
        # Read current schema to get existing values
        schema_file = view_dir / "view.schema.json"
        if schema_file.exists():
            current_schema = json.loads(schema_file.read_text())
            if description is None:
                description = current_schema.get("description", f"View: {view_id}")
            if props is None:
                # Extract props from schema
                props = {}
                for prop_name, prop_info in current_schema.get("props", {}).get("properties", {}).items():
                    props[prop_name] = prop_info.get("type", "string")
        else:
            if description is None:
                description = f"View: {view_id}"
            if props is None:
                return {
                    "success": False,
                    "error": "Props must be specified when no schema exists",
                    "fix": "Provide the props dict with all props for the view",
                }

        # Convert snake_case to PascalCase for component name
        view_name = "".join(word.title() for word in view_id.split("_"))

        # Regenerate view.tsx
        template = jinja_env.get_template("view.tsx.j2")
        code = template.render(view_name=view_name, description=description, props=props)
        (view_dir / "view.tsx").write_text(code)

        # Regenerate view.schema.json
        schema_properties = {}
        required_props = []
        for prop_name, prop_type in props.items():
            if isinstance(prop_type, dict):
                schema_properties[prop_name] = {
                    "type": prop_type.get("type", "string"),
                    "description": prop_type.get("description", f"The {prop_name} prop"),
                }
                if prop_type.get("required", True):
                    required_props.append(prop_name)
            else:
                schema_properties[prop_name] = {
                    "type": prop_type,
                    "description": f"The {prop_name} prop",
                }
                required_props.append(prop_name)

        view_schema = {
            "name": view_id,
            "description": description,
            "props": {
                "type": "object",
                "properties": schema_properties,
                "required": required_props,
            },
        }
        (view_dir / "view.schema.json").write_text(json.dumps(view_schema, indent=2))

        # Regenerate schemas
        from ..schemas import generate_schemas
        generate_schemas(force=True, agent_name=agent_name)

        return {
            "success": True,
            "message": f"Updated view '{view_id}'",
            "path": str(view_dir),
            "files": ["view.tsx", "view.schema.json"],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
