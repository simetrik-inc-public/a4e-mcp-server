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
            view_id=view_id,
            view_name=view_name,
            description=description,
            props=props
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


def update_dependencies(
    dependencies: list, project_dir: Path, versions: dict = None
) -> dict:
    """
    Update dependencies.json with new packages (without duplicates).

    Args:
        dependencies: List of npm package names (e.g., ["recharts", "date-fns"])
        project_dir: Path to the agent project directory
        versions: Optional dict of package versions (e.g., {"recharts": "2.10.0"})

    Returns:
        Result dictionary with success status and added packages
    """
    deps_file = project_dir / "dependencies.json"

    # Default versions for common packages
    default_versions = {
        "recharts": "2.10.0",
        "date-fns": "3.0.0",
        "@tanstack/react-table": "8.11.0",
        "lodash": "4.17.21",
        "axios": "1.6.0",
        "zustand": "4.4.0",
        "react-icons": "5.0.0",
        "framer-motion": "10.16.0",
        "chart.js": "4.4.0",
        "react-chartjs-2": "5.2.0",
    }

    try:
        # Load existing dependencies or create new structure
        if deps_file.exists():
            deps_data = json.loads(deps_file.read_text())
        else:
            deps_data = {
                "version": "1.0.0",
                "description": "External dependencies for agent views",
                "dependencies": {}
            }

        existing_deps = deps_data.get("dependencies", {})
        added = []

        for pkg in dependencies:
            if pkg not in existing_deps:
                # Use provided version, default version, or "latest"
                version = (versions or {}).get(pkg) or default_versions.get(pkg) or "latest"
                existing_deps[pkg] = version
                added.append(pkg)

        deps_data["dependencies"] = existing_deps

        # Write updated file
        deps_file.write_text(json.dumps(deps_data, indent=2) + "\n")

        return {
            "success": True,
            "added": added,
            "total": len(existing_deps),
            "message": f"Added {len(added)} new dependencies" if added else "No new dependencies added",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

