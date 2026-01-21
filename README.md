# A4E

[![PyPI version](https://badge.fury.io/py/a4e.svg)](https://badge.fury.io/py/a4e)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A4E** is a CLI toolkit for building conversational AI agents. It includes:

- **CLI commands** for creating and managing agents (`a4e init`, `a4e add tool`, etc.)
- **MCP server** for IDE integration (Cursor, Claude Code, Antigravity)
- **Dev server** with hot-reload and ngrok tunneling

## Requirements

### Python 3.10+

```bash
# Check your version
python --version

# Install Python 3.10+ if needed
# macOS (with Homebrew)
brew install python@3.10

# Ubuntu/Debian
sudo apt update && sudo apt install python3.10

# Windows (download from python.org)
# https://www.python.org/downloads/
```

> **Note:** If you try to install with an older Python version, pip will show:
> `ERROR: Package 'a4e' requires a different Python: X.Y.Z not in '>=3.10'`

### ngrok (for dev server)

The development server uses ngrok to create public tunnels for testing.

1. **Create account:** https://ngrok.com/signup
2. **Get your authtoken:** https://dashboard.ngrok.com/get-started/your-authtoken
3. **Configure ngrok:**

```bash
# Option A: Install ngrok CLI and configure
brew install ngrok/ngrok/ngrok   # macOS
# or download from https://ngrok.com/download

ngrok config add-authtoken YOUR_TOKEN_HERE

# Option B: Set environment variable
export NGROK_AUTHTOKEN=YOUR_TOKEN_HERE
```

## Installation

```bash
pip install a4e
```

Verify installation:

```bash
a4e --version
```

## Quick Start

### Option 1: Use with AI Assistant (MCP)

Configure A4E for your IDE:

```bash
# For Cursor
a4e mcp setup cursor

# For Claude Code
a4e mcp setup claude-code

# For Antigravity
a4e mcp setup antigravity
```

**Restart your IDE**, then ask your AI assistant:

> "Create an agent called nutrition-coach that helps users track meals and calculate calories"

### Option 2: Use CLI directly

```bash
# Create a new agent
a4e init

# Add components
a4e add tool calculate_bmi
a4e add view bmi_result
a4e add skill show_bmi

# Validate
a4e validate

# Start dev server
a4e dev start

# Deploy
a4e deploy
```

## CLI Commands

| Command            | Arguments                               | Description                               |
| ------------------ | --------------------------------------- | ----------------------------------------- |
| `a4e init`         | `--name`, `--template`                  | Initialize new agent (interactive wizard) |
| `a4e add tool`     | `<name>` `string`                       | Add a Python tool                         |
| `a4e add view`     | `<name>` `string`                       | Add a React view                          |
| `a4e add skill`    | `<name>` `string`                       | Add a skill (connects tools → views)      |
| `a4e list`         | `tools` \| `views` \| `skills` \| `all` | List components                           |
| `a4e remove tool`  | `<name>` `string`                       | Remove a tool                             |
| `a4e remove view`  | `<name>` `string`                       | Remove a view                             |
| `a4e remove skill` | `<name>` `string`                       | Remove a skill                            |
| `a4e update tool`  | `<name>` `string`                       | Update a tool                             |
| `a4e update view`  | `<name>` `string`                       | Update a view                             |
| `a4e update skill` | `<name>` `string`                       | Update a skill                            |
| `a4e validate`     | `--strict`, `--agent`                   | Validate agent structure                  |
| `a4e deploy`       | `--skip-validation`                     | Deploy to A4E Cloud                       |
| `a4e dev start`    | `--port` `int`, `--auth-token` `string` | Start dev server with ngrok               |
| `a4e info`         | `--json`                                | Show agent information                    |

### Init Options

| Option                 | Type     | Values                                                                                                                                | Description                   |
| ---------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| `--name`, `-n`         | `string` | `my-agent`                                                                                                                            | Agent ID (lowercase, hyphens) |
| `--display-name`, `-d` | `string` | `"My Agent"`                                                                                                                          | Human-readable name           |
| `--description`        | `string` | `"Agent description"`                                                                                                                 | Short description             |
| `--category`, `-c`     | `enum`   | `Concierge`, `E-commerce`, `Fitness & Health`, `Education`, `Entertainment`, `Productivity`, `Finance`, `Customer Support`, `General` | Agent category                |
| `--template`, `-t`     | `enum`   | `basic`, `with-tools`, `with-views`, `full`                                                                                           | Project template              |
| `--yes`, `-y`          | `flag`   | —                                                                                                                                     | Skip interactive prompts      |

### MCP Commands

| Command          | Arguments | Values                                  | Description            |
| ---------------- | --------- | --------------------------------------- | ---------------------- |
| `a4e mcp setup`  | `<ide>`   | `cursor`, `claude-code`, `antigravity`  | Configure MCP for IDE  |
| `a4e mcp show`   | `<ide>`   | `cursor`, `claude-code`, `antigravity`  | Show current config    |
| `a4e mcp remove` | `<ide>`   | `cursor`, `claude-code`, `antigravity`  | Remove A4E from config |
| `a4e mcp test`   | —         | —                                       | Test MCP server        |
| `a4e mcp path`   | `<ide>`   | `cursor`, `claude-code`, `antigravity`  | Show config file path  |
| `a4e mcp list`   | —         | —                                       | List supported IDEs    |

### MCP Setup Options

| Option            | Type   | Description                      |
| ----------------- | ------ | -------------------------------- |
| `--dry-run`, `-n` | `flag` | Preview changes without applying |
| `--force`, `-f`   | `flag` | Overwrite existing A4E config    |

## Agent Structure

When you create an agent, A4E generates:

```
my-agent/
├── agent.py           # Agent configuration
├── metadata.json      # Agent metadata
├── AGENTS.md          # Documentation for AI assistants
├── prompts/
│   └── agent.md       # System prompt / personality
├── tools/
│   ├── my_tool.py     # Python functions
│   └── schemas.json   # Auto-generated schemas
├── views/
│   ├── my_view/
│   │   └── view.tsx   # React components
│   └── schemas.json   # Auto-generated schemas
└── skills/
    ├── my_skill/
    │   └── SKILL.md   # Skill documentation
    └── schemas.json   # Auto-generated schemas
```

## Concepts

### Tools

Python functions that give your agent capabilities:

```python
from typing import Dict, Any

def calculate_bmi(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate BMI from height and weight."""
    height = params.get("height_m")
    weight = params.get("weight_kg")
    bmi = weight / (height ** 2)
    return {"bmi": round(bmi, 1), "status": "success"}
```

### Views

React components for rich UI responses:

```tsx
interface BMIResultProps {
  bmi: number;
  category: string;
}

export default function BMIResult({ bmi, category }: BMIResultProps) {
  return (
    <div className="p-4">
      <h2>Your BMI: {bmi}</h2>
      <p>Category: {category}</p>
    </div>
  );
}
```

### Skills

Connect user intents to tools and views:

```json
{
  "id": "show_bmi",
  "name": "Calculate BMI",
  "intent_triggers": ["calculate my bmi", "what's my bmi"],
  "internal_tools": ["calculate_bmi"],
  "output": {
    "view": "bmi_result"
  }
}
```

## MCP Configuration

### Automatic Setup (Recommended)

```bash
a4e mcp setup cursor
```

This:

1. Creates a backup of your existing config
2. Adds A4E to your MCP servers
3. Uses the correct Python path automatically

### Manual Setup

<details>
<summary>Cursor (~/.cursor/mcp.json)</summary>

```json
{
  "mcpServers": {
    "a4e": {
      "command": "/path/to/python",
      "args": ["-m", "a4e.server"],
      "env": {
        "A4E_WORKSPACE": "${workspaceFolder}"
      }
    }
  }
}
```

Find your Python path with: `which python` or `a4e mcp test`

</details>

<details>
<summary>Claude Code (~/.claude.json)</summary>

```json
{
  "mcpServers": {
    "a4e": {
      "command": "/path/to/python",
      "args": ["-m", "a4e.server"]
    }
  }
}
```

</details>

<details>
<summary>Antigravity (~/.gemini/antigravity/mcp_config.json)</summary>

```json
{
  "mcpServers": {
    "a4e": {
      "command": "/path/to/python",
      "args": ["-m", "a4e.server"]
    }
  }
}
```

</details>

## Troubleshooting

### "a4e: command not found"

Ensure pip scripts are in your PATH:

```bash
# Find where pip installs scripts
python -m site --user-base

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Or install with pipx for automatic PATH management
pipx install a4e
```

### MCP not connecting in IDE

```bash
# 1. Test the MCP server
a4e mcp test

# 2. Check your config
a4e mcp show cursor

# 3. Verify Python path is correct
which python

# 4. Restart your IDE after config changes
```

### ngrok errors in dev server

```bash
# Check if ngrok is configured
ngrok config check

# Add your authtoken
ngrok config add-authtoken YOUR_TOKEN

# Or pass it directly
a4e dev start --auth-token YOUR_TOKEN
```

### Port 5000 already in use

```bash
# Find what's using the port
lsof -i :5000

# Kill it
kill -9 <PID>

# Or use a different port
a4e dev start --port 5001
```

### MCP config backup

When running `a4e mcp setup`, a backup is automatically created at:

- Cursor: `~/.cursor/mcp.json.backup`
- Claude Code: `~/.claude.json.backup`
- Antigravity: `~/.gemini/antigravity/mcp_config.json.backup`

To restore:

```bash
cp ~/.cursor/mcp.json.backup ~/.cursor/mcp.json
```

## Documentation

- [CLI Reference](CLI.md) - Full command documentation
- [Getting Started](docs/GETTING_STARTED.md) - Step-by-step tutorial
- [Examples](docs/EXAMPLES.md) - Sample agents
- [View System](docs/VIEW_SYSTEM.md) - How views work

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [PyPI](https://pypi.org/project/a4e/)
- [GitHub](https://github.com/simetrik-inc-public/a4e-mcp-server)
- [Issues](https://github.com/simetrik-inc-public/a4e-mcp-server/issues)
