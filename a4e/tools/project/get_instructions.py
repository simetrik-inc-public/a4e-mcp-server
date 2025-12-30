"""
Get instructions for AI agents on how to use A4E tools.
"""

from ...core import mcp


AGENT_INSTRUCTIONS = '''
# A4E Agent Creator - Instructions for AI Assistants

You have access to the **A4E MCP Server** for creating conversational AI agents.

## Architecture Overview

A4E agents use a **Skills V2** architecture with three layers:

```
USER MESSAGE → SKILL SELECTOR → VIEW RENDERER → VIEW DISPLAY
```

1. **Skill Selector**: Matches user intent to a skill based on `intent_triggers`
2. **View Renderer**: Calls `internal_tools`, processes results, maps to view props
3. **View Display**: Renders React component with the props

## Core Concepts

### Tools (Python Functions)
Backend logic - calculations, API calls, data retrieval.

### Views (React Components)
Frontend display - what users see. Each view has:
- `view.tsx` - React component
- `view.schema.json` - Props schema

### Skills (Intent → View Mapping)
Connect user intents to views:
- `intent_triggers` - phrases that activate the skill
- `internal_tools` - tools to call
- `output_view` - view to render

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `initialize_project(name, display_name, description, category, template)` | Create new agent |
| `add_tool(agent_name, tool_name, description, parameters)` | Add Python tool |
| `add_view(agent_name, view_id, description, props)` | Add React view |
| `add_skill(agent_name, skill_id, name, description, intent_triggers, output_view, internal_tools, requires_auth)` | Add skill |
| `update_tool/view/skill(...)` | Update existing components |
| `remove_tool/view/skill(...)` | Remove components |
| `list_tools/views/skills(agent_name)` | List components |
| `validate(agent_name)` | Validate configuration |
| `generate_schemas(agent_name, force)` | Regenerate schemas |
| `dev_start(agent_name, port)` | Start dev server |

## Workflow

### Step 1: Initialize Project
```python
initialize_project(
    name="my-agent",           # lowercase-hyphens
    display_name="My Agent",
    description="What the agent does",
    category="category",
    template="basic"           # basic | with-tools | with-views | full
)
```

### Step 2: Add Tools
```python
add_tool(
    agent_name="my-agent",
    tool_name="calculate_something",    # snake_case
    description="What it does",
    parameters={
        "param1": {"type": "string", "description": "...", "required": True},
        "param2": {"type": "number", "description": "..."}
    }
)
```

**Parameter types:** `string`, `number`, `integer`, `boolean`, `array`, `object`

### Step 3: Add Views
```python
add_view(
    agent_name="my-agent",
    view_id="result_view",              # snake_case
    description="What it displays",
    props={
        "title": {"type": "string", "description": "..."},
        "items": {"type": "array", "description": "..."}
    }
)
```

### Step 4: Add Skills (AFTER creating views)
```python
add_skill(
    agent_name="my-agent",
    skill_id="show_result",             # snake_case
    name="Show Result",                 # Display name
    description="When to use this skill",
    intent_triggers=[
        "show result",
        "display data",
        "mostrar resultado"             # Multiple languages supported
    ],
    output_view="result_view",          # Must match existing view_id
    internal_tools=["calculate_something"],
    requires_auth=False
)
```

### Step 5: Validate
```python
validate(agent_name="my-agent")
```

## Important Rules

1. **Create views BEFORE skills** - Skills reference views by ID
2. **Use snake_case** for tool_name, view_id, skill_id
3. **Use lowercase-hyphens** for agent name
4. **Write diverse intent_triggers** - variations, synonyms, multiple languages
5. **Check errors** - All tools return `{"success": bool, "error": str, "fix": str}`

## Data Flow Example

User: "Calculate my BMI"

1. Skill Selector → matches "show_bmi_result" skill
2. View Renderer:
   - Calls `calculate_bmi(weight=70, height=1.75)`
   - Gets `{"bmi": 22.9, "category": "normal"}`
   - Maps to view props
3. View Display → renders BMI result component

## Project Structure

```
{agent}/
├── agent.py
├── metadata.json
├── tools/
│   ├── {tool_name}.py
│   └── schemas.json
├── views/
│   ├── {view_id}/
│   │   ├── view.tsx
│   │   └── view.schema.json
│   └── schemas.json
├── skills/
│   ├── {skill_id}/
│   │   └── SKILL.md
│   └── schemas.json
└── prompts/
    └── agent.md
```

## Quick Example

```python
# 1. Initialize
initialize_project(name="calculator", display_name="Calculator", description="Math calculator", category="utilities", template="basic")

# 2. Add tool
add_tool(agent_name="calculator", tool_name="add_numbers", description="Add two numbers", parameters={"a": "number", "b": "number"})

# 3. Add view
add_view(agent_name="calculator", view_id="sum_result", description="Show sum", props={"result": "number", "expression": "string"})

# 4. Add skill
add_skill(agent_name="calculator", skill_id="show_sum", name="Show Sum", description="Display addition result", intent_triggers=["add", "sum", "plus"], output_view="sum_result", internal_tools=["add_numbers"])

# 5. Validate
validate(agent_name="calculator")
```
'''


@mcp.tool()
def get_instructions() -> dict:
    """
    Get instructions for AI agents on how to use A4E MCP tools.

    Call this tool first to understand how to create A4E agents.
    Returns comprehensive documentation on architecture, tools, and workflows.
    """
    return {
        "success": True,
        "instructions": AGENT_INSTRUCTIONS,
        "summary": "A4E Agent Creator instructions loaded. Use initialize_project() to start, then add tools, views, and skills.",
        "quick_reference": {
            "workflow": ["initialize_project", "add_tool", "add_view", "add_skill", "validate"],
            "naming": {
                "agent_name": "lowercase-hyphens",
                "tool_name": "snake_case",
                "view_id": "snake_case",
                "skill_id": "snake_case"
            },
            "parameter_types": ["string", "number", "integer", "boolean", "array", "object"],
            "templates": ["basic", "with-tools", "with-views", "full"]
        }
    }
