# A4E MCP Server Installation Guide

Complete setup guide for the A4E MCP Server in different environments.

## Prerequisites

- **Python 3.11+** (required)
- **uv** package manager (recommended) or pip
- **ngrok** account (for dev mode tunneling)

## Quick Start

```bash
# 1. Navigate to MCP server directory
cd a4e-mcp-server

# 2. Install dependencies
uv sync

# 3. Configure ngrok (one-time)
ngrok config add-authtoken <YOUR_TOKEN>

# 4. Verify installation
uv run python -m a4e.server --help
```

---

## IDE Configuration

### Cursor IDE

**Option 1: MCP Settings UI**

1. Open **Cursor Settings** → **Features** → **MCP**
2. Click **+ Add New MCP Server**
3. Enter:
   - **Name:** `a4e`
   - **Type:** `command`
   - **Command:** `uv`
   - **Args:** `run --directory /path/to/a4e-mcp-server python -m a4e.server`

**Option 2: Configuration File (Recommended)**

Create/edit `~/.cursor/mcp.json`:

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

**Project-level configuration:**

Create `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "a4e": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "${workspaceFolder}/../a4e-mcp-server",
        "python",
        "-m",
        "a4e.server"
      ]
    }
  }
}
```

### Claude Desktop

Create/edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

### VS Code (with MCP extension)

Add to your VS Code settings or workspace config:

```json
{
  "mcp.servers": {
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

---

## Environment Variables

Create `.env` in the `a4e-mcp-server` directory:

```bash
# ngrok (optional - can use ngrok config instead)
NGROK_AUTHTOKEN=your_ngrok_token

# Default workspace for agent projects
A4E_WORKSPACE=/path/to/your/agents

# Database credentials (optional)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### Environment Variable Priority

For ngrok authentication:
1. Environment variable: `NGROK_AUTHTOKEN`
2. ngrok config file (platform-specific):
   - **macOS:** `~/Library/Application Support/ngrok/ngrok.yml`
   - **Linux:** `~/.ngrok2/ngrok.yml`
   - **Windows:** `~/AppData/Local/ngrok/ngrok.yml`

---

## ngrok Setup

ngrok is required for dev mode to create public tunnels for testing.

### 1. Create Account

1. Go to [ngrok.com](https://ngrok.com)
2. Sign up for a free account
3. Copy your authtoken from the dashboard

### 2. Configure ngrok

```bash
# Add your authtoken (one-time setup)
ngrok config add-authtoken <YOUR_TOKEN>
```

### 3. Verify Installation

```bash
# Test ngrok is working
ngrok version

# Or use the MCP tool
# In your IDE, call: check_environment
```

---

## Dependencies

The MCP server requires these packages (automatically installed via `uv sync`):

```toml
# Core
mcp[cli]>=1.22.0          # Model Context Protocol SDK
pydantic>=2.12.4          # Data validation
typer>=0.20.0             # CLI framework

# Development
pyngrok>=7.5.0            # ngrok Python wrapper
watchdog>=6.0.0           # File system monitoring
sse-starlette>=3.0.3      # Server-Sent Events

# Utilities
jinja2>=3.1.6             # Template engine
pyyaml>=6.0.3             # YAML parsing
pyperclip>=1.11.0         # Clipboard operations
```

---

## CLI Commands

After installation, you can use the CLI directly:

```bash
# Initialize new agent
uv run a4e init

# Add components
uv run a4e add tool <name>
uv run a4e add view <name>
uv run a4e add skill <name>

# List components
uv run a4e list tools
uv run a4e list views
uv run a4e list skills

# Validate agent
uv run a4e validate

# Start dev server
uv run a4e dev start

# Stop dev server
uv run a4e dev stop

# Deploy
uv run a4e deploy

# Get agent info
uv run a4e info
```

---

## Dev Mode Workflow

### Start Development Server

```bash
# Default port (5000)
uv run a4e dev start

# Custom port
uv run a4e dev start --port 8000
```

**What happens:**
1. Starts local FastMCP server
2. Creates ngrok tunnel
3. Copies playground URL to clipboard
4. Watches for file changes

### Access Playground

After starting dev mode, access your agent at:
```
https://dev-a4e.global.simetrik.com/builder/playground?url=<ngrok_url>&agent=<agent_id>
```

### Stop Development Server

```bash
uv run a4e dev stop --port 5000
```

---

## Project Structure

```
a4e-mcp-server/
├── README.md                 # Main documentation
├── CLI.md                    # CLI reference
├── AGENTS.md                 # Agent architecture guide
├── pyproject.toml            # Dependencies
├── .env                      # Environment variables
├── .python-version           # Python 3.11
│
├── a4e/                      # Main package
│   ├── server.py             # MCP server entry
│   ├── cli.py                # CLI entry
│   ├── core.py               # Shared utilities
│   ├── dev_runner.py         # Dev server
│   │
│   ├── cli_commands/         # CLI implementations
│   ├── tools/                # MCP tools
│   ├── templates/            # Code generation templates
│   └── utils/                # Utilities
│
├── docs/                     # Additional documentation
│   ├── GETTING_STARTED.md
│   ├── VIEW_SYSTEM.md
│   └── DATABASE_GUIDE.md
│
└── file-store/               # Agent storage
    └── agent-store/
```

---

## Troubleshooting

### "pyngrok not installed"

```bash
cd a4e-mcp-server
uv sync
# Restart your IDE
```

### "ngrok command not found"

```bash
# macOS
brew install ngrok/ngrok/ngrok

# Or use pyngrok (installed with uv sync)
```

### "Port already in use"

```bash
# Find process
lsof -i :5000

# Kill it
kill -9 <PID>

# Or use a different port
uv run a4e dev start --port 8000
```

### "MCP server not connecting"

1. Check the server is running: `ps aux | grep a4e`
2. Verify paths in your config are absolute
3. Restart your IDE after config changes
4. Check IDE logs for MCP errors

### Environment Check

Use the MCP tool to diagnose issues:

```
# In your IDE, call the check_environment tool
# It will report:
# - pyngrok installation status
# - ngrok binary availability
# - ngrok auth configuration
# - Recommendations for any issues
```

---

## Updating

```bash
cd a4e-mcp-server

# Pull latest changes
git pull

# Update dependencies
uv sync

# Restart your IDE to reload MCP server
```

---

## Multiple Workspaces

To use different agent directories:

```json
{
  "mcpServers": {
    "a4e-project1": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/a4e-mcp-server",
        "python", "-m", "a4e.server",
        "--project-dir", "/path/to/project1/agents"
      ]
    },
    "a4e-project2": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/a4e-mcp-server",
        "python", "-m", "a4e.server",
        "--project-dir", "/path/to/project2/agents"
      ]
    }
  }
}
```
