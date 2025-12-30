"""
Helper functions for view management.
"""

import json
from pathlib import Path

from ...core import jinja_env


def create_view(
    view_id: str, description: str, props: dict, project_dir: Path
) -> dict:
    """
    Helper to create a view directory with view.tsx and view.schema.json files.

    Args:
        view_id: ID of the view (snake_case)
        description: View purpose
        props: Dictionary of props with types (e.g., {"title": "string", "count": "number"})
        project_dir: Path to the agent project directory

    Returns:
        Result dictionary with success status
    """
    views_dir = project_dir / "views"

    if not views_dir.exists():
        return {
            "success": False,
            "error": f"views/ directory not found at {views_dir}",
        }

    view_dir = views_dir / view_id
    if view_dir.exists():
        return {"success": False, "error": f"View '{view_id}' already exists"}

    try:
        view_dir.mkdir()

        # Convert snake_case to PascalCase for component name
        view_name = "".join(word.title() for word in view_id.split("_"))

        # Create view.tsx
        template = jinja_env.get_template("view.tsx.j2")
        code = template.render(
            view_name=view_name, description=description, props=props
        )
        (view_dir / "view.tsx").write_text(code)

        # Create view.schema.json (required by A4E View Renderer)
        schema_properties = {}
        required_props = []
        for prop_name, prop_type in props.items():
            # Handle both simple types ("string") and detailed types ({"type": "string", "description": "..."})
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
        (view_dir / "view.schema.json").write_text(
            json.dumps(view_schema, indent=2)
        )

        return {
            "success": True,
            "message": f"Created view '{view_id}' with view.tsx and view.schema.json",
            "path": str(view_dir),
            "files": ["view.tsx", "view.schema.json"],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

