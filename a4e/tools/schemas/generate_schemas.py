"""
Schema generation tool.
"""

from pathlib import Path
from typing import Optional
import json
import inspect
import re
import sys
import importlib.util
from types import ModuleType

from ...core import mcp, get_project_dir


@mcp.tool()
def generate_schemas(force: bool = False, agent_name: Optional[str] = None) -> dict:
    """
    Auto-generate all schemas from code

    Args:
        force: If True, overwrite existing schema files. If False, skip generation if schemas exist.
        agent_name: Optional agent ID if not in agent directory

    Generates:
    - tools/schemas.json (from @tool functions)
    - views/*/view.schema.json (from TypeScript props)
    - views/schemas.json (aggregated summary for backend)
    """
    # Import schema_generator dynamically from utils directory
    schema_gen_path = Path(__file__).parent.parent.parent / "utils" / "schema_generator.py"
    spec = importlib.util.spec_from_file_location("schema_generator", schema_gen_path)
    if not spec or not spec.loader:
        return {"success": False, "error": "Failed to load schema_generator module"}
    schema_gen_module = importlib.util.module_from_spec(spec)
    # Add module to sys.modules before executing to enable imports
    sys.modules[spec.name] = schema_gen_module
    spec.loader.exec_module(schema_gen_module)
    generate_schema = schema_gen_module.generate_schema

    project_dir = get_project_dir(agent_name)
    tools_dir = project_dir / "tools"
    views_dir = project_dir / "views"

    results = {
        "tools": {"count": 0, "status": "skipped", "errors": []},
        "views": {"count": 0, "status": "skipped", "errors": []},
    }

    # Check for existing schemas if force is False
    tools_schema_file = tools_dir / "schemas.json" if tools_dir.exists() else None
    views_schema_file = views_dir / "schemas.json" if views_dir.exists() else None

    if not force:
        # Check if tool schemas exist
        if tools_schema_file and tools_schema_file.exists():
            print(
                f"Skipping tool schema generation - {tools_schema_file} exists (use force=True to overwrite)"
            )
            results["tools"]["status"] = "skipped"

        # Check if view schemas exist
        if views_schema_file and views_schema_file.exists():
            print(
                f"Skipping view schema generation - {views_schema_file} exists (use force=True to overwrite)"
            )
            results["views"]["status"] = "skipped"

        # If both are skipped, return early
        if (
            tools_schema_file
            and tools_schema_file.exists()
            and views_schema_file
            and views_schema_file.exists()
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
        if "a4e.sdk" not in sys.modules:
            # a4e module might already exist (we're running from within it)
            # but a4e.sdk might not be available
            if "a4e" not in sys.modules:
                a4e_module = ModuleType("a4e")
                sys.modules["a4e"] = a4e_module
            else:
                a4e_module = sys.modules["a4e"]

            a4e_sdk_module = ModuleType("a4e.sdk")

            def mock_tool(func):
                func._is_tool = True
                return func

            a4e_sdk_module.tool = mock_tool
            a4e_module.sdk = a4e_sdk_module
            sys.modules["a4e.sdk"] = a4e_sdk_module

        for tool_file in tools_dir.glob("*.py"):
            if tool_file.name == "__init__.py":
                continue

            try:
                # Dynamic import
                spec = importlib.util.spec_from_file_location(tool_file.stem, tool_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    # Add module to sys.modules before executing to enable imports
                    sys.modules[spec.name] = module
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
            schema_file.write_text(json.dumps(tool_schemas, indent=2), encoding='utf-8')
            results["tools"]["status"] = "error" if has_errors else "success"
        except Exception as e:
            error_msg = f"Error writing schemas.json: {e}"
            print(error_msg)
            results["tools"]["errors"].append(error_msg)
            results["tools"]["status"] = "error"

    # Generate View Schemas
    if views_dir.exists() and (
        force or not (views_schema_file and views_schema_file.exists())
    ):
        has_errors = False
        aggregated_views = {}

        for view_dir in views_dir.iterdir():
            if not view_dir.is_dir():
                continue

            view_file = view_dir / "view.tsx"
            if not view_file.exists():
                continue

            try:
                content = view_file.read_text(encoding='utf-8')

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
                    "name": view_dir.name,
                    "description": f"View for {view_dir.name}",
                    "props": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                }

                # Write individual schema
                view_schema_file = view_dir / "view.schema.json"
                if view_schema_file.exists() and force:
                    print(f"Overwriting {view_schema_file}")
                view_schema_file.write_text(json.dumps(schema, indent=2), encoding='utf-8')

                # Add to aggregated dict
                # Backend expects: { "view_id": { "id": "...", "description": "...", "params": {...} } }
                aggregated_views[view_dir.name] = {
                    "id": view_dir.name,
                    "description": f"View for {view_dir.name}",
                    "params": properties,
                }

                results["views"]["count"] += 1

            except Exception as e:
                error_msg = f"Error processing view {view_dir}: {e}"
                print(error_msg)
                results["views"]["errors"].append(error_msg)
                has_errors = True

        # Write aggregated schemas.json
        try:
            aggregated_schema_file = views_dir / "schemas.json"
            if aggregated_schema_file.exists() and force:
                print(f"Overwriting {aggregated_schema_file}")
            aggregated_schema_file.write_text(json.dumps(aggregated_views, indent=2), encoding='utf-8')
        except Exception as e:
            error_msg = f"Error writing views/schemas.json: {e}"
            print(error_msg)
            results["views"]["errors"].append(error_msg)
            has_errors = True

        results["views"]["status"] = "error" if has_errors else "success"

    return results

