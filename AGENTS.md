# AGENTS.md

> **⚠️ IMPORTANT:** Keep this file updated with every structural change to the project. When adding new tools, folders, or modifying the architecture, update this document accordingly. This ensures AI coding agents can work effectively with the codebase.

## Project Overview

A4E MCP Server is a Model Context Protocol (MCP) server toolkit for building, managing, and running AI agents compatible with the A4E ecosystem. It provides tools for agent creation, view management, schema generation, validation, and deployment.

## Setup Commands

- Install dependencies: `uv sync`
- Run MCP server: `uv run a4e`
- Run with project directory: `uv run a4e --project-dir /path/to/project`
- Test imports: `python -c "from a4e.server import main; print('OK')"`

## CLI Commands

The A4E CLI provides a full command-line interface for agent management:

| Command | Description |
|---------|-------------|
| `a4e init` | Initialize a new agent project (interactive wizard) |
| `a4e add tool` | Add a tool to the agent |
| `a4e add view` | Add a view to the agent |
| `a4e add skill` | Add a skill to the agent |
| `a4e list [tools\|views\|skills\|all]` | List agent components |
| `a4e remove [tool\|view\|skill]` | Remove a component |
| `a4e validate` | Validate agent project |
| `a4e deploy` | Deploy to production |
| `a4e info` | Display agent information |
| `a4e dev start` | Start development server |

See [CLI.md](CLI.md) for full command reference.

## Documentation

- [Getting Started](docs/GETTING_STARTED.md) - Quick start tutorial
- [CLI Reference](CLI.md) - Full CLI documentation
- [Examples](docs/EXAMPLES.md) - Example agent implementations
- [View System](docs/VIEW_SYSTEM.md) - How views work in production (#VIEW tags)

## A4E Main Application Compatibility

> **⚠️ CRITICAL:** Tools and schemas must follow specific patterns to work with the A4E main application.

### Tool Signature Pattern

All tools MUST use the `params: Dict[str, Any]` pattern:

```python
from typing import Dict, Any

def my_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool description

    Args:
        params: Dictionary containing:
            - param1: Description (required)
            - param2: Description (optional)
    """
    param1 = params.get("param1")
    param2 = params.get("param2")
    
    return {"status": "success", "result": ...}
```

**Why?** The A4E backend wraps tools with `_wrap_tool_with_context()` which merges user context into the params dict.

### Schema Format

`tools/schemas.json` MUST be a dictionary (not an array):

```json
{
  "tool_name": {
    "function": {
      "name": "tool_name",
      "description": "...",
      "parameters": {
        "type": "object",
        "properties": {...},
        "required": [...]
      }
    },
    "returns": {
      "type": "object",
      "properties": {...}
    }
  }
}
```

### Support Files (db.py, models.py)

Support files must include exec() context compatibility:

```python
# At the top of the file
if '__name__' not in dir():
    __name__ = "module_name"

import sys
import os

if '__file__' in dir():
    _dir = os.path.dirname(globals()['__file__'])
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
```

### Agent Prompt Best Practices

Include a language policy in `prompts/agent.md`:

```markdown
## IMPORTANT: Language Policy

**ALWAYS respond in English only.** Even if the user writes in another language, respond in English.
```

## Project Structure

```
a4e/
├── core.py                 # MCP instance, shared utilities (get_project_dir, sanitize_input)
├── server.py               # Entry point, imports and registers all tools
├── cli.py                  # CLI entry point (typer app)
├── dev_runner.py           # Development server runner
├── cli_commands/           # CLI command modules
│   ├── init.py             # a4e init (interactive wizard)
│   ├── add.py              # a4e add [tool|view|skill]
│   ├── list.py             # a4e list [tools|views|skills]
│   ├── remove.py           # a4e remove [tool|view|skill]
│   ├── validate.py         # a4e validate
│   ├── deploy.py           # a4e deploy
│   ├── info.py             # a4e info
│   └── dev.py              # a4e dev start
├── templates/              # Jinja2 templates for code generation
│   ├── agent.md.j2         # Root AGENTS.md template
│   ├── agents.md.j2        # Project AGENTS.md template
│   ├── agent.py.j2
│   ├── metadata.json.j2
│   ├── prompt.md.j2
│   ├── tool.py.j2
│   ├── view.tsx.j2
│   ├── tools/
│   │   └── agent.md.j2     # Tools directory AGENTS.md template
│   ├── views/
│   │   └── agent.md.j2     # Views directory AGENTS.md template
│   ├── prompts/
│   │   └── agent.md.j2     # Prompts directory AGENTS.md template
│   └── skills/
│       ├── agents.md.j2    # Template for skills/AGENTS.md
│       └── skill.md.j2     # Template for skills/{id}/SKILL.md
├── tools/                  # MCP tools organized by section
│   ├── project/            # initialize_project, get_agent_info
│   ├── agent_tools/        # add_tool, list_tools, remove_tool
│   ├── views/              # add_view, list_views, remove_view, helpers
│   ├── skills/             # add_skill, list_skills, remove_skill, helpers
│   ├── schemas/            # generate_schemas
│   ├── validation/         # validate
│   ├── dev/                # dev_start, dev_stop, check_environment
│   └── deploy/             # deploy
└── utils/                  # Utility modules
    ├── dev_manager.py
    └── schema_generator.py
```

## Tools Folder Reference

Each folder inside `a4e/tools/` has a specific purpose. Use this guide when adding new tools:

| Folder         | Purpose                    | When to use                                                               |
| -------------- | -------------------------- | ------------------------------------------------------------------------- |
| `project/`     | Agent project lifecycle    | Tools for initializing, configuring, or getting info about agent projects |
| `agent_tools/` | Tool management for agents | Tools that create, modify, or list tools within an agent project          |
| `views/`       | View/UI management         | Tools for creating, modifying, or listing React views in agents           |
| `skills/`      | Skill orchestration        | Tools for creating skills that connect intents → tools → views            |
| `schemas/`     | Schema generation          | Tools related to JSON schema generation from code                         |
| `validation/`  | Validation & linting       | Tools that validate agent structure, syntax, or conventions               |
| `dev/`         | Development workflow       | Tools for local development: servers, tunnels, environment checks         |
| `deploy/`      | Deployment & publishing    | Tools for deploying agents to production or A4E Hub                       |

### When to create a new folder

Create a new section folder when:

- The tool doesn't fit any existing category
- You're adding 2+ related tools that form a logical group
- The functionality is distinct enough to warrant separation

### Folder structure convention

Each tool folder must have:

```
section_name/
├── __init__.py      # Exports all tools from this section
├── tool_one.py      # One file per tool
├── tool_two.py
└── helpers.py       # Optional: shared helpers for this section only
```

## Code Style

- Python 3.11+ required
- Use type hints for all function parameters and return types
- Use `Optional[T]` for optional parameters, not `T | None`
- Snake_case for functions and variables
- PascalCase for classes
- All code and comments in English
- Keep solutions simple, minimalist, and scalable

## Adding New Tools

When adding a new MCP tool:

1. Create a new folder under `a4e_mcp/tools/<section_name>/`
2. Create the tool file: `<tool_name>.py`
3. Use the `@mcp.tool()` decorator from `...core import mcp`
4. Export in section's `__init__.py`
5. Import in `a4e_mcp/tools/__init__.py`
6. Import in `a4e_mcp/server.py`

Example tool structure:

```python
from typing import Optional
from ...core import mcp, get_project_dir

@mcp.tool()
def my_tool(param: str, optional_param: Optional[int] = None) -> dict:
    """
    Tool description

    Args:
        param: Parameter description
        optional_param: Optional parameter description
    """
    # Implementation
    return {"success": True}
```

## Key Files

- `core.py`: Contains the `mcp` FastMCP instance, `jinja_env` for templates, and helper functions
- `server.py`: Entry point that imports all tools and runs the server
- `tools/__init__.py`: Re-exports all tools from subsections

## Environment Variables

- `A4E_WORKSPACE`: Workspace directory for agent projects (used by editors)
- `NGROK_AUTHTOKEN`: Auth token for ngrok tunnels (optional)

## Agent Project Structure (Created by tools)

When `initialize_project` creates an agent, it generates:

```
{agent-name}/
├── agent.py
├── metadata.json
├── AGENTS.md               # Root project context for AI agents
├── prompts/
│   ├── AGENTS.md           # Prompts development guide
│   ├── agent.md
│   ├── reviewer.md
│   └── view_renderer.md
├── tools/
│   ├── AGENTS.md           # Tools development guide
│   └── schemas.json
├── views/
│   ├── AGENTS.md           # Views development guide
│   ├── welcome/
│   │   └── view.tsx
│   └── schemas.json
└── skills/
    ├── AGENTS.md           # Skills documentation for AI agents
    ├── show_welcome/
    │   └── SKILL.md
    └── schemas.json
```

## Validation

The `validate` tool checks agent integrity before deployment:

| Check              | Type          | Description                                                       |
| ------------------ | ------------- | ----------------------------------------------------------------- |
| Required files     | Error         | agent.py, metadata.json, prompts/agent.md, views/welcome/view.tsx |
| Python syntax      | Error         | All .py files must be valid Python                                |
| Type hints         | Error         | Public functions must have type hints                             |
| Tools schemas      | Error         | tools/schemas.json must exist if tools/ has .py files             |
| Views schemas      | Error         | views/schemas.json must exist if views/ has view folders          |
| Skills schemas     | Error         | skills/schemas.json must exist if skills/ has folders             |
| Skill SKILL.md     | Warning       | Each skill should have SKILL.md documentation                     |
| Skill dependencies | Error/Warning | output.view must exist, internal_tools warned if missing          |
| Duplicate triggers | Warning       | Same intent_trigger in multiple skills                            |
| Orphan skills      | Warning       | Skill folders not in schemas.json                                 |

## Security Considerations

- All user inputs are sanitized via `sanitize_input()` before template rendering
- Template injection is prevented by stripping non-alphanumeric characters
- Agents cannot be created in HOME directory without proper agent-store structure

## Dependencies

- `mcp[cli]`: Model Context Protocol SDK
- `jinja2`: Template engine for code generation
- `pydantic`: Data validation
- `pyngrok`: Ngrok tunnel for dev server
- `watchdog`: File system monitoring
