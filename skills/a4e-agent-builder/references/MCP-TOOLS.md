# A4E MCP Tools Reference

Complete reference for all tools available in the A4E MCP Server.

## Project Management

### initialize_project

Initialize a new agent project with the standard directory structure.

**Parameters:**
- `agent_id` (required): Unique identifier for the agent
- `name` (required): Display name for the agent
- `description` (required): What the agent does
- `personality` (optional): Agent personality traits

**Example:**
```
initialize_project(
  agent_id="weather-bot",
  name="Weather Assistant",
  description="Provides weather forecasts and alerts",
  personality="Friendly and informative meteorologist"
)
```

### get_agent_info

Get current agent configuration and metadata.

**Returns:** Agent metadata, tools, views, and skills

### get_instructions

Get detailed instructions for building agents with A4E.

**Returns:** Comprehensive guide for agent development

---

## Tool Management

### add_tool

Add a new tool to the agent.

**Parameters:**
- `name` (required): Tool function name (snake_case)
- `description` (required): What the tool does
- `parameters` (required): List of parameter definitions
  - `name`: Parameter name
  - `type`: Python type (str, int, float, bool, list, dict)
  - `description`: Parameter description
  - `required`: Whether parameter is required (default: true)
- `return_type` (required): Return type annotation

**Example:**
```
add_tool(
  name="search_products",
  description="Search product catalog by query",
  parameters=[
    {"name": "query", "type": "str", "description": "Search query", "required": true},
    {"name": "limit", "type": "int", "description": "Max results", "required": false}
  ],
  return_type="list[dict]"
)
```

### list_tools

List all tools in the current agent.

**Returns:** List of tool names with descriptions

### update_tool

Update an existing tool's code or configuration.

**Parameters:**
- `name` (required): Tool name to update
- `code` (optional): New Python code
- `description` (optional): New description

### remove_tool

Remove a tool from the agent.

**Parameters:**
- `name` (required): Tool name to remove

---

## View Management

### add_view

Add a new view component to the agent.

**Parameters:**
- `name` (required): View name (kebab-case)
- `description` (required): What the view displays
- `props` (required): List of prop definitions
  - `name`: Prop name
  - `type`: TypeScript type (string, number, boolean, array, object)
  - `description`: Prop description
  - `required`: Whether prop is required
- `mobile_optimized` (optional): Generate mobile-first template (default: false)

**Example:**
```
add_view(
  name="product-card",
  description="Display a single product with image and details",
  props=[
    {"name": "title", "type": "string", "description": "Product title"},
    {"name": "price", "type": "number", "description": "Product price"},
    {"name": "imageUrl", "type": "string", "description": "Product image URL"},
    {"name": "inStock", "type": "boolean", "description": "Availability status"}
  ],
  mobile_optimized=true
)
```

### list_views

List all views in the current agent.

**Returns:** List of view names with descriptions

### update_view

Update an existing view's code or schema.

**Parameters:**
- `name` (required): View name to update
- `code` (optional): New TSX code
- `schema` (optional): New schema definition

### remove_view

Remove a view from the agent.

**Parameters:**
- `name` (required): View name to remove

### get_mobile_view_tips

Get best practices for mobile-optimized view development.

**Returns:** Comprehensive mobile development guidelines

---

## Skill Management

### add_skill

Add a new skill to the agent.

**Parameters:**
- `skill_id` (required): Unique skill identifier (kebab-case)
- `name` (required): Display name
- `description` (required): What the skill does
- `triggers` (required): List of phrases that activate this skill
- `view` (optional): View to render on completion
- `tools` (optional): Tools this skill uses
- `requires_auth` (optional): Whether authentication is required

**Example:**
```
add_skill(
  skill_id="check-order-status",
  name="Order Status",
  description="Check the status of a customer order",
  triggers=["where is my order", "track order", "order status"],
  view="order-status-view",
  tools=["get_order", "track_shipment"],
  requires_auth=true
)
```

### list_skills

List all skills in the current agent.

**Returns:** List of skills with triggers and configuration

### update_skill

Update an existing skill's configuration.

**Parameters:**
- `skill_id` (required): Skill to update
- `triggers` (optional): New trigger phrases
- `view` (optional): New view assignment
- `tools` (optional): New tool list

### remove_skill

Remove a skill from the agent.

**Parameters:**
- `skill_id` (required): Skill to remove

---

## Schema Generation

### generate_schemas

Generate TypeScript and Python schemas for all tools and views.

**What it does:**
- Creates `tools/schemas.json` from tool definitions
- Creates `views/schemas.json` from view schemas
- Creates `skills/schemas.json` from skill definitions
- Validates all schemas for consistency

**When to use:** After adding or modifying tools, views, or skills.

---

## Validation

### validate

Validate the agent's structure and configuration.

**Checks:**
- Required files exist (agent.py, metadata.json, etc.)
- Tools have valid schemas
- Views have valid React code
- Skills reference valid tools and views
- No circular dependencies

**Returns:** List of errors and warnings

---

## Development Mode

### dev_start

Start development mode with live reload and ngrok tunnel.

**Parameters:**
- `port` (optional): Local port to use (default: 8000)

**What it does:**
- Starts local development server
- Creates ngrok tunnel for external access
- Watches files for changes
- Auto-reloads on changes

**Returns:** Public ngrok URL for testing

### dev_stop

Stop development mode and close ngrok tunnel.

### check_environment

Check if the development environment is properly configured.

**Checks:**
- Python version
- Required packages installed
- ngrok authentication
- Environment variables

---

## Database Tools

### SQLite Tools

#### sqlite_query
Execute a read-only SQL query on a SQLite database.

**Parameters:**
- `database_path` (required): Path to SQLite file
- `query` (required): SQL query to execute

#### sqlite_execute
Execute a write SQL statement (INSERT, UPDATE, DELETE).

**Parameters:**
- `database_path` (required): Path to SQLite file
- `statement` (required): SQL statement to execute

#### sqlite_schema
Get the schema of a SQLite database.

**Parameters:**
- `database_path` (required): Path to SQLite file

### Supabase Tools

#### supabase_query
Query data from a Supabase table.

**Parameters:**
- `table` (required): Table name
- `select` (optional): Columns to select (default: *)
- `filters` (optional): Filter conditions
- `limit` (optional): Max rows to return

#### supabase_insert
Insert data into a Supabase table.

**Parameters:**
- `table` (required): Table name
- `data` (required): Data to insert (object or array)

#### supabase_update
Update data in a Supabase table.

**Parameters:**
- `table` (required): Table name
- `data` (required): Data to update
- `filters` (required): Filter conditions

#### supabase_delete
Delete data from a Supabase table.

**Parameters:**
- `table` (required): Table name
- `filters` (required): Filter conditions

#### supabase_rpc
Call a Supabase remote procedure.

**Parameters:**
- `function_name` (required): RPC function name
- `params` (optional): Function parameters

#### supabase_schema
Get Supabase database schema.

### PostgreSQL Tools

#### postgres_query
Execute a query on PostgreSQL.

#### postgres_schema
Get PostgreSQL schema.

#### postgres_sync
Sync schema from PostgreSQL to agent tools.

### MySQL Tools

#### mysql_query
Execute a query on MySQL.

#### mysql_schema
Get MySQL schema.

#### mysql_sync
Sync schema from MySQL to agent tools.

### MongoDB Tools

#### mongodb_find
Find documents in a MongoDB collection.

#### mongodb_insert
Insert documents into MongoDB.

#### mongodb_update
Update documents in MongoDB.

#### mongodb_delete
Delete documents from MongoDB.

#### mongodb_aggregate
Run aggregation pipeline on MongoDB.

### Database Tool Generation

#### generate_db_tools

Auto-generate CRUD tools from a database schema.

**Parameters:**
- `database_type` (required): sqlite, supabase, postgres, mysql, mongodb
- `connection_string` (required): Database connection details
- `tables` (optional): Specific tables to generate tools for

**Example:**
```
generate_db_tools(
  database_type="supabase",
  connection_string="your-project-url",
  tables=["users", "orders", "products"]
)
```

**Generates:**
- `get_{table}` - Read single record
- `list_{table}` - List records with filters
- `create_{table}` - Create new record
- `update_{table}` - Update existing record
- `delete_{table}` - Delete record

---

## Deployment

### deploy

Deploy the agent to production (requires A4E Hub connection).

**Parameters:**
- `environment` (optional): Target environment (staging, production)

**Note:** This tool is currently mocked in the MCP server.

---

## Tool Categories Summary

| Category | Count | Purpose |
|----------|-------|---------|
| Project | 3 | Setup and information |
| Tools | 4 | Tool management |
| Views | 5 | View management |
| Skills | 4 | Skill management |
| Schemas | 1 | Schema generation |
| Validation | 1 | Structure validation |
| Development | 3 | Local dev mode |
| SQLite | 3 | SQLite operations |
| Supabase | 6 | Supabase operations |
| PostgreSQL | 3 | PostgreSQL operations |
| MySQL | 3 | MySQL operations |
| MongoDB | 5 | MongoDB operations |
| DB Generation | 1 | Auto-generate CRUD tools |
| Deployment | 1 | Production deployment |

**Total: 40+ tools**
