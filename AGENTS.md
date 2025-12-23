# A4E MCP Server - Agent Instructions

This file provides instructions for AI coding agents (Cursor, VS Code Copilot, OpenAI Codex, Aider, Windsurf, Google Jules, etc.) to work effectively with the A4E MCP Server project.

## Project Overview

The **A4E MCP Server** enables creators to build AI agents using natural language directly in their IDE. It exposes MCP tools that generate agent files (metadata, prompts, tools, views) following the A4E ecosystem standards.

## Repository Structure

```
a4e-mcp-server/
├── a4e_mcp/
│   ├── server.py           # Main MCP server with all tools
│   ├── dev_runner.py       # Local development with ngrok
│   ├── __init__.py
│   ├── templates/          # Jinja2 templates for code generation
│   │   ├── agent.py.j2     # Agent entry point template
│   │   ├── metadata.json.j2# Agent metadata template
│   │   ├── prompt.md.j2    # System prompt template
│   │   ├── tool.py.j2      # Python tool template
│   │   └── view.tsx.j2     # React view template
│   └── utils/
│       ├── schema_generator.py  # JSON schema generation
│       └── dev_manager.py       # Dev server management
├── main.py                 # Entry point
├── pyproject.toml          # Dependencies (Python 3.11+)
└── uv.lock                 # Lock file
```

## Setup Commands

```bash
# Install dependencies
uv sync

# Configure ngrok (required for dev mode)
ngrok config add-authtoken <YOUR_TOKEN>

# Run the server directly
uv run a4e_mcp/server.py
```

## Available MCP Tools

The server exposes these tools for agent creation:

| Tool | Description |
|------|-------------|
| `initialize_project` | Create new agent with metadata, prompts, and welcome view |
| `add_tool` | Add a Python tool to an agent |
| `add_view` | Add a React view/widget to an agent |
| `generate_schemas` | Auto-generate JSON schemas from code |
| `validate` | Validate agent structure and files |
| `check_environment` | Diagnose setup issues |
| `dev_start` | Start local server with ngrok tunnel |
| `dev_stop` | Stop the development server |
| `deploy` | Deploy agent to A4E Hub |
| `list_tools` | List all tools in an agent |
| `list_views` | List all views in an agent |
| `get_agent_info` | Get agent metadata and status |

## Agent Creation Workflow

When a user asks to create an agent:

### Step 1: Initialize Project

Call `initialize_project` with:
- `name`: Agent ID (lowercase, hyphens, e.g., "nutrition-coach")
- `display_name`: Human-readable name
- `description`: Short description
- `category`: One of Concierge, E-commerce, Fitness & Health, Education, Entertainment, Productivity, Finance, Customer Support, General
- `template`: basic, with-tools, with-views, or full

### Step 2: Add Tools

Call `add_tool` with:
- `name`: Tool function name (snake_case)
- `description`: What the tool does
- `parameters`: Dict of parameter definitions

### Step 3: Add Views

Call `add_view` with:
- `name`: View name (PascalCase)
- `description`: What the view displays
- `props`: Dict of prop definitions

### Step 4: Generate Schemas

Call `generate_schemas` to auto-generate JSON schemas from Python functions and React props.

## Generated Agent Structure

```
{agent_id}/
├── metadata.json           # Agent identity and config
├── agent.py                # Entry point (create_agent function)
├── prompts/
│   ├── agent.md            # System prompt
│   ├── reviewer.md         # Response review prompt
│   └── view_renderer.md    # View rendering prompt
├── views/
│   ├── welcome/            # Mandatory welcome view
│   │   └── view.tsx
│   └── {view_name}/
│       └── view.tsx
└── tools/
    └── {tool_name}.py
```

## Code Style Guidelines

### Python (Tools & Server)

- Python 3.11+ required
- Use type hints for all function signatures
- Use `@tool` decorator from `a4e.sdk`
- Docstrings required for all tools (used for schema generation)
- Follow PEP 8 style guide
- Use `Optional[T]` for optional parameters

### TypeScript/React (Views)

- Use `"use client"` directive for client components
- Define props interface for each view
- Destructure props in function signature
- Use Tailwind CSS for styling
- Import `a4e` SDK from `@/lib/sdk`

## Template Syntax

Templates use Jinja2 with these conventions:

- `{{ variable }}` - Variable substitution
- `{{ value|tojson }}` - JSON-safe output
- `{% for item in list %}` - Iteration
- `{% if condition %}` - Conditionals

### Modifying Templates

When updating templates in `a4e_mcp/templates/`:

1. Preserve Jinja2 syntax (`{{ }}`, `{% %}`)
2. Use `|tojson` filter for JSON fields
3. Test with `generate_schemas` after changes
4. Validate output matches expected structure

## Testing

```bash
# Run the server in development
uv run a4e_mcp/server.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run a4e_mcp/server.py
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `A4E_WORKSPACE` | Project root directory (set by IDE) |
| `NGROK_AUTHTOKEN` | ngrok authentication token |

## Error Handling

- Always validate agent name format (alphanumeric + hyphens)
- Check if directory exists before creating
- Use `sanitize_input()` for template variables
- Return `{"success": False, "error": "..."}` on failure

## Best Practices

1. **Always create welcome view** - It's mandatory for all agents
2. **Use descriptive tool names** - snake_case, action-oriented
3. **Include parameter descriptions** - Used for LLM context
4. **Validate before deploy** - Run `validate` tool first
5. **Test incrementally** - Create agent → add tool → test → add view → test

## Common Patterns

### Creating a Complete Agent

```
User: "Create a fitness coach agent with BMI calculator"

1. initialize_project(
     name="fitness-coach",
     display_name="Fitness Coach",
     description="Personal fitness assistant",
     category="Fitness & Health",
     template="full"
   )

2. add_tool(
     name="calculate_bmi",
     description="Calculate Body Mass Index",
     parameters={
       "weight_kg": {"type": "float", "description": "Weight in kg"},
       "height_cm": {"type": "float", "description": "Height in cm"}
     }
   )

3. add_view(
     name="BMIResult",
     description="Display BMI calculation result",
     props={
       "bmi": {"type": "number", "description": "Calculated BMI"},
       "category": {"type": "string", "description": "BMI category"}
     }
   )

4. generate_schemas()
```

### Development Workflow

```
1. dev_start(port=5000) - Start local server
2. Test agent in A4E Hub (via ngrok URL)
3. Make changes to prompts/tools/views
4. generate_schemas() - Update schemas
5. validate() - Check for errors
6. dev_stop() - Stop server
7. deploy() - Push to production
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "pyngrok not installed" | Run `uv sync` in project directory |
| "ngrok command not found" | Install via `brew install ngrok` or `choco install ngrok` |
| "Cannot create in HOME" | Set `A4E_WORKSPACE` env var in MCP config |
| "Directory already exists" | Choose different agent name or delete existing |
| "Invalid agent name" | Use only lowercase letters, numbers, and hyphens |

## IDE Configuration

### Cursor

```json
{
  "mcpServers": {
    "a4e": {
      "command": "uv",
      "args": ["run", "--directory", "${workspaceFolder}", "a4e_mcp/server.py"],
      "env": {"A4E_WORKSPACE": "${workspaceFolder}"}
    }
  }
}
```

### Claude Desktop

```json
{
  "mcpServers": {
    "a4e": {
      "command": "uv",
      "args": ["run", "/path/to/a4e-mcp-server/a4e_mcp/server.py"],
      "cwd": "/path/to/a4e-mcp-server"
    }
  }
}
```

## Contributing

When modifying this codebase:

1. Keep MCP tools simple and focused
2. Update templates when adding new agent capabilities
3. Maintain backward compatibility with existing agents
4. Add validation for new parameters
5. Update this AGENTS.md when adding new tools

## Related Documentation

| Document | Location | Description |
|----------|----------|-------------|
| **A4E Hub AGENTS.md** | [simetrik-inc/a4e-hub](https://github.com/simetrik-inc/a4e-hub/blob/develop/AGENTS.md) | Agent runtime instructions for the main A4E platform |
| **Claude MCP Guide** | [a4e-hub/docs/guides/claude.md](https://github.com/simetrik-inc/a4e-hub/blob/develop/docs/guides/claude.md) | Detailed tutorial for creating agents with MCP |
| **README** | `README.md` | Quick start and usage instructions |

---

*Compatible with [agents.md](https://agents.md/) standard*
