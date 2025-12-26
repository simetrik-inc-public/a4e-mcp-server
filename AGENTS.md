# AGENTS.md

> **⚠️ IMPORTANT:** Keep this file updated with every structural change to the project. When adding new tools, folders, or modifying the architecture, update this document accordingly. This ensures AI coding agents can work effectively with the codebase.

## Project Overview

A4E MCP Server is a Model Context Protocol (MCP) server toolkit for building, managing, and running AI agents compatible with the A4E ecosystem. It provides tools for agent creation, view management, schema generation, validation, and deployment.

## Setup Commands

- Install dependencies: `uv sync`
- Run MCP server: `uv run a4e`
- Run with project directory: `uv run a4e --project-dir /path/to/project`
- Test imports: `python -c "from a4e.server import main; print('OK')"`

## Project Structure

```
a4e/
├── core.py                 # MCP instance, shared utilities (get_project_dir, sanitize_input)
├── server.py               # Entry point, imports and registers all tools
├── dev_runner.py           # Development server runner
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
│   ├── agent_tools/        # add_tool, list_tools
│   ├── views/              # add_view, list_views, helpers
│   ├── skills/             # add_skill, list_skills, helpers
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
