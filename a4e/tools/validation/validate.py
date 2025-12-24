"""
Validate agent structure tool.
"""

from typing import Optional
from collections import defaultdict
import ast
import json

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
    - Skills integrity (triggers, dependencies, orphans)
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

    errors = []
    warnings = []

    if strict:
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
            view_dirs = [
                d
                for d in views_dir.iterdir()
                if d.is_dir() and (d / "view.tsx").exists()
            ]
            if not (views_dir / "schemas.json").exists() and view_dirs:
                errors.append(
                    "Views exist but views/schemas.json is missing. Run generate_schemas."
                )

        # 4. Validate skills integrity
        skills_dir = project_dir / "skills"
        if skills_dir.exists():
            skill_errors, skill_warnings = _validate_skills(
                skills_dir, tools_dir, views_dir
            )
            errors.extend(skill_errors)
            warnings.extend(skill_warnings)

    if errors:
        result = {
            "success": False,
            "error": "Validation failed",
            "details": errors,
        }
        if warnings:
            result["warnings"] = warnings
        return result

    result = {"success": True, "message": "Agent structure is valid"}
    if warnings:
        result["warnings"] = warnings
    return result


def _validate_skills(skills_dir, tools_dir, views_dir) -> tuple:
    """
    Validate skills for integrity issues.
    
    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []
    
    schema_file = skills_dir / "schemas.json"
    
    # Check if schemas.json exists when skill folders exist
    skill_folders = [d for d in skills_dir.iterdir() if d.is_dir()]
    if skill_folders and not schema_file.exists():
        errors.append("Skills exist but skills/schemas.json is missing.")
        return errors, warnings
    
    if not schema_file.exists():
        return errors, warnings
    
    try:
        schemas = json.loads(schema_file.read_text())
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in skills/schemas.json: {e}")
        return errors, warnings
    
    # Get existing tools and views for dependency validation
    existing_tools = set()
    if tools_dir.exists():
        tools_schema = tools_dir / "schemas.json"
        if tools_schema.exists():
            try:
                ts = json.loads(tools_schema.read_text())
                if isinstance(ts, dict):
                    existing_tools = set(ts.keys())
                else:
                    existing_tools = {t.get("name") for t in ts if isinstance(t, dict)}
            except Exception:
                pass
    
    existing_views = set()
    if views_dir.exists():
        existing_views = {d.name for d in views_dir.iterdir() if d.is_dir() and (d / "view.tsx").exists()}
    
    # Track triggers for duplicate detection
    trigger_to_skills = defaultdict(list)
    
    for skill_id, skill_data in schemas.items():
        # Check SKILL.md exists
        skill_md = skills_dir / skill_id / "SKILL.md"
        if not skill_md.exists():
            warnings.append(f"Skill '{skill_id}' missing SKILL.md documentation")
        
        # Check output view exists
        output = skill_data.get("output", {})
        view_id = output.get("view")
        if view_id and view_id != "NONE" and view_id not in existing_views:
            errors.append(f"Skill '{skill_id}' references non-existent view '{view_id}'")
        
        # Check internal tools exist
        internal_tools = skill_data.get("internal_tools", [])
        for tool in internal_tools:
            if tool not in existing_tools:
                warnings.append(f"Skill '{skill_id}' references tool '{tool}' not in schemas")
        
        # Collect triggers for duplicate detection
        triggers = skill_data.get("intent_triggers", [])
        for trigger in triggers:
            trigger_lower = trigger.lower().strip()
            trigger_to_skills[trigger_lower].append(skill_id)
    
    # Check for orphan SKILL.md (folder exists but not in schemas.json)
    for skill_folder in skill_folders:
        if skill_folder.name not in schemas:
            warnings.append(f"Orphan skill folder '{skill_folder.name}' not in schemas.json")
    
    # Detect duplicate triggers
    for trigger, skills in trigger_to_skills.items():
        if len(skills) > 1:
            warnings.append(f"Duplicate trigger '{trigger}' in skills: {', '.join(skills)}")
    
    return errors, warnings
