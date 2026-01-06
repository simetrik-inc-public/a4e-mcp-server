"""
Validate agent structure tool.

Enhanced validation based on lessons learned from production deployments:
- Tool signature must use params: Dict[str, Any] pattern
- Schemas must be in dictionary format (not array)
- Support files must have __name__ compatibility for exec() context
- Agent prompt should include language policy
"""

from typing import Optional
from collections import defaultdict
import ast
import json
import re

from ...core import mcp, get_project_dir


@mcp.tool()
def validate(strict: bool = True, agent_name: Optional[str] = None) -> dict:
    """
    Validate agent structure before deployment

    Checks:
    - Required files exist
    - Python syntax valid
    - Tool signatures use params: Dict pattern (A4E compatibility)
    - Schemas are in dictionary format (not array)
    - Support files have exec() compatibility
    - Skills integrity (triggers, dependencies, orphans)
    - Agent prompt includes language policy
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

    tools_dir = project_dir / "tools"
    views_dir = project_dir / "views"

    if strict:
        # 1. Check Python syntax and tool signatures
        python_files = [project_dir / "agent.py"]
        if tools_dir.exists():
            python_files.extend(list(tools_dir.glob("*.py")))

        for py_file in python_files:
            if py_file.name == "__init__.py":
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)

                # Check type hints and tool signatures
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Skip private functions or __init__
                        if node.name.startswith("_"):
                            continue
                        
                        # For tool files, check if using params: Dict pattern
                        if py_file.parent == tools_dir and py_file.name not in ["db.py", "models.py", "seed_data.py", "__init__.py"]:
                            tool_errors = _validate_tool_signature(node, py_file.name)
                            errors.extend(tool_errors)

                        # Check args for annotations
                        for arg in node.args.args:
                            if arg.annotation is None and arg.arg != "self":
                                errors.append(
                                    f"Missing type hint for argument '{arg.arg}' in {py_file.name}:{node.name}"
                                )

                # Check exec() compatibility for support files
                if py_file.name in ["db.py", "models.py", "seed_data.py"]:
                    compat_warnings = _check_exec_compatibility(content, py_file.name)
                    warnings.extend(compat_warnings)

            except SyntaxError as e:
                errors.append(f"Syntax error in {py_file.name}: {e}")
            except Exception as e:
                errors.append(f"Error analyzing {py_file.name}: {e}")

        # 2. Check if schemas exist and are in correct format
        if tools_dir.exists():
            tool_files = [f for f in tools_dir.glob("*.py") if f.name not in ["__init__.py", "db.py", "models.py", "seed_data.py"]]
            schemas_file = tools_dir / "schemas.json"
            
            if not schemas_file.exists() and tool_files:
                errors.append(
                    "Tools exist but tools/schemas.json is missing. Run generate_schemas."
                )
            elif schemas_file.exists():
                schema_errors = _validate_tools_schema_format(schemas_file)
                errors.extend(schema_errors)

        # 3. Check view schemas
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

        # 5. Check agent prompt for language policy
        agent_prompt = project_dir / "prompts" / "agent.md"
        if agent_prompt.exists():
            prompt_warnings = _check_agent_prompt(agent_prompt)
            warnings.extend(prompt_warnings)

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


def _validate_tool_signature(func_node: ast.FunctionDef, filename: str) -> list:
    """
    Validate that tool function uses the params: Dict[str, Any] pattern.
    
    The A4E main application expects tools with signature:
        def tool_name(params: Dict[str, Any]) -> Dict[str, Any]
    """
    errors = []
    func_name = func_node.name
    
    # Get function arguments (excluding self)
    args = [arg for arg in func_node.args.args if arg.arg != "self"]
    
    # Check if using params: Dict pattern
    if len(args) == 1 and args[0].arg == "params":
        # Good - using params dict pattern
        return errors
    
    # Check if using multiple parameters (legacy pattern)
    if len(args) > 1:
        errors.append(
            f"Tool '{func_name}' in {filename} uses individual parameters. "
            f"A4E requires params: Dict[str, Any] pattern. "
            f"Fix: Change signature to 'def {func_name}(params: Dict[str, Any]) -> Dict[str, Any]'"
        )
    elif len(args) == 1 and args[0].arg != "params":
        errors.append(
            f"Tool '{func_name}' in {filename} has single param named '{args[0].arg}'. "
            f"A4E expects the param to be named 'params'. "
            f"Fix: Rename to 'params: Dict[str, Any]'"
        )
    
    return errors


def _check_exec_compatibility(content: str, filename: str) -> list:
    """
    Check if support file has exec() context compatibility.
    
    Support files (db.py, models.py, etc.) need:
    1. __name__ definition for exec() context
    2. sys.path manipulation for imports
    """
    warnings = []
    
    # Check for __name__ compatibility
    if "if '__name__' not in" not in content and "if \"__name__\" not in" not in content:
        warnings.append(
            f"{filename} may not work in exec() context. "
            f"Add at top: if '__name__' not in dir(): __name__ = \"{filename.replace('.py', '')}\""
        )
    
    # Check for if __name__ == "__main__" pattern
    if 'if __name__ == "__main__"' in content or "if __name__ == '__main__'" in content:
        # Make sure it's using globals().get pattern
        if "globals().get('__name__')" not in content:
            warnings.append(
                f"{filename} uses 'if __name__ == \"__main__\"' which may fail in exec() context. "
                f"Change to: if globals().get('__name__') == '__main__'"
            )
    
    return warnings


def _validate_tools_schema_format(schema_file) -> list:
    """
    Validate that tools/schemas.json is in dictionary format.
    
    The A4E main application expects:
    {
        "tool_name": {
            "function": {...},
            "returns": {...}
        }
    }
    
    NOT an array format:
    [{"name": "tool_name", ...}]
    """
    errors = []
    
    try:
        with open(schema_file) as f:
            schemas = json.load(f)
        
        if isinstance(schemas, list):
            errors.append(
                "tools/schemas.json is in array format but A4E expects dictionary format. "
                "Run 'generate_schemas(force=True)' to regenerate in correct format."
            )
        elif isinstance(schemas, dict):
            # Check each tool has the correct structure
            for tool_name, tool_schema in schemas.items():
                if "function" not in tool_schema:
                    errors.append(
                        f"Tool '{tool_name}' schema missing 'function' key. "
                        "Expected format: {\"function\": {...}, \"returns\": {...}}"
                    )
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in tools/schemas.json: {e}")
    except Exception as e:
        errors.append(f"Error reading tools/schemas.json: {e}")
    
    return errors


def _check_agent_prompt(prompt_file) -> list:
    """
    Check agent prompt for recommended patterns.
    """
    warnings = []
    
    try:
        content = prompt_file.read_text()
        
        # Check for language policy
        language_patterns = [
            "english only",
            "respond in english",
            "language policy",
            "always respond in english",
        ]
        has_language_policy = any(
            pattern in content.lower() for pattern in language_patterns
        )
        
        if not has_language_policy:
            warnings.append(
                "Agent prompt (prompts/agent.md) doesn't specify language policy. "
                "Consider adding: '## Language Policy\\n**ALWAYS respond in English only.**'"
            )
        
    except Exception:
        pass
    
    return warnings


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
        else:
            # Check SKILL.md content for correct tool calling pattern
            try:
                skill_content = skill_md.read_text()
                if "render_view(" in skill_content:
                    warnings.append(
                        f"Skill '{skill_id}' SKILL.md references non-existent 'render_view()' function. "
                        "Update to use actual tool names with params dict pattern."
                    )
            except Exception:
                pass
        
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
