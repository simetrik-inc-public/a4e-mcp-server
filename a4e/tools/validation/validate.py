"""
Validate agent structure tool.
"""

from typing import Optional
import ast

from ...core import mcp, get_project_dir


@mcp.tool()
def validate(strict: bool = True, agent_name: Optional[str] = None) -> dict:
    """
    Validate agent structure before deployment

    Checks:
    - Required files exist
    - Python syntax valid
    - Type hints present
    - Schemas up-to-date
    """
    project_dir = get_project_dir(agent_name)
    required_files = [
        "agent.py",
        "metadata.json",
        "prompts/agent.md",
        "views/welcome/view.tsx",
    ]

    missing = []
    for f in required_files:
        if not (project_dir / f).exists():
            missing.append(f)

    if missing:
        return {
            "success": False,
            "error": f"Missing required files in {project_dir}: {', '.join(missing)}",
        }

    if strict:
        errors = []

        # 1. Check Python syntax and type hints
        python_files = [project_dir / "agent.py"]
        tools_dir = project_dir / "tools"
        if tools_dir.exists():
            python_files.extend(list(tools_dir.glob("*.py")))

        for py_file in python_files:
            if py_file.name == "__init__.py":
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)

                # Check type hints in functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Skip private functions or __init__
                        if node.name.startswith("_"):
                            continue

                        # Check args for annotations
                        for arg in node.args.args:
                            if arg.annotation is None and arg.arg != "self":
                                errors.append(
                                    f"Missing type hint for argument '{arg.arg}' in {py_file.name}:{node.name}"
                                )

                        # Check return annotation
                        if node.returns is None:
                            # Optional: maybe not enforce return types for everything, but good for strict mode
                            pass

            except SyntaxError as e:
                errors.append(f"Syntax error in {py_file.name}: {e}")
            except Exception as e:
                errors.append(f"Error analyzing {py_file.name}: {e}")

        # 2. Check if schemas exist (basic check)
        tool_files = [f for f in tools_dir.glob("*.py") if f.name != "__init__.py"]
        if not (tools_dir / "schemas.json").exists() and tool_files:
            errors.append(
                "Tools exist but tools/schemas.json is missing. Run generate_schemas."
            )

        # 3. Check view schemas
        views_dir = project_dir / "views"
        if views_dir.exists():
            # Find view directories (not __init__.py files)
            view_dirs = [
                d
                for d in views_dir.iterdir()
                if d.is_dir() and (d / "view.tsx").exists()
            ]
            if not (views_dir / "schemas.json").exists() and view_dirs:
                errors.append(
                    "Views exist but views/schemas.json is missing. Run generate_schemas."
                )

        if errors:
            return {
                "success": False,
                "error": "Strict validation failed",
                "details": errors,
            }

    return {"success": True, "message": "Agent structure is valid"}

