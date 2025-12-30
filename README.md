# A4E MCP Server

The **A4E MCP Server** enables creators to build agents using natural language directly in their IDE (Cursor, Claude Desktop).

## Installation

### Prerequisites

1. **Python 3.10+**
2. **uv** (recommended) or `pip`
3. **ngrok Account**: Required for "Dev Mode" to share your local agent with the Hub.
   - Sign up at [ngrok.com](https://ngrok.com)
   - Get your Authtoken from the dashboard.

### Setup

1. Navigate to this directory:
   ```bash
   cd a4e-mcp-server
   ```
2. Install dependencies:
   ```bash
   uv sync
   ```
3. **Configure ngrok** (One-time setup):
   ```bash
   ngrok config add-authtoken <YOUR_TOKEN>
   ```
   _Or pass it later to `dev_start`._

## Usage in Cursor

### Option 1: MCP Settings UI

1. Go to **Cursor Settings** > **Features** > **MCP**.
2. Click **+ Add New MCP Server**.
3. Enter:
   - **Name**: `a4e`
   - **Type**: `command`
   - **Command**: `uv`
   - **Args**: `run --directory /path/to/a4e-mcp-server python -m a4e.server`

### Option 2: mcp.json Configuration (Recommended)

Edit `~/.cursor/mcp.json` (or `.cursor/mcp.json` in your project):

```json
{
  "mcpServers": {
    "a4e": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/a4e-mcp-server",
        "python",
        "-m",
        "a4e.server",
        "--project-dir",
        "/absolute/path/to/a4e-mcp-server"
      ]
    }
  }
}
```

**Example for macOS:**

```json
{
  "mcpServers": {
    "a4e": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/yourname/Documents/a4e-mcp-server",
        "python",
        "-m",
        "a4e.server",
        "--project-dir",
        "/Users/yourname/Documents/a4e-mcp-server"
      ]
    }
  }
}
```

### Configuration Options

| Option | Description |
|--------|-------------|
| `--directory` | Path to the a4e-mcp-server repository |
| `--project-dir` | Where agents will be created (defaults to current directory) |

After adding, restart Cursor to load the MCP server. You should see **21 tools** available.

## Usage in Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "a4e": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/a4e-mcp-server",
        "python",
        "-m",
        "a4e.server"
      ]
    }
  }
}
```

## Concepts

### What is an A4E Agent?

An **A4E Agent** is a specialized AI assistant tailored for a specific domain or task (e.g., a Nutrition Coach or Daily Planner). It combines natural language understanding with custom capabilities defined by **Tools** and **Views**.

### Tools

**Tools** are Python functions that give the agent the ability to perform actions or retrieve information.

- Defined in `tools/*.py` using the `@tool` decorator.
- The agent decides when to call a tool based on the user's request.
- **How it works**: When you ask "Calculate BMI", the agent looks for a tool capable of that calculation, executes the Python code, and returns the result.

### Views

**Views** are React components that provide a rich graphical interface for the agent's responses.

- Defined in `views/*/view.tsx`.
- Used to display structured data (like charts, lists, or forms) instead of just text.
- **How it works**: If a tool returns complex data (like a meal plan), the agent can choose to render a specific view (e.g., `MealPlanView`) to show that data interactively.

## Workflow

1. **Create an Agent**:
   Open a new folder in Cursor (e.g., `my-agents/`).
   Ask Cursor: _"Create a nutrition coach agent"_
   -> This creates the folder `nutrition-coach` with `agent.py`, `metadata.json`, etc.

2. **Add Tools**:
   Ask: _"Add a tool to calculate BMI"_
   -> Creates `tools/calculate_bmi.py`.

3. **Add Views**:
   Ask: _"Add a view to show the BMI result"_
   -> Creates `views/bmi_result/view.tsx`.

4. **Auto-Generate Schemas**:
   The server automatically generates schemas from your Python code and React props when you run `generate_schemas` (or when the file watcher triggers, if enabled).

## Where are agents created?

Agents are created in your **current working directory**.

- If you want to add an agent to the `agent-store`, open that folder in Cursor first.
- If you are testing, just create a temporary folder.

## Integration

- **Local Dev**: `dev_start` - Starts local server and ngrok tunnel.
- **Deployment**: `deploy` (Mocked) - Will upload to S3 and register with the Hub.

## Troubleshooting

### "pyngrok not installed"

If `dev_start` fails, it means the MCP server environment is missing dependencies.

1. Run `check_environment` tool to diagnose.
2. Ensure you ran `uv sync` in the `a4e-mcp-server` directory.
3. Restart your IDE/MCP Client to reload the environment.

### "ngrok command not found"

If you don't want to use `pyngrok`, install the ngrok CLI manually:

- Mac: `brew install ngrok/ngrok/ngrok`
- Windows: `choco install ngrok`
