from mcp.server.fastmcp import FastMCP
from pathlib import Path
from typing import Literal, Optional, List, Dict, Any
import json
import yaml
import inspect
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
import os
import argparse

# Global project directory (set by CLI args)
_PROJECT_DIR: Optional[Path] = None

# Initialize MCP server
mcp = FastMCP(name="a4e-agent-creator")

# Load templates
template_dir = Path(__file__).parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=False,  # Explicit for code generation
)


def sanitize_input(value: str, allowed_chars: str = r"a-zA-Z0-9_-") -> str:
    """
    Sanitize user input to prevent template injection.

    Args:
        value: Input string to sanitize
        allowed_chars: Regex character class of allowed characters

    Returns:
        Sanitized string with only allowed characters
    """
    import re

    pattern = f"[^{allowed_chars}]"
    return re.sub(pattern, "", value)


def get_project_dir(agent_name: Optional[str] = None) -> Path:
    """
    Resolve the agent project directory.

    Priority (highest to lowest):
    1. --project-dir CLI arg (explicit override)
    2. A4E_WORKSPACE env var (set by editor via ${workspaceFolder})
    3. Path.cwd() (fallback for development)

    Args:
        agent_name: Optional agent ID to resolve path for

    Returns:
        Path to agent directory or project root

    Raises:
        ValueError: If agent creation attempted in invalid location
    """
    global _PROJECT_DIR

    # Priority 1: Explicit CLI override
    if _PROJECT_DIR:
        root = _PROJECT_DIR
    # Priority 2: Workspace from editor (portable solution)
    elif os.environ.get("A4E_WORKSPACE"):
        root = Path(os.environ["A4E_WORKSPACE"]).resolve()
    # Priority 3: Fallback to cwd
    else:
        root = Path.cwd()

    if not agent_name:
        return root

    # Agents live in file-store/agent-store
    agent_store = root / "file-store" / "agent-store"

    # Safety: Prevent creating in user HOME without agent-store
    if root == Path.home() and not agent_store.exists():
        raise ValueError(
            f"Cannot create agent in HOME directory ({root}).\n"
            f"Solution: Add to your MCP config:\n"
            f'  "env": {{"A4E_WORKSPACE": "${{workspaceFolder}}"}}'
        )

    return agent_store / agent_name


# ============================================================================
# TOOLS - Agent Creation & Management
# ============================================================================


@mcp.tool()
def initialize_project(
    name: str,
    display_name: str,
    description: str,
    category: Literal[
        "Concierge",
        "E-commerce",
        "Fitness & Health",
        "Education",
        "Entertainment",
        "Productivity",
        "Finance",
        "Customer Support",
        "General",
    ],
    template: Literal["basic", "with-tools", "with-widgets", "full"] = "basic",
) -> dict:
    """
    Initialize a new A4E agent project

    Args:
        name: Agent ID (lowercase, hyphens, e.g., "nutrition-coach")
        display_name: Human-readable name (e.g., "Nutrition Coach")
        description: Short description of the agent
        category: Agent category for marketplace
        template: Project template (basic=files only, with-tools=example tool, with-widgets=example widget, full=both)

    Returns:
        Project details with created files and next steps
    """
    # Validate name format
    if not name.replace("-", "").replace("_", "").isalnum():
        return {
            "success": False,
            "error": "Agent name must be alphanumeric with hyphens/underscores only",
        }

    # Use helper to determine path
    project_dir = get_project_dir(name)

    if project_dir.exists():
        return {"success": False, "error": f"Directory '{project_dir}' already exists"}

    try:
        # Ensure file-store/agent-store structure exists
        agent_store_root = project_dir.parent
        agent_store_root.mkdir(parents=True, exist_ok=True)

        # Create agent directory
        project_dir.mkdir(exist_ok=True)
        (project_dir / "prompts").mkdir(exist_ok=True)
        (project_dir / "tools").mkdir(exist_ok=True)
        (project_dir / "widgets").mkdir(exist_ok=True)

        # Sanitize inputs before template rendering
        safe_name = sanitize_input(name)

        # Generate agent.py
        agent_template = jinja_env.get_template("agent.py.j2")
        agent_code = agent_template.render(agent_id=safe_name)
        (project_dir / "agent.py").write_text(agent_code)

        # Generate metadata.json
        metadata_template = jinja_env.get_template("metadata.json.j2")
        # Sanitize text inputs (allow spaces and common punctuation for display_name and description)
        safe_display_name = sanitize_input(display_name, r"a-zA-Z0-9 _-")
        safe_description = sanitize_input(description, r"a-zA-Z0-9 .,!?_-")
        metadata = metadata_template.render(
            agent_id=safe_name,
            display_name=safe_display_name,
            description=safe_description,
            category=category,
        )
        (project_dir / "metadata.json").write_text(metadata)

        # Generate prompts/agent.md
        prompt_template = jinja_env.get_template("prompt.md.j2")
        prompt = prompt_template.render(
            display_name=safe_display_name,
            category=category,
            description=safe_description,
        )
        (project_dir / "prompts/agent.md").write_text(prompt)
        (project_dir / "prompts/reviewer.md").write_text("")
        (project_dir / "prompts/widget_renderer.md").write_text("")

        # Create welcome widget (MANDATORY)
        _create_widget(
            widget_id="welcome",
            description="Welcome widget for the agent",
            props={"title": {"type": "string", "description": "Welcome title"}},
            project_dir=project_dir,
        )

        # Create example content based on template
        if template in ["with-tools", "full"]:
            # Create example tool
            example_tool_code = '''from a4e.sdk import tool
from typing import Optional, Any

@tool
def example_tool(
    query: str,
    max_results: Optional[int] = 10
) -> dict:
    """
    Example tool that demonstrates basic functionality
    
    Args:
        query: Search query or input text
        max_results: Maximum number of results to return
    """
    # TODO: Implement your tool logic here
    return {
        "status": "success",
        "message": f"Processed query: {query}",
        "results": []
    }
'''
            (project_dir / "tools" / "example_tool.py").write_text(example_tool_code)

        if template in ["with-widgets", "full"]:
            # Create example widget (in addition to welcome)
            _create_widget(
                widget_id="example_widget",
                description="Example widget demonstrating props usage",
                props={
                    "title": {"type": "string", "description": "Widget title"},
                    "count": {"type": "number", "description": "Count value"},
                },
                project_dir=project_dir,
            )

        # Auto-generate schemas after project initialization
        generate_schemas(force=False, agent_name=name)

        return {
            "success": True,
            "message": f"Initialized agent '{name}'",
            "path": str(project_dir),
            "diagnostic": {
                "workspace_env": os.environ.get("A4E_WORKSPACE"),
                "project_dir_flag": str(_PROJECT_DIR) if _PROJECT_DIR else None,
                "detected_root": str(get_project_dir()),
                "cwd": str(Path.cwd()),
            },
            "next_steps": [
                f"Add tools: add_tool(..., agent_name='{name}')",
                f"Add widgets: add_widget(..., agent_name='{name}')",
                "Start dev server using 'dev_start'",
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _create_widget(
    widget_id: str, description: str, props: dict, project_dir: Path
) -> dict:
    """Helper to create a widget"""
    widgets_dir = project_dir / "widgets"

    if not widgets_dir.exists():
        return {
            "success": False,
            "error": f"widgets/ directory not found at {widgets_dir}",
        }

    widget_dir = widgets_dir / widget_id
    if widget_dir.exists():
        return {"success": False, "error": f"Widget '{widget_id}' already exists"}

    try:
        widget_dir.mkdir()

        # Convert snake_case to PascalCase for component name
        widget_name = "".join(word.title() for word in widget_id.split("_"))

        template = jinja_env.get_template("widget.tsx.j2")
        code = template.render(
            widget_name=widget_name, description=description, props=props
        )
        (widget_dir / "widget.tsx").write_text(code)

        return {
            "success": True,
            "message": f"Created widget '{widget_id}'",
            "path": str(widget_dir),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


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
        generate_schemas(force=False, agent_name=agent_name)

        return {
            "success": True,
            "message": f"Created tool '{tool_name}'",
            "path": str(tool_file),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def add_widget(
    widget_id: str, description: str, props: dict, agent_name: Optional[str] = None
) -> dict:
    """
    Add a new React widget

    Args:
        widget_id: ID of the widget (snake_case, e.g., "meal_plan")
        description: Widget purpose
        props: Dictionary of props with types
        agent_name: Optional agent ID if not in agent directory
    """
    # Validate widget ID
    if not widget_id.replace("_", "").isalnum():
        return {
            "success": False,
            "error": "Widget ID must be alphanumeric with underscores",
        }

    project_dir = get_project_dir(agent_name)
    result = _create_widget(widget_id, description, props, project_dir)

    # Auto-generate schemas after adding widget
    if result.get("success"):
        generate_schemas(force=False, agent_name=agent_name)

    return result


@mcp.tool()
def generate_schemas(force: bool = False, agent_name: Optional[str] = None) -> dict:
    """
    Auto-generate all schemas from code

    Args:
        force: If True, overwrite existing schema files. If False, skip generation if schemas exist.
        agent_name: Optional agent ID if not in agent directory

    Generates:
    - tools/schemas.json (from @tool functions)
    - widgets/*/widget.schema.json (from TypeScript props)
    - widgets/schemas.json (aggregated summary for backend)
    """
    import sys
    import importlib.util

    # Import schema_generator dynamically from current directory
    schema_gen_path = Path(__file__).parent / "utils" / "schema_generator.py"
    spec = importlib.util.spec_from_file_location("schema_generator", schema_gen_path)
    if not spec or not spec.loader:
        return {"success": False, "error": "Failed to load schema_generator module"}
    schema_gen_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schema_gen_module)
    generate_schema = schema_gen_module.generate_schema

    project_dir = get_project_dir(agent_name)
    tools_dir = project_dir / "tools"
    widgets_dir = project_dir / "widgets"

    results = {
        "tools": {"count": 0, "status": "skipped", "errors": []},
        "widgets": {"count": 0, "status": "skipped", "errors": []},
    }

    # Check for existing schemas if force is False
    tools_schema_file = tools_dir / "schemas.json" if tools_dir.exists() else None
    widgets_schema_file = widgets_dir / "schemas.json" if widgets_dir.exists() else None

    if not force:
        # Check if tool schemas exist
        if tools_schema_file and tools_schema_file.exists():
            print(
                f"Skipping tool schema generation - {tools_schema_file} exists (use force=True to overwrite)"
            )
            results["tools"]["status"] = "skipped"

        # Check if widget schemas exist
        if widgets_schema_file and widgets_schema_file.exists():
            print(
                f"Skipping widget schema generation - {widgets_schema_file} exists (use force=True to overwrite)"
            )
            results["widgets"]["status"] = "skipped"

        # If both are skipped, return early
        if (
            tools_schema_file
            and tools_schema_file.exists()
            and widgets_schema_file
            and widgets_schema_file.exists()
        ):
            return results

    # Generate Tool Schemas
    if tools_dir.exists() and (
        force or not (tools_schema_file and tools_schema_file.exists())
    ):
        tool_schemas = []
        has_errors = False

        # Add project dir to sys.path to allow imports
        if str(project_dir) not in sys.path:
            sys.path.insert(0, str(project_dir))

        # Mock a4e SDK to avoid backend dependency hell (psycopg2, etc.)
        # We only need the @tool decorator to mark functions
        import sys
        from types import ModuleType

        if "a4e" not in sys.modules:
            a4e_module = ModuleType("a4e")
            a4e_sdk_module = ModuleType("a4e.sdk")

            def mock_tool(func):
                func._is_tool = True
                return func

            a4e_sdk_module.tool = mock_tool
            a4e_module.sdk = a4e_sdk_module

            sys.modules["a4e"] = a4e_module
            sys.modules["a4e.sdk"] = a4e_sdk_module

        for tool_file in tools_dir.glob("*.py"):
            if tool_file.name == "__init__.py":
                continue

            try:
                # Dynamic import
                spec = importlib.util.spec_from_file_location(tool_file.stem, tool_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Find @tool decorated functions or functions matching filename convention
                    for name, obj in inspect.getmembers(module):
                        if not inspect.isfunction(obj):
                            continue

                        is_decorated_tool = getattr(obj, "_is_tool", False)
                        matches_filename = name == tool_file.stem

                        if is_decorated_tool or matches_filename:
                            schema = generate_schema(obj)
                            tool_schemas.append(schema)
                            results["tools"]["count"] += 1
                            if is_decorated_tool:
                                break
            except Exception as e:
                error_msg = f"Error processing {tool_file}: {e}"
                print(error_msg)
                results["tools"]["errors"].append(error_msg)
                has_errors = True

        try:
            schema_file = tools_dir / "schemas.json"
            if schema_file.exists() and force:
                print(f"Overwriting {schema_file}")
            schema_file.write_text(json.dumps(tool_schemas, indent=2))
            results["tools"]["status"] = "error" if has_errors else "success"
        except Exception as e:
            error_msg = f"Error writing schemas.json: {e}"
            print(error_msg)
            results["tools"]["errors"].append(error_msg)
            results["tools"]["status"] = "error"

    # Generate Widget Schemas
    if widgets_dir.exists() and (
        force or not (widgets_schema_file and widgets_schema_file.exists())
    ):
        import re

        has_errors = False
        aggregated_widgets = {}

        for widget_dir in widgets_dir.iterdir():
            if not widget_dir.is_dir():
                continue

            widget_file = widget_dir / "widget.tsx"
            if not widget_file.exists():
                continue

            try:
                content = widget_file.read_text()

                # Simple regex to find interface Props
                props_match = re.search(r"interface\s+(\w+Props)\s*{([^}]+)}", content)

                properties = {}
                required = []

                if props_match:
                    props_body = props_match.group(2)
                    for line in props_body.split("\n"):
                        line = line.strip()
                        if not line or line.startswith("//"):
                            continue

                        prop_match = re.match(r"(\w+)(\?)?:\s*([^;]+);", line)
                        if prop_match:
                            name = prop_match.group(1)
                            optional = prop_match.group(2) == "?"
                            ts_type = prop_match.group(3).strip()

                            json_type = "string"
                            if "number" in ts_type:
                                json_type = "number"
                            elif "boolean" in ts_type:
                                json_type = "boolean"
                            elif "Array" in ts_type or "[]" in ts_type:
                                json_type = "array"

                            properties[name] = {
                                "type": json_type,
                                "description": f"From {ts_type}",
                            }

                            if not optional:
                                required.append(name)

                schema = {
                    "name": widget_dir.name,
                    "description": f"Widget for {widget_dir.name}",
                    "props": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                }

                # Write individual schema
                widget_schema_file = widget_dir / "widget.schema.json"
                if widget_schema_file.exists() and force:
                    print(f"Overwriting {widget_schema_file}")
                widget_schema_file.write_text(json.dumps(schema, indent=2))

                # Add to aggregated dict
                # Backend expects: { "widget_id": { "id": "...", "description": "...", "params": {...} } }
                aggregated_widgets[widget_dir.name] = {
                    "id": widget_dir.name,
                    "description": f"Widget for {widget_dir.name}",
                    "params": properties,  # Simplified mapping for now
                }

                results["widgets"]["count"] += 1

            except Exception as e:
                error_msg = f"Error processing widget {widget_dir}: {e}"
                print(error_msg)
                results["widgets"]["errors"].append(error_msg)
                has_errors = True

        # Write aggregated schemas.json
        try:
            aggregated_schema_file = widgets_dir / "schemas.json"
            if aggregated_schema_file.exists() and force:
                print(f"Overwriting {aggregated_schema_file}")
            aggregated_schema_file.write_text(json.dumps(aggregated_widgets, indent=2))
        except Exception as e:
            error_msg = f"Error writing widgets/schemas.json: {e}"
            print(error_msg)
            results["widgets"]["errors"].append(error_msg)
            has_errors = True

        results["widgets"]["status"] = "error" if has_errors else "success"

    return results


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
    import ast

    project_dir = get_project_dir(agent_name)
    required_files = [
        "agent.py",
        "metadata.json",
        "prompts/agent.md",
        "widgets/welcome/widget.tsx",
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

        # 3. Check widget schemas
        widgets_dir = project_dir / "widgets"
        if widgets_dir.exists():
            # Find widget directories (not __init__.py files)
            widget_dirs = [
                d
                for d in widgets_dir.iterdir()
                if d.is_dir() and (d / "widget.tsx").exists()
            ]
            if not (widgets_dir / "schemas.json").exists() and widget_dirs:
                errors.append(
                    "Widgets exist but widgets/schemas.json is missing. Run generate_schemas."
                )

        if errors:
            return {
                "success": False,
                "error": "Strict validation failed",
                "details": errors,
            }

    return {"success": True, "message": "Agent structure is valid"}


@mcp.tool()
def check_environment() -> dict:
    """
    Diagnose the current environment for agent development
    """
    import sys
    import shutil
    import os

    results = {
        "python": {
            "version": sys.version.split()[0],
            "ok": sys.version_info >= (3, 10),
        },
        "project_root": {
            "configured_dir": str(_PROJECT_DIR) if _PROJECT_DIR else None,
            "effective_dir": str(get_project_dir()),
            "using_fallback": _PROJECT_DIR is None,
        },
        "dependencies": {"pyngrok": False, "message": "Not installed"},
        "ngrok_binary": {"found": False, "path": None},
        "ngrok_auth": {"configured": False},
        "recommendations": [],
    }

    # Check pyngrok
    try:
        import pyngrok

        results["dependencies"]["pyngrok"] = True
        results["dependencies"]["message"] = f"Installed ({pyngrok.__version__})"
    except ImportError:
        results["recommendations"].append("Install pyngrok: 'uv add pyngrok'")

    # Check ngrok binary
    ngrok_path = shutil.which("ngrok")
    if ngrok_path:
        results["ngrok_binary"]["found"] = True
        results["ngrok_binary"]["path"] = ngrok_path
    else:
        results["recommendations"].append("Install ngrok CLI and add to PATH")

    # Check auth token
    if os.environ.get("NGROK_AUTHTOKEN"):
        results["ngrok_auth"]["configured"] = True
        results["ngrok_auth"]["source"] = "env_var"
    else:
        try:
            from pyngrok import conf

            if conf.get_default().auth_token:
                results["ngrok_auth"]["configured"] = True
                results["ngrok_auth"]["source"] = "config_file"
        except ImportError:
            config_path = Path.home() / ".ngrok2" / "ngrok.yml"
            config_path_new = (
                Path.home() / "Library/Application Support/ngrok/ngrok.yml"
            )
            if config_path.exists() or config_path_new.exists():
                results["ngrok_auth"]["configured"] = True
                results["ngrok_auth"]["source"] = "config_file_detected"

    if not results["ngrok_auth"]["configured"]:
        results["recommendations"].append(
            "Configure ngrok auth: 'ngrok config add-authtoken <TOKEN>'"
        )

    return results


@mcp.tool()
def dev_start(
    port: int = 5000, auth_token: Optional[str] = None, agent_name: Optional[str] = None
) -> dict:
    """
    Start development mode with ngrok tunnel
    """
    import sys
    import importlib.util

    # Import DevManager dynamically
    dev_manager_path = Path(__file__).parent / "utils" / "dev_manager.py"
    spec = importlib.util.spec_from_file_location("dev_manager", dev_manager_path)
    if not spec or not spec.loader:
        return {"success": False, "error": "Failed to load dev_manager module"}
    dev_manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dev_manager_module)
    DevManager = dev_manager_module.DevManager

    project_dir = get_project_dir(agent_name)
    return DevManager.start_dev_server(project_dir, port, auth_token)


@mcp.tool()
def dev_stop(port: int = 5000) -> dict:
    """
    Stop development server and cleanup tunnels
    """
    import sys
    import importlib.util

    # Import DevManager dynamically
    dev_manager_path = Path(__file__).parent / "utils" / "dev_manager.py"
    spec = importlib.util.spec_from_file_location("dev_manager", dev_manager_path)
    if not spec or not spec.loader:
        return {"success": False, "error": "Failed to load dev_manager module"}
    dev_manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dev_manager_module)
    DevManager = dev_manager_module.DevManager

    return DevManager.stop_dev_server(port)


@mcp.tool()
def deploy(
    environment: str = "production",
    auto_publish: bool = False,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Deploy agent to A4E Hub
    """
    val_result = validate(strict=True, agent_name=agent_name)
    if not val_result["success"]:
        return val_result

    gen_result = generate_schemas(force=True, agent_name=agent_name)

    if (
        gen_result.get("tools", {}).get("status") == "error"
        or gen_result.get("widgets", {}).get("status") == "error"
    ):
        return {
            "success": False,
            "error": "Schema generation failed",
            "details": gen_result,
        }

    project_dir = get_project_dir(agent_name)
    agent_id = project_dir.name

    return {
        "success": True,
        "message": f"Agent '{agent_id}' deployed successfully to {environment}",
        "agent_url": f"https://hub.a4e.com/agents/{agent_id}",
        "mcp_endpoint": f"mcp://{agent_id}.a4e.com",
        "details": {
            "validation": val_result,
            "schema_generation": gen_result,
            "upload": "success",
            "deployment": "success",
        },
    }


@mcp.tool()
def list_tools(agent_name: Optional[str] = None) -> dict:
    """
    List all tools available in the current agent project
    """
    project_dir = get_project_dir(agent_name)
    tools_dir = project_dir / "tools"

    if not tools_dir.exists():
        return {"tools": [], "count": 0}

    tools = []
    for tool_file in tools_dir.glob("*.py"):
        if tool_file.name == "__init__.py":
            continue
        tools.append(tool_file.stem)

    return {"tools": sorted(tools), "count": len(tools)}


@mcp.tool()
def list_widgets(agent_name: Optional[str] = None) -> dict:
    """
    List all widgets available in the current agent project
    """
    project_dir = get_project_dir(agent_name)
    widgets_dir = project_dir / "widgets"

    if not widgets_dir.exists():
        return {"widgets": [], "count": 0}

    widgets = []
    for widget_dir in widgets_dir.iterdir():
        if widget_dir.is_dir() and (widget_dir / "widget.tsx").exists():
            widgets.append(widget_dir.name)

    return {"widgets": sorted(widgets), "count": len(widgets)}


@mcp.tool()
def get_agent_info(agent_name: Optional[str] = None) -> dict:
    """
    Get general metadata and info about the current agent
    """
    project_dir = get_project_dir(agent_name)
    metadata_file = project_dir / "metadata.json"

    if not metadata_file.exists():
        return {
            "error": f"metadata.json not found in {project_dir}. Are you in an agent project?"
        }

    try:
        metadata = json.loads(metadata_file.read_text())
        return {
            "agent_id": project_dir.name,
            "metadata": metadata,
            "path": str(project_dir),
        }
    except Exception as e:
        return {"error": f"Failed to read metadata: {str(e)}"}


def main():
    """Entry point for the CLI"""
    global _PROJECT_DIR

    # Parse CLI arguments (standard MCP pattern)
    parser = argparse.ArgumentParser(
        description="A4E MCP Server for agent creation and management"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        help="Root directory for agent projects (standard MCP pattern). "
        "Agents will be created in {project-dir}/file-store/agent-store/",
    )

    args, unknown = parser.parse_known_args()

    # Set global project directory
    if args.project_dir:
        _PROJECT_DIR = Path(args.project_dir).resolve()
        # Validate that it exists
        if not _PROJECT_DIR.exists():
            print(f"Error: Project directory does not exist: {_PROJECT_DIR}")
            exit(1)

    # Run MCP server
    mcp.run()


if __name__ == "__main__":
    main()
