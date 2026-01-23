---
name: a4e-agent-builder
description: Build and manage A4E (Agents for Everyone) agents using the MCP server. Use when creating agents, adding tools, views, skills, or working with the A4E platform. Provides context on agent structure, mobile-optimized views, database integration, and all MCP capabilities.
license: MIT
compatibility: Designed for Agent Skills compatible AI assistants. Requires access to filesystem and MCP server tools.
metadata:
  author: simetrik-inc
  version: "1.0.0"
  repository: https://github.com/simetrik-inc-public/a4e-mcp-server
---

# A4E Agent Builder

## Overview

A4E (Agents for Everyone) is a comprehensive platform for building, deploying, and managing AI agents with rich interactive capabilities. The platform consists of:

- **A4E Hub**: Full-stack application (FastAPI backend + Next.js frontend) for agent management
- **A4E MCP Server**: Model Context Protocol server enabling natural language agent creation

## Quick Reference

For detailed information, see:

### Setup & Development
- [MCP-INSTALLATION.md](references/MCP-INSTALLATION.md) - Installation and IDE configuration
- [DEPLOYMENT.md](references/DEPLOYMENT.md) - Deploy agents to A4E Hub

### Agent Building
- [AGENT-STRUCTURE.md](references/AGENT-STRUCTURE.md) - Agent directory structure and templates
- [MCP-TOOLS.md](references/MCP-TOOLS.md) - Complete MCP tool reference
- [DATABASE-GUIDE.md](references/DATABASE-GUIDE.md) - Database integration patterns

### Design & Content
- [UI-UX-GUIDE.md](references/UI-UX-GUIDE.md) - Design system and UI components
- [MOBILE-VIEWS.md](references/MOBILE-VIEWS.md) - Mobile-first view development
- [COPYWRITING.md](references/COPYWRITING.md) - Agent prompts and UI microcopy

## Agent Architecture

```
{agent_id}/
├── agent.py                 # Entry point (create_agent function)
├── metadata.json           # Agent identity & capabilities
├── model_config.yaml       # LLM configuration
├── prompts/
│   ├── agent.md           # System prompt (personality/expertise)
│   └── orchestrator.md    # Optional task decomposition
├── views/
│   ├── schemas.json       # Combined view schemas
│   └── {view_name}/
│       ├── view.tsx       # React component
│       └── view.schema.json
├── tools/
│   ├── schemas.json       # Combined tool schemas
│   └── {tool_name}.py     # Tool implementations
└── skills/
    ├── schemas.json       # Skill registry
    └── {skill_id}/SKILL.md
```

## Core Concepts

### 1. Tools
Python functions that agents can call to perform actions:

```python
from a4e.tools import tool

@tool
def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    # Implementation
    return {"city": city, "temp": 72, "condition": "sunny"}
```

### 2. Views
React components that render rich UI responses:

```tsx
interface WeatherViewProps {
  city: string;
  temp: number;
  condition: string;
  isMobile?: boolean;  // Auto-injected by A4E Hub
}

export default function WeatherView({ city, temp, condition, isMobile }: WeatherViewProps) {
  return (
    <div className={`p-4 ${isMobile ? 'text-sm' : 'text-base'}`}>
      <h2>{city}</h2>
      <p>{temp}°F - {condition}</p>
    </div>
  );
}
```

### 3. Skills
High-level action definitions that route user intents:

```markdown
---
name: check-weather
description: Check weather for a location
triggers:
  - "what's the weather"
  - "weather in"
  - "forecast for"
view: weather-view
tools:
  - get_weather
requires_auth: false
---
```

## MCP Tools Summary

| Category | Tools | Purpose |
|----------|-------|---------|
| **Project** | `initialize_project`, `get_agent_info`, `get_instructions` | Setup and info |
| **Tools** | `add_tool`, `list_tools`, `remove_tool`, `update_tool` | Tool management |
| **Views** | `add_view`, `list_views`, `remove_view`, `update_view`, `get_mobile_view_tips` | View creation |
| **Skills** | `add_skill`, `list_skills`, `remove_skill`, `update_skill` | Skill management |
| **Schemas** | `generate_schemas` | Auto-generate schemas |
| **Validation** | `validate` | Validate agent structure |
| **Development** | `dev_start`, `dev_stop`, `check_environment` | Local dev mode |
| **Database** | 20+ tools for SQLite, Supabase, PostgreSQL, MySQL, MongoDB | DB integration |

## Common Workflows

### Creating a New Agent

1. Use `initialize_project` to scaffold the agent
2. Edit `prompts/agent.md` to define personality
3. Add tools with `add_tool`
4. Create views with `add_view` (use `mobile_optimized=True`)
5. Define skills with `add_skill`
6. Run `generate_schemas` to update schema files
7. Use `validate` to check structure
8. Start dev mode with `dev_start`

### Adding a Tool

```
Use add_tool with:
- name: "search_products"
- description: "Search product catalog by query"
- parameters: [{"name": "query", "type": "str", "description": "Search query"}]
- return_type: "list[dict]"
```

### Creating a Mobile-Optimized View

```
Use add_view with:
- name: "product-grid"
- description: "Display products in a responsive grid"
- mobile_optimized: true
- props: [{"name": "products", "type": "array", "description": "List of products"}]
```

## Mobile View Best Practices

1. **Always use the `isMobile` prop** - Auto-injected by A4E Hub
2. **Responsive grid patterns**: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`
3. **Touch-friendly sizing**: Min 44px touch targets
4. **Bottom padding**: `pb-20` to avoid action bar overlap
5. **Text scaling**: `text-base md:text-lg lg:text-xl`

See [MOBILE-VIEWS.md](references/MOBILE-VIEWS.md) for complete guide.

## Agent Capabilities

| Capability | Description | How to Enable |
|-----------|-------------|---------------|
| **Chat** | Conversational interaction | Agent prompt |
| **Tools** | Execute functions | Add tools to `tools/` |
| **Views** | Render rich UI | Add views to `views/` |
| **Handover** | Transfer to other agents | Configure in metadata |
| **Payment** | Stripe integration | Agent configuration |
| **Authentication** | Require user login | Skill `requires_auth` |
| **Task Orchestration** | Multi-step planning | `useOrchestrator=true` |
| **Database** | Connect to DBs | MCP database tools |

## Database Integration

The MCP server provides tools for:

- **SQLite**: Local queries and execution
- **Supabase**: Full CRUD, auth, RPC calls
- **PostgreSQL**: Schema sync and queries
- **MySQL**: Schema sync and queries
- **MongoDB**: Document operations

Use `generate_db_tools()` to auto-generate CRUD tools from your schema.

## Development Mode

```bash
# Start dev mode (creates ngrok tunnel)
dev_start

# Stop dev mode
dev_stop

# Check environment
check_environment
```

Dev mode provides:
- Live reload on file changes
- Public URL via ngrok
- Real-time testing in A4E Hub

## File Locations

- **Agent Store**: `file-store/agent-store/{agent_id}/`
- **Backend**: `friendly-agent-forall/backend/`
- **Frontend**: `friendly-agent-forall/frontend/`
- **MCP Server**: `a4e-mcp-server/`

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, AutoGen, SQLAlchemy |
| Frontend | Next.js 15, React 19, Tailwind CSS |
| MCP Server | Python, Jinja2, Pydantic |
| Storage | MinIO/S3, PostgreSQL |
| Avatar | HeyGen SDK |
| Speech | Deepgram STT |
