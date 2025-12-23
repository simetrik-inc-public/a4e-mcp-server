"""
Helper functions for view management.
"""

from pathlib import Path

from ...core import jinja_env


def create_view(
    view_id: str, description: str, props: dict, project_dir: Path
) -> dict:
    """
    Helper to create a view directory with view.tsx file.
    
    Args:
        view_id: ID of the view (snake_case)
        description: View purpose
        props: Dictionary of props with types
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

        template = jinja_env.get_template("view.tsx.j2")
        code = template.render(
            view_name=view_name, description=description, props=props
        )
        (view_dir / "view.tsx").write_text(code)

        return {
            "success": True,
            "message": f"Created view '{view_id}'",
            "path": str(view_dir),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

